from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import MEDICAL_DISCLAIMER, ORMModel


AlertSeverity = Literal["info", "warning", "critical"]


class AlertCreate(BaseModel):
    alert_type: str = Field(max_length=100)
    severity: AlertSeverity
    title: str = Field(max_length=255)
    message: str
    recommended_action: str
    source: str | None = Field(default=None, max_length=100)


class AlertResponse(AlertCreate, ORMModel):
    id: UUID
    user_id: UUID
    acknowledged: bool
    created_at: datetime
    updated_at: datetime
    disclaimer: str = MEDICAL_DISCLAIMER
