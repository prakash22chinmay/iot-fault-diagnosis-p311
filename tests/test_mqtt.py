"""
Unit tests for MQTT Telemetry serialization and simulator.
"""
import sys
from pathlib import Path
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.mqtt.simulator import iot_simulator
from app.mqtt.client import mqtt_manager
from app.models.telemetry import TelemetryData


class TestMQTTAndSimulator(unittest.TestCase):
    def test_telemetry_model(self):
        t = TelemetryData(
            device_id="PUMP-204",
            device_type="Centrifugal Pump",
            vibration_rms=1.5,
            vibration_peak=0.4,
            temperature=45.0,
            current_draw=16.0,
            pressure=5.2
        )
        self.assertEqual(t.device_id, "PUMP-204")
        self.assertEqual(t.health_index, 100.0)

    def test_simulator_generation(self):
        dev = iot_simulator.devices["MTR-101"]
        data = iot_simulator._generate_telemetry(dev)
        self.assertEqual(data["device_id"], "MTR-101")
        self.assertIn("vibration_rms", data)
        self.assertIn("temperature", data)

    def test_fault_injection(self):
        iot_simulator.inject_fault("PUMP-204", "E305_PUMP_CAVITATION", severity=1.0)
        dev = iot_simulator.devices["PUMP-204"]
        self.assertEqual(dev["fault_mode"], "E305_PUMP_CAVITATION")
        data = iot_simulator._generate_telemetry(dev)
        self.assertGreater(data["vibration_rms"], 3.0)
        
        # Restore normal
        iot_simulator.inject_fault("PUMP-204", "NORMAL")
        self.assertEqual(dev["fault_mode"], "NORMAL")


if __name__ == "__main__":
    unittest.main()
