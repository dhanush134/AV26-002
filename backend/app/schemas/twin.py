from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import MEDICAL_DISCLAIMER, ORMModel


class TwinGoalCreate(BaseModel):
    target_age: int = Field(ge=1, le=120)
    target_weight_kg: float | None = Field(default=None, ge=10, le=300)
    target_sleep_hours: float | None = Field(default=None, ge=0, le=24)
    target_steps: int | None = Field(default=None, ge=0)
    target_resting_hr: int | None = Field(default=None, ge=30, le=250)
    target_bp_systolic: int | None = Field(default=None, ge=40, le=260)
    target_bp_diastolic: int | None = Field(default=None, ge=30, le=180)
    target_ldl: float | None = Field(default=None, ge=0, le=500)
    goal_description: str | None = None


class TwinGoalResponse(TwinGoalCreate, ORMModel):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime


class TwinSummaryResponse(BaseModel):
    user_id: UUID
    current_twin: dict
    ideal_twin: dict | None = None
    twin_gap: dict | None = None
    twin_alignment_score: float | None = Field(default=None, ge=0, le=100)
    disclaimer: str = MEDICAL_DISCLAIMER
