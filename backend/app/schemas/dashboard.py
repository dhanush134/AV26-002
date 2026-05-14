from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import MEDICAL_DISCLAIMER


class DashboardUser(BaseModel):
    id: UUID
    full_name: str
    age: int
    gender: str | None
    height_cm: float
    weight_kg: float
    bmi: float
    target_age: int | None


class DashboardCurrentStatus(BaseModel):
    overall_risk_level: str
    twin_alignment_score: float = Field(ge=0, le=100)
    anomaly_score: float = Field(ge=0, le=100)
    summary_message: str


class DashboardVitals(BaseModel):
    heart_rate: int | None = None
    resting_heart_rate: int | None = None
    spo2: float | None = None
    steps: int | None = None
    sleep_hours: float | None = None
    active_minutes: int | None = None
    timestamp: datetime | None = None


class DashboardRiskScores(BaseModel):
    cardio_score: float
    metabolic_score: float
    sleep_score: float
    activity_score: float
    lifestyle_score: float


class DashboardRiskFactor(BaseModel):
    category: str
    factor: str
    severity: str
    suggested_action: str


class DashboardAction(BaseModel):
    category: str
    recommended_action: str
    priority: str
    completed: bool = False


class DashboardAlert(BaseModel):
    severity: str
    title: str
    message: str


class ChartPoint(BaseModel):
    timestamp: datetime
    value: float


class RiskBreakdownPoint(BaseModel):
    label: str
    value: float


class DashboardCharts(BaseModel):
    heart_rate_trend: list[ChartPoint]
    sleep_trend: list[ChartPoint]
    steps_trend: list[ChartPoint]
    risk_breakdown: list[RiskBreakdownPoint]


class DashboardResponse(BaseModel):
    user: DashboardUser
    current_status: DashboardCurrentStatus
    latest_vitals: DashboardVitals
    risk_scores: DashboardRiskScores
    top_risk_factors: list[DashboardRiskFactor]
    today_actions: list[DashboardAction]
    recent_alerts: list[DashboardAlert]
    charts: DashboardCharts
    disclaimer: str = MEDICAL_DISCLAIMER
