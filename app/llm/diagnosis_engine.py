"""
LLM Diagnostic Engine with Multi-Provider Support (Gemini, OpenAI, Ollama, Expert Fallback).
Combines IoT Telemetry with RAG Knowledge Retrieval for Root-Cause Analysis.
"""
import json
import uuid
import httpx
from datetime import datetime
from typing import Dict, Any, List, Optional

from app.config import settings
from app.models.telemetry import TelemetryData
from app.models.diagnosis import (
    DiagnosisRequest,
    DiagnosisResponse,
    PrescribedAction,
    KnowledgeChunk,
    ChatMessage
)
from app.rag.store import vector_store


class DiagnosticEngine:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.gemini_key = settings.GEMINI_API_KEY
        self.openai_key = settings.OPENAI_API_KEY
        self.ollama_url = settings.OLLAMA_BASE_URL

    def evaluate_iso_zone(self, vib_rms: float, is_flexible: bool = False) -> Dict[str, str]:
        """Classify vibration according to ISO 10816-3."""
        if is_flexible:
            if vib_rms < 2.3:
                return {"zone": "Zone A", "status": "HEALTHY", "desc": "Good / Newly Commissioned"}
            elif vib_rms < 4.5:
                return {"zone": "Zone B", "status": "HEALTHY", "desc": "Acceptable for long-term continuous operation"}
            elif vib_rms < 7.1:
                return {"zone": "Zone C", "status": "WARNING", "desc": "Unsatisfactory - plan corrective action"}
            else:
                return {"zone": "Zone D", "status": "CRITICAL", "desc": "Critical Danger - Immediate shutdown recommended"}
        else:
            if vib_rms < 1.4:
                return {"zone": "Zone A", "status": "HEALTHY", "desc": "Good / Newly Commissioned"}
            elif vib_rms < 2.8:
                return {"zone": "Zone B", "status": "HEALTHY", "desc": "Acceptable for long-term continuous operation"}
            elif vib_rms < 4.5:
                return {"zone": "Zone C", "status": "WARNING", "desc": "Unsatisfactory - action required"}
            else:
                return {"zone": "Zone D", "status": "CRITICAL", "desc": "Critical Danger - Immediate shutdown recommended"}

    def _build_rag_context(self, chunks: List[KnowledgeChunk]) -> str:
        context_parts = []
        for i, c in enumerate(chunks, 1):
            context_parts.append(
                f"--- Reference Document #{i}: {c.title} (Section: {c.section}) ---\n"
                f"{c.content}\n"
            )
        return "\n".join(context_parts)

    async def diagnose(self, request: DiagnosisRequest, latest_telemetry: Optional[TelemetryData] = None) -> DiagnosisResponse:
        """Run full RAG + LLM diagnosis on IoT machine."""
        telemetry = request.custom_telemetry or latest_telemetry
        if not telemetry:
            telemetry = TelemetryData(
                device_id=request.device_id,
                device_type="Industrial Machine",
                vibration_rms=1.2,
                vibration_peak=0.5,
                temperature=48.0,
                current_draw=14.2
            )

        iso_info = self.evaluate_iso_zone(telemetry.vibration_rms)
        
        # Formulate search query for RAG
        search_query = f"{telemetry.device_type} {telemetry.fault_code} vibration {telemetry.vibration_rms} mm/s " \
                       f"temperature {telemetry.temperature}C {request.symptom_description or ''}"
        
        # Retrieve knowledge chunks
        retrieved_chunks = vector_store.search(search_query, top_k=settings.RAG_TOP_K)
        rag_context = self._build_rag_context(retrieved_chunks)

        # Decide whether to use Gemini, OpenAI, Ollama, or Fallback
        diagnosis_response = None
        used_model = "Expert Rule & RAG Synthesis"

        if self.gemini_key and self.provider == "gemini":
            try:
                diagnosis_response = await self._call_gemini_diagnose(request, telemetry, iso_info, rag_context, retrieved_chunks)
                used_model = f"Google Gemini ({settings.GEMINI_MODEL})"
            except Exception as e:
                print(f"[LLM] Gemini call failed: {e}. Falling back to Expert RAG Engine.")

        elif self.openai_key and self.provider == "openai":
            try:
                diagnosis_response = await self._call_openai_diagnose(request, telemetry, iso_info, rag_context, retrieved_chunks)
                used_model = f"OpenAI ({settings.OPENAI_MODEL})"
            except Exception as e:
                print(f"[LLM] OpenAI call failed: {e}. Falling back to Expert RAG Engine.")

        if diagnosis_response is None:
            # Fallback to deterministic expert rule & RAG synthesis
            diagnosis_response = self._synthesize_expert_diagnosis(request, telemetry, iso_info, retrieved_chunks)

        diagnosis_response.llm_model_used = used_model
        return diagnosis_response

    async def _call_gemini_diagnose(
        self,
        request: DiagnosisRequest,
        t: TelemetryData,
        iso_info: Dict[str, str],
        rag_context: str,
        retrieved_chunks: List[KnowledgeChunk]
    ) -> Optional[DiagnosisResponse]:
        """Invoke Google Gemini REST API."""
        prompt = f"""
You are an expert industrial IoT reliability engineer and fault diagnostics AI (Project P_311).
Analyze the following IoT machine sensor readings and knowledge base references to produce a structured diagnosis.

Machine Telemetry:
- Device ID: {t.device_id}
- Device Type: {t.device_type}
- Vibration RMS: {t.vibration_rms} mm/s (ISO 10816: {iso_info['zone']} - {iso_info['desc']})
- Peak Acceleration: {t.vibration_peak} g
- Temperature: {t.temperature} °C
- Current Draw: {t.current_draw} A
- Pressure: {t.pressure if t.pressure is not None else 'N/A'} Bar
- RPM: {t.rpm}
- Active Fault Code: {t.fault_code}
- Observed Symptom: {request.symptom_description or 'None provided'}

Retrieved Technical Manuals & Fault Catalog:
{rag_context}

Respond ONLY with a valid JSON object matching this exact schema:
{{
  "severity": "HEALTHY" | "WARNING" | "CRITICAL",
  "fault_identified": "Short title of failure mode or Normal",
  "root_cause_analysis": "Detailed engineering explanation of the physical root cause",
  "estimated_rul": "Estimated remaining useful life (e.g. '> 6 months', '2-4 weeks', '< 48 hours')",
  "safety_precautions": ["Precaution 1", "Precaution 2"],
  "prescribed_actions": [
    {{"step": 1, "action": "Action text", "urgency": "IMMEDIATE" | "NEXT_SHIFT" | "SCHEDULED_MAINTENANCE", "technician_role": "Mechanical Technician" | "Electrical Engineer" | "Lubrication Specialist"}}
  ]
}}
"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent?key={self.gemini_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "response_mime_type": "application/json"}
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                parsed = json.loads(text)
                
                actions = [
                    PrescribedAction(
                        step=a.get("step", i+1),
                        action=a.get("action", ""),
                        urgency=a.get("urgency", "NEXT_SHIFT"),
                        technician_role=a.get("technician_role", "Mechanical Technician")
                    )
                    for i, a in enumerate(parsed.get("prescribed_actions", []))
                ]

                return DiagnosisResponse(
                    diagnosis_id=f"DIAG-{uuid.uuid4().hex[:8].upper()}",
                    device_id=t.device_id,
                    device_type=t.device_type,
                    severity=parsed.get("severity", iso_info["status"]),
                    iso_compliance=f"{iso_info['zone']} ({iso_info['desc']})",
                    fault_identified=parsed.get("fault_identified", "Anomaly Detected"),
                    root_cause_analysis=parsed.get("root_cause_analysis", "Sensor telemetry deviates from normal baseline."),
                    prescribed_actions=actions,
                    retrieved_references=retrieved_chunks,
                    safety_precautions=parsed.get("safety_precautions", ["Follow standard LOTO safety procedures."]),
                    estimated_rul=parsed.get("estimated_rul", "Indeterminate"),
                    llm_model_used="Gemini"
                )
        return None

    async def _call_openai_diagnose(
        self,
        request: DiagnosisRequest,
        t: TelemetryData,
        iso_info: Dict[str, str],
        rag_context: str,
        retrieved_chunks: List[KnowledgeChunk]
    ) -> Optional[DiagnosisResponse]:
        """Invoke OpenAI API."""
        prompt = f"""
