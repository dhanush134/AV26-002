from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import MEDICAL_DISCLAIMER


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class BiomarkerInput(StrictModel):
    hba1c: float | None = None
    fasting_glucose: float | None = None
    bp_systolic: int | None = None
    bp_diastolic: int | None = None
    ldl: float | None = None
    hdl: float | None = None
    triglycerides: float | None = None
    vitamin_d: float | None = None
    vitamin_b12: float | None = None
    sgpt: float | None = None
    sgot: float | None = None
    creatinine: float | None = None
    notes: str | None = None


class AdaptiveMetricsInput(StrictModel):
    age: int | None = Field(default=None, ge=1, le=120)
    weight_kg: float | None = Field(default=None, gt=0, le=400)
    height_cm: float | None = Field(default=None, gt=0, le=260)
    stress_score: float | None = Field(default=None, ge=0, le=100)
    heart_rate_bpm: int | None = Field(default=None, ge=25, le=240)
    sleep_hours: float | None = Field(default=None, ge=0, le=24)
    steps: int | None = Field(default=None, ge=0, le=100000)
    workout_info: str | None = Field(default=None, max_length=1000)
    biomarkers: BiomarkerInput | None = None


NegativeChoice = Literal[
    "alcohol",
    "smoking",
    "high_sugar",
    "fried_food",
    "late_heavy_meal",
    "missed_sleep_window",
    "missed_workout",
    "very_high_stress",
    "low_water",
    "excess_caffeine",
]


class PlanFeedbackInput(StrictModel):
    completed_activity_ids: list[str] = Field(default_factory=list, max_length=30)
    skipped_activity_ids: list[str] = Field(default_factory=list, max_length=30)
    negative_choices: list[NegativeChoice] = Field(default_factory=list, max_length=10)
    notes: str | None = Field(default=None, max_length=2000)


class AdaptivePlanRequest(StrictModel):
    plan_date: date | None = None
    metrics: AdaptiveMetricsInput | None = None
    previous_day: PlanFeedbackInput | None = None


class AdaptiveCheckinRequest(StrictModel):
    plan_date: date | None = None
    metrics: AdaptiveMetricsInput | None = None
    feedback: PlanFeedbackInput


class IdealState(StrictModel):
    bmi_range: str
    sleep_hours: str
    steps: str
    resting_heart_rate_bpm: str
    blood_pressure: str
    metabolic_markers: str
    nutrition_pattern: str


class TimelineEstimate(StrictModel):
    estimated_weeks: int = Field(ge=1, le=260)
    confidence: Literal["low", "medium", "high"]
    summary: str
    next_review_date: date
    assumptions: list[str] = Field(default_factory=list, max_length=8)


class PlannedActivity(StrictModel):
    id: str
    time_window: str
    title: str
    category: str
    target: str
    why: str
    priority: Literal["critical", "high", "medium", "low"]
    strict_rule: str
    progression_note: str


class MacroDistribution(StrictModel):
    protein_percent: int = Field(ge=0, le=100)
    carbs_percent: int = Field(ge=0, le=100)
    fats_percent: int = Field(ge=0, le=100)
    fiber_grams: int = Field(ge=0, le=100)
    water_liters: float = Field(ge=0, le=10)


class MealPlan(StrictModel):
    meal: Literal["breakfast", "lunch", "snack", "dinner"]
    composition: str
    north_indian_veg: list[str] = Field(default_factory=list, max_length=4)
    north_indian_non_veg: list[str] = Field(default_factory=list, max_length=4)
    south_indian_veg: list[str] = Field(default_factory=list, max_length=4)
    south_indian_non_veg: list[str] = Field(default_factory=list, max_length=4)
    note: str


class SupplementGuidance(StrictModel):
    name: str
    priority: Literal["critical", "high", "medium", "optional", "avoid"]
    why: str
    suggested_timing: str
    safety_note: str


class NutritionPlan(StrictModel):
    macro_distribution: MacroDistribution
    meals: list[MealPlan] = Field(min_length=3, max_length=5)
    supplement_guidance: list[SupplementGuidance] = Field(default_factory=list, max_length=8)


class AdaptivePlanResponse(StrictModel):
    user_id: UUID
    plan_date: date
    generated_by: Literal["openai", "fallback"]
    model_used: str
    strictness: Literal["strict", "progressive", "recovery"]
    summary: str
    ideal_state: IdealState
    timeline: TimelineEstimate
    activities: list[PlannedActivity] = Field(min_length=5, max_length=12)
    negative_options: list[NegativeChoice]
    checkin_prompt: str
    nutrition: NutritionPlan
    safety_notes: list[str] = Field(default_factory=lambda: [MEDICAL_DISCLAIMER], max_length=6)


class RoutinePlanResponse(StrictModel):
    user_id: UUID
    plan_date: date
    generated_by: Literal["openai", "fallback"]
    model_used: str
    strictness: Literal["strict", "progressive", "recovery"]
    summary: str
    timeline: TimelineEstimate
    activities: list[PlannedActivity] = Field(min_length=5, max_length=12)
    negative_options: list[NegativeChoice]
    checkin_prompt: str
    safety_notes: list[str] = Field(default_factory=lambda: [MEDICAL_DISCLAIMER], max_length=6)


class NutritionPlanResponse(StrictModel):
    user_id: UUID
    plan_date: date
    generated_by: Literal["openai", "fallback"]
    model_used: str
    summary: str
    nutrition: NutritionPlan
    safety_notes: list[str] = Field(default_factory=lambda: [MEDICAL_DISCLAIMER], max_length=6)


class AdaptiveCheckinLogResponse(StrictModel):
    user_id: UUID
    saved: bool


class BiomarkerAnalysisRequest(StrictModel):
    metrics: AdaptiveMetricsInput | None = None


class BiomarkerAnalysisResponse(StrictModel):
    user_id: UUID
    generated_by: Literal["openai", "fallback"]
    model_used: str
    summary: str
    key_findings: list[str] = Field(min_length=1, max_length=5)
    watch_items: list[str] = Field(default_factory=list, max_length=5)
    next_actions: list[str] = Field(default_factory=list, max_length=5)
    safety_notes: list[str] = Field(default_factory=lambda: [MEDICAL_DISCLAIMER], max_length=4)
