from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class DailyCheckinBase(BaseModel):
    checkin_date: date | None = None
    sleep_quality: str | None = Field(default=None, max_length=100)
    exercise_done: str | None = Field(default=None, max_length=100)
    food_quality: str | None = Field(default=None, max_length=100)
    alcohol_used: bool | None = None
    smoking_done: bool | None = None
    stress_level: str | None = Field(default=None, max_length=100)
    steps_completed: int | None = Field(default=None, ge=0)
    sleep_hours: float | None = Field(default=None, ge=0, le=24)
    user_notes: str | None = None


class DailyCheckinCreate(DailyCheckinBase):
    pass


class DailyCheckinResponse(DailyCheckinBase, ORMModel):
    id: UUID
    user_id: UUID
    checkin_date: date
    created_at: datetime


class TwinActionResponse(ORMModel):
    id: UUID
    user_id: UUID
    action_date: date
    category: str
    recommended_action: str
    priority: str
    completed: bool
    created_at: datetime
    updated_at: datetime


class DailyRoutineResponse(BaseModel):
    user_id: UUID
    routine_date: date
    focus_areas: list[str]
    actions: list[dict]


class DailyAdjustmentResponse(BaseModel):
    user_id: UUID
    alignment_delta: float
    previous_alignment: float | None = None
    new_alignment: float | None = None
    missed_items: list[str]
    tomorrow_adjustments: list[dict] | list[str]
    encouraging_message: str


class DailyCheckinAdjustmentResponse(DailyAdjustmentResponse):
    checkin: DailyCheckinResponse