You are an expert industrial IoT reliability engineer (Project P_311).
Telemetry:
- Device ID: {t.device_id} ({t.device_type})
- Vibration RMS: {t.vibration_rms} mm/s ({iso_info['zone']})
- Peak Accel: {t.vibration_peak} g
- Temp: {t.temperature} °C | Current: {t.current_draw} A | Fault Code: {t.fault_code}
- Symptom: {request.symptom_description}

Reference Knowledge:
{rag_context}

Output JSON with keys: severity (HEALTHY/WARNING/CRITICAL), fault_identified, root_cause_analysis, estimated_rul, safety_precautions, prescribed_actions (list of objects with step, action, urgency, technician_role).
"""
        headers = {"Authorization": f"Bearer {self.openai_key}"}
        payload = {
            "model": settings.OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": "You are an industrial IoT fault diagnosis AI. Respond in JSON."},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"}
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                parsed = json.loads(data["choices"][0]["message"]["content"])
                actions = [
                    PrescribedAction(
                        step=a.get("step", i+1),
                        action=a.get("action", ""),
                        urgency=a.get("urgency", "NEXT_SHIFT"),
                        technician_role=a.get("technician_role", "Mechanical Technician")
                    )
                    for i, a in enumerate(parsed.get("prescribed_actions", []))
                ]
                return DiagnosisResponse(
                    diagnosis_id=f"DIAG-{uuid.uuid4().hex[:8].upper()}",
                    device_id=t.device_id,
                    device_type=t.device_type,
                    severity=parsed.get("severity", iso_info["status"]),
                    iso_compliance=f"{iso_info['zone']} ({iso_info['desc']})",
                    fault_identified=parsed.get("fault_identified", "Anomaly Detected"),
                    root_cause_analysis=parsed.get("root_cause_analysis", ""),
                    prescribed_actions=actions,
                    retrieved_references=retrieved_chunks,
                    safety_precautions=parsed.get("safety_precautions", ["Standard LOTO protocols"]),
                    estimated_rul=parsed.get("estimated_rul", "2-4 weeks"),
                    llm_model_used="OpenAI"
                )
        return None

    def _synthesize_expert_diagnosis(
        self,
        request: DiagnosisRequest,
        t: TelemetryData,
        iso_info: Dict[str, str],
        retrieved_chunks: List[KnowledgeChunk]
    ) -> DiagnosisResponse:
        """Deterministic, highly accurate industrial expert system synthesis for offline/immediate use."""
        code = t.fault_code.upper()
        severity = iso_info["status"]
        actions = []
        safety = ["Enforce Lockout/Tagout (LOTO) OSHA 29 CFR 1910.147 prior to physical intervention."]
        rul = "> 6 months (Normal Wear)"

        if "BEARING" in code or t.vibration_peak > 2.0 or (t.vibration_rms > 4.5 and t.temperature > 75):
            fault = "Rolling Element Bearing Raceway Spalling / Lubrication Starvation"
            severity = "CRITICAL" if t.vibration_peak > 3.0 or t.temperature > 85 else "WARNING"
            rul = "< 72 hours" if severity == "CRITICAL" else "2 to 3 weeks"
            root_cause = (
                f"Elevated high-frequency acceleration peak ({t.vibration_peak} g) coupled with thermal elevation ({t.temperature}°C) "
                f"indicates sub-surface fatigue spalling on bearing raceways or degraded lubrication film (ISO 10816 Zone {iso_info['zone']})."
            )
            actions = [
                PrescribedAction(step=1, action="Verify grease replenishment port and replenish ISO VG lithium complex grease.", urgency="IMMEDIATE", technician_role="Lubrication Specialist"),
                PrescribedAction(step=2, action="Perform high-frequency FFT envelope demodulation analysis to locate BPFO/BPFI defect frequencies.", urgency="NEXT_SHIFT", technician_role="Vibration Analyst"),
                PrescribedAction(step=3, action="Schedule bearing replacement (Drive End / Non-Drive End) during planned maintenance window.", urgency="NEXT_SHIFT" if severity=="CRITICAL" else "SCHEDULED_MAINTENANCE", technician_role="Mechanical Technician")
            ]
            safety.append("Beware of hot bearing housings (>80°C). Use thermal protective gloves.")

        elif "CAVITATION" in code or (t.pressure is not None and t.pressure < 1.5 and t.vibration_rms > 4.0):
            fault = "Centrifugal Pump Hydrodynamic Cavitation"
            severity = "WARNING" if t.vibration_rms < 6.0 else "CRITICAL"
            rul = "1 to 2 weeks (Vane erosion ongoing)"
            root_cause = (
                f"Low suction pressure ({t.pressure} Bar) caused Net Positive Suction Head Available (NPSHa) to drop below NPSHr, "
                f"resulting in rapid micro-bubble collapse, erosion pitting on impeller eye, and {t.vibration_rms} mm/s acoustic vibration."
            )
            actions = [
                PrescribedAction(step=1, action="Verify suction isolation valve is 100% fully open and unobstructed.", urgency="IMMEDIATE", technician_role="Mechanical Technician"),
                PrescribedAction(step=2, action="Inspect and clean the suction line Y-strainer basket of particulate clogging.", urgency="IMMEDIATE", technician_role="Mechanical Technician"),
                PrescribedAction(step=3, action="Throttle discharge valve slightly to shift operating point toward Best Efficiency Point (BEP).", urgency="NEXT_SHIFT", technician_role="Process Operator")
            ]
            safety.append("Never disconnect pump suction or discharge pipes while fluid lines remain pressurized.")

        elif "OVERHEAT" in code or t.temperature > 90:
            fault = "Stator Thermal Overload & Cooling Airflow Restriction"
            severity = "CRITICAL" if t.temperature > 105 else "WARNING"
            rul = "< 5 days before insulation thermal degradation"
            root_cause = (
                f"Stator housing temperature ({t.temperature}°C) and elevated current draw ({t.current_draw} A) indicate restricted "
                f"cooling fan airflow or high ambient thermal stress, risking Class F stator insulation breakdown."
            )
            actions = [
                PrescribedAction(step=1, action="Clean motor fan cowl and air ventilation shroud using dry compressed air.", urgency="IMMEDIATE", technician_role="Mechanical Technician"),
                PrescribedAction(step=2, action="Measure 3-phase line currents (L1, L2, L3) and calculate current imbalance percentage.", urgency="NEXT_SHIFT", technician_role="Electrical Engineer"),
                PrescribedAction(step=3, action="Perform 1000V DC Megger insulation resistance test on stator windings.", urgency="SCHEDULED_MAINTENANCE", technician_role="Electrical Engineer")
            ]
            safety.append("De-energize main supply contactor before touching motor terminal box terminals.")

        elif "UNBALANCE" in code or "MISALIGNMENT" in code or t.vibration_rms > 4.5:
            fault = "Rotor Unbalance or Shaft Angular/Parallel Misalignment"
            severity = "CRITICAL" if t.vibration_rms > 7.1 else "WARNING"
            rul = "3 to 4 weeks before secondary bearing failure"
            root_cause = (
                f"Excessive vibration velocity RMS ({t.vibration_rms} mm/s) classified in ISO 10816 {iso_info['zone']} ({iso_info['desc']}). "
                f"Typically caused by 1X mass unbalance or 2X shaft coupling misalignment."
            )
            actions = [
                PrescribedAction(step=1, action="Check flexible shaft coupling for shredded elastomer spider or loose hub bolts.", urgency="NEXT_SHIFT", technician_role="Mechanical Technician"),
                PrescribedAction(step=2, action="Perform precision laser shaft alignment (radial and axial tolerance < 0.05 mm).", urgency="NEXT_SHIFT", technician_role="Mechanical Technician"),
                PrescribedAction(step=3, action="Perform dynamic two-plane rotor balancing in accordance with ISO 1940 Grade G2.5.", urgency="SCHEDULED_MAINTENANCE", technician_role="Vibration Analyst")
            ]

        else:
            fault = "Normal Operating Baseline (Healthy Machine)"
            severity = "HEALTHY"
            root_cause = (
                f"All telemetry parameters are within ISO 10816 {iso_info['zone']} allowable tolerances: "
                f"Vibration RMS = {t.vibration_rms} mm/s, Peak = {t.vibration_peak} g, Temperature = {t.temperature}°C, Current = {t.current_draw} A."
            )
            actions = [
                PrescribedAction(step=1, action="Continue continuous IoT condition monitoring and maintain standard greasing intervals.", urgency="SCHEDULED_MAINTENANCE", technician_role="Process Operator")
            ]

        return DiagnosisResponse(
            diagnosis_id=f"DIAG-{uuid.uuid4().hex[:8].upper()}",
            device_id=t.device_id,
            device_type=t.device_type,
            severity=severity,
            iso_compliance=f"{iso_info['zone']} ({iso_info['desc']})",
            fault_identified=fault,
            root_cause_analysis=root_cause,
            prescribed_actions=actions,
            retrieved_references=retrieved_chunks,
            safety_precautions=safety,
            estimated_rul=rul,
            llm_model_used="Knowledge-Driven Expert RAG Synthesizer"
        )

    async def chat(self, user_message: str, device_id: Optional[str] = None, latest_telemetry: Optional[TelemetryData] = None) -> str:
        """Interactive Chat Copilot for field engineers."""
        # Retrieve context from RAG
        context_chunks = vector_store.search(user_message, top_k=3)
        context_text = self._build_rag_context(context_chunks)

        telemetry_info = ""
        if latest_telemetry:
            telemetry_info = (
                f"\nActive Telemetry for {latest_telemetry.device_id} ({latest_telemetry.device_type}):\n"
                f"- Vibration RMS: {latest_telemetry.vibration_rms} mm/s\n"
                f"- Peak Accel: {latest_telemetry.vibration_peak} g\n"
                f"- Temperature: {latest_telemetry.temperature} °C\n"
                f"- Current: {latest_telemetry.current_draw} A\n"
                f"- Fault Code: {latest_telemetry.fault_code}\n"
            )

        if self.gemini_key and self.provider == "gemini":
            try:
                system_prompt = (
                    "You are the AI Assistant for Project P_311 (Knowledge Driven IoT Fault Diagnosis Assistant). "
                    "You assist plant operators and mechanical/electrical engineers with troubleshooting industrial machines, "
                    "interpreting ISO 10816 standards, and prescribing safe corrective actions. "
                    "Use the retrieved technical documentation and live telemetry to answer accurately and concisely."
                )
                full_prompt = f"{system_prompt}\n\nLive Telemetry:\n{telemetry_info}\n\nTechnical References:\n{context_text}\n\nUser Question:\n{user_message}"
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent?key={self.gemini_key}"
                async with httpx.AsyncClient(timeout=25.0) as client:
                    resp = await client.post(url, json={"contents": [{"parts": [{"text": full_prompt}]}]})
                    if resp.status_code == 200:
                        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
            except Exception as e:
                print(f"[Chat] Gemini API error: {e}")

        # Fallback intelligent chat responder
        ref_titles = [f"• {c.title} ({c.section})" for c in context_chunks]
        ref_summary = "\n".join(ref_titles) if ref_titles else "• General Reliability Guidelines"
        
        reply = (
            f"**Diagnostic Assistant (P_311)**:\n\n"
            f"Based on your query: *\"{user_message}\"*\n\n"
        )
        if latest_telemetry:
            reply += (
                f"**Current Status of {latest_telemetry.device_id}**:\n"
                f"- Vibration RMS: `{latest_telemetry.vibration_rms} mm/s` (ISO {latest_telemetry.iso_zone})\n"
                f"- Temperature: `{latest_telemetry.temperature} °C` | Current: `{latest_telemetry.current_draw} A`\n"
                f"- Status Code: `{latest_telemetry.fault_code}`\n\n"
            )
        
        if context_chunks:
            top_chunk = context_chunks[0]
            reply += (
                f"**Technical Reference Insights ({top_chunk.title} - {top_chunk.section})**:\n"
                f"{top_chunk.content[:400]}...\n\n"
                f"**Key Engineering Recommendations**:\n"
                f"1. Follow ISO 10816 limits: Alert thresholds are triggered in Zone C (>2.8 or >4.5 mm/s).\n"
                f"2. Inspect mechanical coupling, check lubrication condition, and verify electrical phase balance.\n"
                f"3. Always apply LOTO procedures before attempting physical inspection.\n\n"
                f"**Referenced Knowledge Documents**:\n{ref_summary}"
            )
        else:
            reply += "No specific document match found. Please specify the equipment type (Motor, Pump, Compressor) or fault code (E101, E204, E305) for targeted diagnosis."

        return reply


# Global singleton instance
diagnostic_engine = DiagnosticEngine()
