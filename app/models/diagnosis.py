"""
Diagnosis request and response models for RAG and LLM diagnostic engine.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from app.models.telemetry import TelemetryData


class KnowledgeChunk(BaseModel):
    doc_id: str
    title: str
    category: str
    section: str
    content: str
    similarity_score: float = 0.0


class DiagnosisRequest(BaseModel):
    device_id: str
    symptom_description: Optional[str] = Field(
        default=None,
        description="Optional human-observed symptom or question (e.g. 'Unusual whistling sound, high casing heat')"
    )
    custom_telemetry: Optional[TelemetryData] = None


class PrescribedAction(BaseModel):
    step: int
    action: str
    urgency: str  # "IMMEDIATE", "NEXT_SHIFT", "SCHEDULED_MAINTENANCE"
    technician_role: str  # "Mechanical Technician", "Electrical Engineer", "Lubrication Specialist"


class DiagnosisResponse(BaseModel):
    diagnosis_id: str
    device_id: str
    device_type: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    severity: str  # "HEALTHY", "WARNING", "CRITICAL"
    iso_compliance: str
    fault_identified: str
    root_cause_analysis: str
    prescribed_actions: List[PrescribedAction]
    retrieved_references: List[KnowledgeChunk]
    safety_precautions: List[str]
    estimated_rul: str  # Remaining Useful Life estimation
    llm_model_used: str


class ChatMessage(BaseModel):
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


class ChatRequest(BaseModel):
    message: str
    device_id: Optional[str] = None
    conversation_history: List[ChatMessage] = []
