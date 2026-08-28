from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime

REQUIRED_THRESHOLD_KEYS = {
    "casino",
    "pyramid",
    "guaranteed_income",
    "referral",
    "investment_scam",
    "block_threshold",
    "flag_threshold",
    "hard_block",
}

class ProfileBase(BaseModel):
    name: str
    thresholds: Dict[str, float]

    @field_validator("thresholds")
    @classmethod
    def validate_thresholds(cls, thresholds: Dict[str, float]) -> Dict[str, float]:
        keys = set(thresholds)
        missing = REQUIRED_THRESHOLD_KEYS - keys
        unknown = keys - REQUIRED_THRESHOLD_KEYS
        if missing:
            raise ValueError(f"Missing threshold keys: {', '.join(sorted(missing))}")
        if unknown:
            raise ValueError(f"Unknown threshold keys: {', '.join(sorted(unknown))}")
        for key, value in thresholds.items():
            if not 0.0 <= float(value) <= 1.0:
                raise ValueError(f"Threshold {key} must be between 0 and 1")
        return thresholds

class ProfileCreate(ProfileBase):
    pass

class ProfileResponse(ProfileBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class ModerationRequest(BaseModel):
    text: Optional[str] = None
    image_base64: Optional[str] = None
    url: Optional[str] = None
    profile_id: int

class ModerationResponse(BaseModel):
    decision: str
    explanation: List[Dict[str, Any]]
    scores: Dict[str, float]
    transcription: Optional[str] = None
    risk_score: Optional[float] = None

class ContentLogResponse(BaseModel):
    id: int
    content_type: str
    content_preview: str
    scores: Dict[str, float]
    profile_id: int
    decision: str
    explanation: List[Dict[str, Any]]
    created_at: datetime
    risk_score: Optional[float] = None
    source_id: Optional[str] = None
    source_platform: Optional[str] = None
    author_handle: Optional[str] = None
    author_url: Optional[str] = None
    caption_text: Optional[str] = None
    transcription_text: Optional[str] = None
    extracted_identifiers: Optional[List[Dict[str, str]]] = None
    model_config = ConfigDict(from_attributes=True)

class ProfileAnalyzeRequest(BaseModel):
    platform: str
    target: str
    profile_id: int

class ProfileAnalyzeResponse(BaseModel):
    account: Dict[str, Any]
    items: List[Dict[str, Any]]
