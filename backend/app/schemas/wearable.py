from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


WearableSource = Literal["manual", "synthetic", "dataset", "watch"]


class WearableReadingBase(BaseModel):
    timestamp: datetime | None = None
    heart_rate: int | None = Field(default=None, ge=30, le=250)
    resting_heart_rate: int | None = Field(default=None, ge=30, le=250)
    spo2: float | None = Field(default=None, ge=50, le=100)
    steps: int | None = Field(default=None, ge=0)
    active_minutes: int | None = Field(default=None, ge=0, le=1440)
    sleep_hours: float | None = Field(default=None, ge=0, le=24)
    sleep_quality: float | None = Field(default=None, ge=0, le=100)
    calories: float | None = Field(default=None, ge=0)
    stress_score: float | None = Field(default=None, ge=0, le=100)
    source: WearableSource = "manual"


class WearableReadingCreate(WearableReadingBase):
    pass


class WearableBulkCreate(BaseModel):
    readings: list[WearableReadingCreate] = Field(min_length=1, max_length=1000)


class WearableReadingResponse(WearableReadingBase, ORMModel):
    id: UUID
    user_id: UUID
    timestamp: datetime
    created_at: datetime


class WearableSummary(BaseModel):
    count: int
    average_steps: float | None
    average_sleep_hours: float | None
    average_resting_heart_rate: float | None
    latest_reading: WearableReadingResponse | None
