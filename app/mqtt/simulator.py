"""
Industrial IoT Multi-Device Telemetry Simulator for Project P_311.
Simulates real industrial machines, physics-based telemetry jitter, and controlled fault injection.
"""
import random
import time
import threading
from datetime import datetime
from typing import Dict, Any

from app.mqtt.client import mqtt_manager


class IoTSimulator:
    def __init__(self):
        self.running = False
        self._thread: threading.Thread = None
        self.interval_seconds = 3.0

        # Base configuration of simulated fleet
        self.devices: Dict[str, Dict[str, Any]] = {
            "MTR-101": {
                "device_id": "MTR-101",
                "device_type": "Induction Motor",
                "rpm": 1480.0,
                "base_vib_rms": 1.2,
                "base_vib_peak": 0.4,
                "base_temp": 52.0,
                "base_current": 18.5,
                "fault_mode": "NORMAL",
                "fault_severity": 0.0
            },
            "PUMP-204": {
                "device_id": "PUMP-204",
                "device_type": "Centrifugal Pump",
                "rpm": 2950.0,
                "base_vib_rms": 1.6,
                "base_vib_peak": 0.6,
                "base_temp": 46.0,
                "base_current": 32.0,
                "base_pressure": 6.8,
                "base_flow": 85.0,
                "fault_mode": "NORMAL",
                "fault_severity": 0.0
            },
            "CMP-301": {
                "device_id": "CMP-301",
                "device_type": "Screw Compressor",
                "rpm": 3000.0,
                "base_vib_rms": 2.1,
                "base_vib_peak": 0.7,
                "base_temp": 68.0,
                "base_current": 45.0,
                "base_pressure": 8.5,
                "fault_mode": "NORMAL",
                "fault_severity": 0.0
            },
            "FAN-402": {
                "device_id": "FAN-402",
                "device_type": "Exhaust Blower Fan",
                "rpm": 980.0,
                "base_vib_rms": 1.4,
                "base_vib_peak": 0.3,
                "base_temp": 42.0,
                "base_current": 12.0,
                "fault_mode": "NORMAL",
                "fault_severity": 0.0
            }
        }

    def start(self):
        if not self.running:
            self.running = True
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()
            print("[IoTSimulator] Background telemetry simulator started.")

    def stop(self):
        self.running = False

    def inject_fault(self, device_id: str, fault_code: str, severity: float = 1.0):
        """Inject a fault: E101_BEARING_DEGRADATION, E204_MOTOR_OVERHEAT, E305_PUMP_CAVITATION, E401_ROTOR_UNBALANCE, NORMAL."""
        if device_id in self.devices:
            self.devices[device_id]["fault_mode"] = fault_code
            self.devices[device_id]["fault_severity"] = max(0.0, min(1.0, severity))
            print(f"[IoTSimulator] Injected {fault_code} (severity={severity}) into {device_id}")
            return True
        return False

    def _generate_telemetry(self, dev: Dict[str, Any]) -> Dict[str, Any]:
        fault = dev["fault_mode"]
        sev = dev["fault_severity"]

        # Jitter
        vib_rms = dev["base_vib_rms"] + random.uniform(-0.1, 0.1)
        vib_peak = dev["base_vib_peak"] + random.uniform(-0.05, 0.05)
        temp = dev["base_temp"] + random.uniform(-0.5, 0.5)
        current = dev["base_current"] + random.uniform(-0.3, 0.3)
        pressure = dev.get("base_pressure")
        flow = dev.get("base_flow")

        # Physics-based fault signatures
        if fault == "E101_BEARING_DEGRADATION":
            vib_rms += 2.5 * sev + random.uniform(0.1, 0.4)
            vib_peak += 3.2 * sev + random.uniform(0.2, 0.6)  # High peak acceleration spikes
            temp += 28.0 * sev  # Bearing friction heat

        elif fault == "E204_MOTOR_OVERHEAT":
            temp += 45.0 * sev + random.uniform(0.5, 2.0)  # Thermal rise above 95°C
            current += (dev["base_current"] * 0.35) * sev
            vib_rms += 1.0 * sev

        elif fault == "E305_PUMP_CAVITATION":
            vib_rms += 4.2 * sev + random.uniform(0.3, 0.9)  # Violent broad-band vibration
            vib_peak += 2.8 * sev
            if pressure is not None:
                pressure = max(0.8, pressure - (3.5 * sev) + random.uniform(-0.4, 0.4))
            if flow is not None:
                flow = max(20.0, flow - (35.0 * sev))

        elif fault == "E401_ROTOR_UNBALANCE":
            vib_rms += 5.8 * sev + random.uniform(0.2, 0.5)  # 1X RPM dominant vibration
            vib_peak += 1.2 * sev
            current += 4.0 * sev

        elif fault == "E502_PHASE_IMBALANCE":
            current += 8.5 * sev + random.uniform(-1.0, 1.0)
            temp += 22.0 * sev
            vib_rms += 2.0 * sev

        # Cap minimums and round
        payload = {
            "device_id": dev["device_id"],
            "device_type": dev["device_type"],
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "vibration_rms": round(max(0.1, vib_rms), 2),
            "vibration_peak": round(max(0.05, vib_peak), 2),
            "temperature": round(temp, 1),
            "current_draw": round(current, 1),
            "rpm": dev["rpm"],
            "fault_code": fault
        }
        if pressure is not None:
            payload["pressure"] = round(pressure, 2)
        if flow is not None:
            payload["flow_rate"] = round(flow, 1)

        return payload

    def _run_loop(self):
        while self.running:
            for dev_id, dev_cfg in self.devices.items():
                if not self.running:
                    break
                telemetry = self._generate_telemetry(dev_cfg)
                
                # Publish to MQTT broker
                mqtt_manager.publish_telemetry(dev_id, telemetry)
                
                # Also pass directly to handle telemetry if broker loop hasn't triggered or if testing locally
                mqtt_manager._handle_telemetry(telemetry)

            time.sleep(self.interval_seconds)


# Global singleton instance
iot_simulator = IoTSimulator()
