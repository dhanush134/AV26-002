from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class LabReportBase(BaseModel):
    report_date: date
    bp_systolic: int | None = Field(default=None, ge=40, le=260)
    bp_diastolic: int | None = Field(default=None, ge=30, le=180)
    fasting_glucose: float | None = Field(default=None, ge=20, le=600)
    hba1c: float | None = Field(default=None, ge=2, le=20)
    ldl: float | None = Field(default=None, ge=0, le=500)
    hdl: float | None = Field(default=None, ge=0, le=200)
    triglycerides: float | None = Field(default=None, ge=0, le=1000)
    vitamin_d: float | None = Field(default=None, ge=0, le=200)
    vitamin_b12: float | None = Field(default=None, ge=0, le=3000)
    sgpt: float | None = Field(default=None, ge=0, le=2000)
    sgot: float | None = Field(default=None, ge=0, le=2000)
    creatinine: float | None = Field(default=None, ge=0, le=20)
    notes: str | None = None


class LabReportCreate(LabReportBase):
    pass


class LabReportUpdate(BaseModel):
    report_date: date | None = None
    bp_systolic: int | None = Field(default=None, ge=40, le=260)
    bp_diastolic: int | None = Field(default=None, ge=30, le=180)
    fasting_glucose: float | None = Field(default=None, ge=20, le=600)
    hba1c: float | None = Field(default=None, ge=2, le=20)
    ldl: float | None = Field(default=None, ge=0, le=500)
    hdl: float | None = Field(default=None, ge=0, le=200)
    triglycerides: float | None = Field(default=None, ge=0, le=1000)
    vitamin_d: float | None = Field(default=None, ge=0, le=200)
    vitamin_b12: float | None = Field(default=None, ge=0, le=3000)
    sgpt: float | None = Field(default=None, ge=0, le=2000)
    sgot: float | None = Field(default=None, ge=0, le=2000)
    creatinine: float | None = Field(default=None, ge=0, le=20)
    notes: str | None = None


class LabReportResponse(LabReportBase, ORMModel):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
