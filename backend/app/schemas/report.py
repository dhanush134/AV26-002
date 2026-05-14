from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import MEDICAL_DISCLAIMER


class DoctorReportResponse(BaseModel):
    user_id: UUID
    user_profile: dict
    latest_vitals_summary: dict | None
    latest_lab_summary: dict | None
    latest_risk_scores: dict | None
    top_risk_factors: list[dict]
    recent_alerts: list[dict]
    preventive_plan: dict
    disclaimer: str = MEDICAL_DISCLAIMER


class PreventivePlanResponse(BaseModel):
    user_id: UUID
    focus_areas: list[str]
    daily_routine: list[dict]
    weekly_targets: dict
    follow_up_suggestions: list[str]
    disclaimer: str = MEDICAL_DISCLAIMER
