"""
MQTT Client Manager for IoT Fault Diagnosis Assistant.
Handles telemetry ingestion, automated anomaly detection, SQLite storage, and WebSocket dispatch.
"""
import json
import sqlite3
import threading
import time
from typing import Dict, List, Optional, Callable
import paho.mqtt.client as mqtt

from app.config import settings, DB_PATH
from app.models.telemetry import TelemetryData


class MQTTManager:
    def __init__(self):
        self.broker_host = settings.MQTT_BROKER_HOST
        self.broker_port = settings.MQTT_BROKER_PORT
        self.client_id = settings.MQTT_CLIENT_ID
        self.client: Optional[mqtt.Client] = None
        self.is_connected = False
        
        # In-memory fast cache of latest device state
        self.latest_devices: Dict[str, TelemetryData] = {}
        self.active_alerts: List[Dict] = []
        
        # Callbacks for WebSocket broadcasting
        self.ws_broadcast_callback: Optional[Callable] = None
        self._lock = threading.Lock()

    def set_ws_callback(self, callback: Callable):
        self.ws_broadcast_callback = callback

    def start(self):
        """Start MQTT client in background loop with reconnect."""
        try:
            # Paho MQTT 2.x supports CallbackAPIVersion
            try:
                self.client = mqtt.Client(
                    mqtt.CallbackAPIVersion.VERSION2,
                    client_id=self.client_id
                )
            except (AttributeError, TypeError):
                self.client = mqtt.Client(client_id=self.client_id)

            if settings.MQTT_USERNAME and settings.MQTT_PASSWORD:
                self.client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)

            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message

            print(f"[MQTT] Connecting to broker {self.broker_host}:{self.broker_port} ...")
            self.client.connect_async(self.broker_host, self.broker_port, keepalive=settings.MQTT_KEEPALIVE)
            self.client.loop_start()
        except Exception as e:
            print(f"[MQTT] Failed to start MQTT client: {e}")

    def stop(self):
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.is_connected = False

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        rc_code = rc if isinstance(rc, int) else getattr(rc, "value", rc)
        if rc_code == 0:
            self.is_connected = True
            print(f"[MQTT] Connected successfully to {self.broker_host}:{self.broker_port}")
            # Subscribe to telemetry & alerts
            self.client.subscribe([(settings.TOPIC_TELEMETRY, 0), (settings.TOPIC_ALERTS, 0)])
            print(f"[MQTT] Subscribed to {settings.TOPIC_TELEMETRY} and {settings.TOPIC_ALERTS}")
        else:
            print(f"[MQTT] Connection failed with code {rc_code}")

    def _on_disconnect(self, client, userdata, rc, properties=None):
        self.is_connected = False
        print(f"[MQTT] Disconnected from broker (rc={rc}). Will attempt auto-reconnect.")

    def _on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            payload_str = msg.payload.decode("utf-8")
            data = json.loads(payload_str)

            if "/telemetry" in topic:
                self._handle_telemetry(data)
            elif "/alerts" in topic:
                self._handle_alert(data)
        except Exception as e:
            print(f"[MQTT] Error processing message on {msg.topic}: {e}")

    def _handle_telemetry(self, data: dict):
        # Validate data with TelemetryData
        try:
            telemetry = TelemetryData(**data)
            
            # Auto ISO 10816-3 Zone calculation
            if telemetry.vibration_rms < 1.4:
                iso_zone = "Zone A"
            elif telemetry.vibration_rms < 2.8:
                iso_zone = "Zone B"
            elif telemetry.vibration_rms < 4.5:
                iso_zone = "Zone C"
            else:
                iso_zone = "Zone D"
            telemetry.iso_zone = iso_zone

            # Anomaly trigger
            is_anomaly = iso_zone in ("Zone C", "Zone D") or telemetry.temperature > 80 or telemetry.fault_code != "NORMAL"
            telemetry.is_anomaly = is_anomaly

            # Health index estimate
            deductions = 0.0
            if telemetry.vibration_rms > 1.4:
                deductions += min(45.0, (telemetry.vibration_rms - 1.4) * 8.0)
            if telemetry.vibration_peak > 1.0:
                deductions += min(30.0, (telemetry.vibration_peak - 1.0) * 12.0)
            if telemetry.temperature > 65.0:
                deductions += min(25.0, (telemetry.temperature - 65.0) * 1.5)
            telemetry.health_index = max(5.0, round(100.0 - deductions, 1))

            with self._lock:
                self.latest_devices[telemetry.device_id] = telemetry

            # Store to SQLite database
            self._save_telemetry_to_db(telemetry)

            # Auto alert if critical
            if is_anomaly and iso_zone in ("Zone C", "Zone D"):
                alert_payload = {
                    "device_id": telemetry.device_id,
                    "severity": "CRITICAL" if iso_zone == "Zone D" or telemetry.temperature > 90 else "WARNING",
                    "fault_code": telemetry.fault_code,
                    "message": f"ISO {iso_zone} violation: Vibration {telemetry.vibration_rms} mm/s, Temp {telemetry.temperature}°C",
                    "timestamp": telemetry.timestamp
                }
                self.publish_alert(alert_payload)

            # Forward to WebSocket clients
            if self.ws_broadcast_callback:
                self.ws_broadcast_callback({
                    "type": "telemetry",
                    "data": telemetry.model_dump()
                })

        except Exception as e:
            print(f"[MQTT] Validation error: {e}")

    def _handle_alert(self, alert_data: dict):
        with self._lock:
            self.active_alerts.insert(0, alert_data)
            if len(self.active_alerts) > 50:
                self.active_alerts.pop()

        if self.ws_broadcast_callback:
            self.ws_broadcast_callback({
                "type": "alert",
                "data": alert_data
            })

    def _save_telemetry_to_db(self, t: TelemetryData):
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO telemetry_logs 
                    (device_id, device_type, timestamp, vibration_rms, vibration_peak, temperature, current_draw, pressure, flow_rate, fault_code, health_index, iso_zone, is_anomaly)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    t.device_id, t.device_type, t.timestamp, t.vibration_rms, t.vibration_peak,
                    t.temperature, t.current_draw, t.pressure, t.flow_rate, t.fault_code,
                    t.health_index, t.iso_zone, 1 if t.is_anomaly else 0
                ))
                conn.commit()
        except Exception as e:
            print(f"[DB] Error saving telemetry: {e}")

    def publish_telemetry(self, device_id: str, payload: dict):
        if self.client and self.is_connected:
            topic = f"{settings.TOPIC_TELEMETRY_PUB_PREFIX}/{device_id}"
            self.client.publish(topic, json.dumps(payload), qos=0)

    def publish_alert(self, alert: dict):
        if self.client and self.is_connected:
            topic = f"{settings.TOPIC_ALERTS_PUB_PREFIX}/{alert['device_id']}"
            self.client.publish(topic, json.dumps(alert), qos=1)


# Global singleton instance
mqtt_manager = MQTTManager()
