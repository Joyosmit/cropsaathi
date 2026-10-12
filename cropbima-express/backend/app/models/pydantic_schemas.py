"""Pydantic schemas."""
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

class DocumentProcessResponse(BaseModel):
    farmer_name: str = ""
    survey_khasra_number: str = ""
    land_area_acres: Optional[float] = None
    district_state: str = ""
    crop_type: str = ""
    damage_reason: str = ""
    damage_percentage: Optional[int] = None
    loss_date: str = ""
    confidence: Dict[str, float] = {}
    raw_text: str = ""
    mock: bool = False

class STTResponse(BaseModel):
    transcript: str
    language_code: str
    mock: bool = False

class TTSRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    language_code: str = "hi-IN"
    speaker: str = "simran"
    pace: float = 1.0

class AuditRequest(BaseModel):
    data: Dict[str, Any]
    language: str = "hi-IN"

class AuditResponse(BaseModel):
    eligible: bool
    missing_fields: List[str]
    low_confidence_fields: List[str]
    next_prompts: List[str]
    next_field: Optional[str] = None
    payout_hint: Optional[str] = None

class VoiceFillRequest(BaseModel):
    data: Dict[str, Any]
    transcript: str
    target_field: Optional[str] = None
    language: str = "hi-IN"

class ClaimCreate(BaseModel):
    farmer_name: str = ""
    father_name: str = ""
    survey_khasra_number: str = ""
    land_area_acres: Optional[float] = None
    land_area_hectare: Optional[float] = None
    village_taluka_district: str = ""
    district_state: str = ""
    crop_type: str = ""
    damage_reason: str = ""
    damage_percentage: Optional[int] = None
    loss_date: str = ""
    mobile_number: str = ""
    language: str = "hi-IN"

class ClaimOut(ClaimCreate):
    id: int
    status: str
