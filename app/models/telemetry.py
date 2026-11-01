"""
Telemetry models for IoT Fault Diagnosis Assistant.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class TelemetryData(BaseModel):
    device_id: str = Field(..., description="Unique IoT equipment identifier (e.g. MTR-101)")
    device_type: str = Field(..., description="Equipment category: Motor, Pump, Compressor, Fan")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    
    # Key vibration telemetry (ISO 10816 standards)
    vibration_rms: float = Field(..., description="Vibration velocity RMS in mm/s (10-1000 Hz)")
    vibration_peak: float = Field(default=0.0, description="Vibration acceleration peak in g (bearing high-frequency)")
    
    # Thermal & Electrical
    temperature: float = Field(..., description="Bearing / casing temperature in Celsius")
    current_draw: float = Field(..., description="Current consumption in Amperes")
    rpm: float = Field(default=1750.0, description="Rotational speed in RPM")
    
    # Hydraulic / Pneumatic (optional depending on device)
    pressure: Optional[float] = Field(default=None, description="Operating pressure in Bar")
    flow_rate: Optional[float] = Field(default=None, description="Flow rate in m3/h")
    
    # Health Assessment & Diagnostics
    fault_code: str = Field(default="NORMAL", description="Active equipment fault code or NORMAL")
    health_index: float = Field(default=100.0, ge=0.0, le=100.0, description="Machine health percentage")
    iso_zone: str = Field(default="Zone A", description="ISO 10816-3 Zone: Zone A (Good), B (Acceptable), C (Unsatisfactory), D (Critical)")
    is_anomaly: bool = Field(default=False, description="Whether automated edge trigger detected anomaly")


class TelemetryHistoryQuery(BaseModel):
    device_id: Optional[str] = None
    limit: int = 100


class DeviceSummary(BaseModel):
    device_id: str
    device_type: str
    status: str  # "HEALTHY", "WARNING", "CRITICAL", "OFFLINE"
    latest_telemetry: Optional[TelemetryData] = None
    last_updated: str
