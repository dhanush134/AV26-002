from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class LifestyleBase(BaseModel):
    smoking_status: str | None = Field(default=None, max_length=100)
    alcohol_frequency: str | None = Field(default=None, max_length=100)
    exercise_frequency: str | None = Field(default=None, max_length=100)
    diet_quality: str | None = Field(default=None, max_length=100)
    stress_level: str | None = Field(default=None, max_length=100)
    sleep_goal_hours: float | None = Field(default=None, ge=0, le=24)
    medical_conditions: list[str] | dict[str, Any] | None = None
    family_history: list[str] | dict[str, Any] | None = None


class LifestyleCreate(LifestyleBase):
    pass


class LifestyleUpdate(LifestyleBase):
    pass


class LifestyleResponse(LifestyleBase, ORMModel):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
