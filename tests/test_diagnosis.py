"""
Unit tests for Diagnostic Engine and ISO 10816 Classification.
"""
import sys
from pathlib import Path
import unittest
import asyncio

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.llm.diagnosis_engine import diagnostic_engine
from app.models.telemetry import TelemetryData
from app.models.diagnosis import DiagnosisRequest


class TestDiagnosisEngine(unittest.TestCase):
    def test_iso_10816_zones(self):
        res_a = diagnostic_engine.evaluate_iso_zone(1.1)
        self.assertEqual(res_a["zone"], "Zone A")
        self.assertEqual(res_a["status"], "HEALTHY")

        res_b = diagnostic_engine.evaluate_iso_zone(2.2)
        self.assertEqual(res_b["zone"], "Zone B")
        self.assertEqual(res_b["status"], "HEALTHY")

        res_c = diagnostic_engine.evaluate_iso_zone(3.8)
        self.assertEqual(res_c["zone"], "Zone C")
        self.assertEqual(res_c["status"], "WARNING")

        res_d = diagnostic_engine.evaluate_iso_zone(8.5)
        self.assertEqual(res_d["zone"], "Zone D")
        self.assertEqual(res_d["status"], "CRITICAL")

    def test_expert_diagnosis_bearing(self):
        telemetry = TelemetryData(
            device_id="MTR-101",
            device_type="Induction Motor",
            vibration_rms=5.2,
            vibration_peak=2.9,
            temperature=82.0,
            current_draw=22.4,
            fault_code="E101_BEARING_DEGRADATION"
        )
        req = DiagnosisRequest(device_id="MTR-101", custom_telemetry=telemetry)
        
        resp = asyncio.run(diagnostic_engine.diagnose(req))
        self.assertEqual(resp.device_id, "MTR-101")
        self.assertIn(resp.severity, ("WARNING", "CRITICAL"))
        self.assertTrue("bearing" in resp.fault_identified.lower() or "bearing" in resp.root_cause_analysis.lower())
        self.assertGreaterEqual(len(resp.prescribed_actions), 1)
        self.assertGreaterEqual(len(resp.retrieved_references), 1)

    def test_chat_copilot(self):
        reply = asyncio.run(diagnostic_engine.chat("What are the vibration limits for Zone C under ISO 10816-3?"))
        self.assertGreater(len(reply), 20)
        self.assertTrue("ISO" in reply or "Zone" in reply or "vibration" in reply.lower())


if __name__ == "__main__":
    unittest.main()
