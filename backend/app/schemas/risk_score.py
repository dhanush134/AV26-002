from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import MEDICAL_DISCLAIMER, ORMModel


class RiskFactor(BaseModel):
    category: str
    factor: str
    severity: str
    reason: str
    suggested_action: str


class RiskScoreResponse(ORMModel):
    id: UUID
    user_id: UUID
    calculated_at: datetime
    cardio_score: float = Field(ge=0, le=100)
    metabolic_score: float = Field(ge=0, le=100)
    sleep_score: float = Field(ge=0, le=100)
    activity_score: float = Field(ge=0, le=100)
    lifestyle_score: float = Field(ge=0, le=100)
    anomaly_score: float = Field(ge=0, le=100)
    twin_alignment_score: float = Field(ge=0, le=100)
    overall_risk_level: str
    explanation: str
    risk_factors: list[RiskFactor] | list[dict[str, Any]]
    recommendations: list[dict[str, Any]] | list[str]
    created_at: datetime
    disclaimer: str = MEDICAL_DISCLAIMER
