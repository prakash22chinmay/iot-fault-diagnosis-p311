"""
Integration tests for FastAPI REST API endpoints and fault injection flow.
"""
import sys
from pathlib import Path
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from app.api.app import app
from app.mqtt.simulator import iot_simulator
from app.mqtt.client import mqtt_manager


class TestAPIEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_info_endpoint(self):
        resp = self.client.get("/api/info")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["project_id"], "P_311")
        self.assertEqual(data["project_name"], "Knowledge driven IoT fault diagnosis assistant")

    def test_devices_list(self):
        resp = self.client.get("/api/devices")
        self.assertEqual(resp.status_code, 200)
        devices = resp.json()
        self.assertEqual(len(devices), 4)

    def test_web_ui_served(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("IoT Fault Diagnosis Assistant", resp.text)
        self.assertIn("P_311", resp.text)

    def test_fault_injection_and_diagnosis(self):
        # Inject bearing defect
        inj_resp = self.client.post("/api/simulator/inject?device_id=MTR-101&fault_code=E101_BEARING_DEGRADATION&severity=1.0")
        self.assertEqual(inj_resp.status_code, 200)

        # Trigger one simulation tick for MTR-101
        telemetry = iot_simulator._generate_telemetry(iot_simulator.devices["MTR-101"])
        mqtt_manager._handle_telemetry(telemetry)

        # Request diagnosis
        diag_resp = self.client.post("/api/diagnose", json={"device_id": "MTR-101"})
        self.assertEqual(diag_resp.status_code, 200)
        diag = diag_resp.json()
        self.assertIn(diag["severity"], ("WARNING", "CRITICAL"))
        self.assertTrue("bearing" in diag["fault_identified"].lower() or "bearing" in diag["root_cause_analysis"].lower())
        self.assertGreaterEqual(len(diag["prescribed_actions"]), 1)
        self.assertGreaterEqual(len(diag["retrieved_references"]), 1)

        # Restore normal
        self.client.post("/api/simulator/inject?device_id=MTR-101&fault_code=NORMAL&severity=0.0")

    def test_chat_copilot_endpoint(self):
        resp = self.client.post("/api/chat", json={"message": "What is cavitation in centrifugal pumps?"})
        self.assertEqual(resp.status_code, 200)
        reply = resp.json()["reply"]
        self.assertGreater(len(reply), 30)


if __name__ == "__main__":
    unittest.main()
