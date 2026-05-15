import json
import random
import time
from datetime import UTC, date, datetime, timedelta
from email.utils import parsedate_to_datetime
from typing import Any
from uuid import UUID

import httpx
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import ExternalServiceError
from app.models.daily_checkin import DailyCheckin
from app.repositories import health_repository, user_repository, wearable_repository
from app.schemas.adaptive_plan import (
    AdaptiveCheckinRequest,
    AdaptiveMetricsInput,
    AdaptivePlanRequest,
    AdaptivePlanResponse,
    BiomarkerAnalysisRequest,
    BiomarkerAnalysisResponse,
    BiomarkerInput,
    NutritionPlanResponse,
    PlanFeedbackInput,
    RoutinePlanResponse,
)
from app.schemas.common import MEDICAL_DISCLAIMER
from app.services.twin_engine import calculate_bmi, target_weight_for_bmi


NEGATIVE_OPTIONS = [
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


def _openai_failure(operation: str, exc: Exception) -> ExternalServiceError:
    if isinstance(exc, httpx.HTTPStatusError):
        status_code = exc.response.status_code
        detail = exc.response.text[:1200]
        try:
            payload = exc.response.json()
            detail = payload.get("error", {}).get("message") or detail
        except ValueError:
            pass
        return ExternalServiceError(f"OpenAI {operation} call failed with HTTP {status_code}: {detail}")
    if isinstance(exc, httpx.TimeoutException):
        return ExternalServiceError(f"OpenAI {operation} call timed out. Try again or increase the service timeout.")
    if isinstance(exc, httpx.HTTPError):
        return ExternalServiceError(f"OpenAI {operation} call failed: {exc}")
    return ExternalServiceError(f"OpenAI {operation} response could not be used: {exc}")


def _retry_after_seconds(response: httpx.Response, fallback_seconds: float, max_seconds: float) -> float:
    retry_after = response.headers.get("retry-after")
    if retry_after:
        try:
            return min(float(retry_after), max_seconds)
        except ValueError:
            try:
                retry_at = parsedate_to_datetime(retry_after)
                if retry_at.tzinfo is None:
                    retry_at = retry_at.replace(tzinfo=UTC)
                return min(max(0.0, (retry_at - datetime.now(UTC)).total_seconds()), max_seconds)
            except (TypeError, ValueError):
                pass
    return min(fallback_seconds, max_seconds)


def _retry_delay(attempt: int) -> float:
    settings = get_settings()
    exponential = settings.openai_retry_base_seconds * (2**attempt)
    jitter = random.uniform(0, settings.openai_retry_base_seconds)
    return min(exponential + jitter, settings.openai_retry_max_seconds)


def _is_retryable_request_error(exc: httpx.RequestError) -> bool:
    return isinstance(
        exc,
        (
            httpx.TimeoutException,
            httpx.ConnectError,
            httpx.ReadError,
            httpx.WriteError,
            httpx.RemoteProtocolError,
            httpx.NetworkError,
        ),
    )


def _post_openai_response(body: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    retry_statuses = {408, 409, 425, 429, 500, 502, 503, 504}
    last_error: Exception | None = None

    with httpx.Client(timeout=settings.openai_timeout_seconds) as client:
        for attempt in range(settings.openai_max_retries):
            try:
                response = client.post(
                    "https://api.openai.com/v1/responses",
                    headers={
                        "Authorization": f"Bearer {settings.openai_api_key}",
                        "Content-Type": "application/json",
                    },
                    json=body,
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                last_error = exc
                if response.status_code not in retry_statuses or attempt == settings.openai_max_retries - 1:
                    raise
                time.sleep(_retry_after_seconds(response, _retry_delay(attempt), settings.openai_retry_max_seconds))
            except httpx.RequestError as exc:
                last_error = exc
                if not _is_retryable_request_error(exc) or attempt == settings.openai_max_retries - 1:
                    raise
                time.sleep(_retry_delay(attempt))

    if last_error:
        raise last_error
    raise RuntimeError("OpenAI request did not complete.")


StructuredOpenAIModel = (
    type[AdaptivePlanResponse] | type[RoutinePlanResponse] | type[NutritionPlanResponse] | type[BiomarkerAnalysisResponse]
)


def _validated_openai_model(
    *,
    body: dict[str, Any],
    response_model: StructuredOpenAIModel,
    user_id: UUID,
    plan_date: date | None = None,
) -> AdaptivePlanResponse | RoutinePlanResponse | NutritionPlanResponse | BiomarkerAnalysisResponse:
    settings = get_settings()
    last_error: Exception | None = None
    for attempt in range(settings.openai_validation_retries):
        try:
            raw_plan = json.loads(_output_text(_post_openai_response(body)))
            raw_plan["user_id"] = str(user_id)
            raw_plan["generated_by"] = "openai"
            raw_plan["model_used"] = settings.openai_model
            if plan_date is not None and "plan_date" in response_model.model_fields:
                raw_plan["plan_date"] = plan_date.isoformat()
            return response_model.model_validate(raw_plan)
        except (ValueError, ValidationError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt == settings.openai_validation_retries - 1:
                raise
            time.sleep(_retry_delay(attempt))
    if last_error:
        raise last_error
    raise RuntimeError("OpenAI structured response did not validate.")


def _clean_dict(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value is not None}


def _metrics_from_storage(db: Session, user_id: UUID, override: AdaptiveMetricsInput | None) -> AdaptiveMetricsInput:
    user = user_repository.ensure_user(db, user_id)
    latest_lab = health_repository.get_latest_lab_report(db, user_id)
    latest_wearable = wearable_repository.get_latest_reading(db, user_id)
    override_values = override.model_dump(exclude_unset=True) if override else {}
    override_biomarkers = override_values.pop("biomarkers", None) or {}

    stored_biomarkers = BiomarkerInput(
        hba1c=latest_lab.hba1c if latest_lab else None,
        fasting_glucose=latest_lab.fasting_glucose if latest_lab else None,
        bp_systolic=latest_lab.bp_systolic if latest_lab else None,
        bp_diastolic=latest_lab.bp_diastolic if latest_lab else None,
        ldl=latest_lab.ldl if latest_lab else None,
        hdl=latest_lab.hdl if latest_lab else None,
        triglycerides=latest_lab.triglycerides if latest_lab else None,
        vitamin_d=latest_lab.vitamin_d if latest_lab else None,
        vitamin_b12=latest_lab.vitamin_b12 if latest_lab else None,
        sgpt=latest_lab.sgpt if latest_lab else None,
        sgot=latest_lab.sgot if latest_lab else None,
        creatinine=latest_lab.creatinine if latest_lab else None,
        notes=latest_lab.notes if latest_lab else None,
    )
    merged_biomarkers = {
        **stored_biomarkers.model_dump(exclude_none=True),
        **{key: value for key, value in override_biomarkers.items() if value is not None},
    }

    stored = AdaptiveMetricsInput(
        age=user.age,
        weight_kg=user.weight_kg,
        height_cm=user.height_cm,
        stress_score=latest_wearable.stress_score if latest_wearable else None,
        heart_rate_bpm=(latest_wearable.resting_heart_rate or latest_wearable.heart_rate) if latest_wearable else None,
        sleep_hours=latest_wearable.sleep_hours if latest_wearable else None,
        steps=latest_wearable.steps if latest_wearable else None,
        workout_info=(
            f"Active minutes {latest_wearable.active_minutes}"
            if latest_wearable and latest_wearable.active_minutes is not None
            else None
        ),
        biomarkers=BiomarkerInput(**merged_biomarkers) if merged_biomarkers else None,
    )
    merged = {**stored.model_dump(exclude_none=True), **{key: value for key, value in override_values.items() if value is not None}}
    if merged_biomarkers:
        merged["biomarkers"] = BiomarkerInput(**merged_biomarkers)
    return AdaptiveMetricsInput(**merged)


def _completion_ratio(feedback: PlanFeedbackInput | None) -> float:
    if feedback is None:
        return 0.0
    total = len(feedback.completed_activity_ids) + len(feedback.skipped_activity_ids)
    return len(feedback.completed_activity_ids) / total if total else 0.0


def _timeline_increase_cap(feedback: PlanFeedbackInput | None) -> int | None:
    if feedback is None or feedback.previous_timeline_weeks is None:
        return None
    ratio = _completion_ratio(feedback)
    choices = set(feedback.negative_choices)
    high_risk_choices = {"smoking", "alcohol", "very_high_stress"}
    high_risk_poor_day = ratio < 0.4 and bool(choices.intersection(high_risk_choices))
    allowed_increase = 2 if high_risk_poor_day else 1 if choices or ratio < 0.85 else 0
    return feedback.previous_timeline_weeks + allowed_increase


def _timeline_weeks(metrics: AdaptiveMetricsInput, feedback: PlanFeedbackInput | None) -> int:
    weeks = 8
    if metrics.height_cm and metrics.weight_kg:
        bmi = calculate_bmi(metrics.height_cm, metrics.weight_kg)
        if bmi > 30:
            weeks += 24
        elif bmi > 25:
            weeks += 14
        elif bmi < 18.5:
            weeks += 16
    if metrics.sleep_hours is not None and metrics.sleep_hours < 6.5:
        weeks += 6
    if metrics.steps is not None and metrics.steps < 5000:
        weeks += 5
    if metrics.heart_rate_bpm is not None and metrics.heart_rate_bpm > 80:
        weeks += 6
    if metrics.biomarkers:
        bio = metrics.biomarkers
        if bio.hba1c is not None and bio.hba1c >= 5.7:
            weeks += 12
        if bio.bp_systolic is not None and bio.bp_systolic >= 130:
            weeks += 8
        if bio.vitamin_d is not None and bio.vitamin_d < 30:
            weeks += 8
        if bio.vitamin_b12 is not None and bio.vitamin_b12 < 350:
            weeks += 8
    ratio = _completion_ratio(feedback)
    if feedback:
        severe_choices = {"smoking", "alcohol", "very_high_stress", "missed_sleep_window"}
        severe_count = len(severe_choices.intersection(set(feedback.negative_choices)))
        if ratio >= 0.85 and not feedback.negative_choices:
            weeks = max(4, weeks - 1)
        elif ratio < 0.4 and severe_count >= 2:
            weeks += 2
        elif ratio < 0.5 or severe_count >= 1:
            weeks += 1
    weeks = max(4, min(104, weeks))
    cap = _timeline_increase_cap(feedback)
    return min(weeks, cap) if cap is not None else weeks


def _priority_activity(
    activity_id: str,
    time_window: str,
    title: str,
    category: str,
    target: str,
    why: str,
    priority: str,
    strict_rule: str,
    progression_note: str,
) -> dict[str, Any]:
    return {
        "id": activity_id,
        "time_window": time_window,
        "title": title,
        "category": category,
        "target": target,
        "why": why,
        "priority": priority,
        "strict_rule": strict_rule,
        "progression_note": progression_note,
    }


def _fallback_adaptive_plan(user_id: UUID, plan_date: date, metrics: AdaptiveMetricsInput, feedback: PlanFeedbackInput | None) -> AdaptivePlanResponse:
    bmi = calculate_bmi(metrics.height_cm or 170, metrics.weight_kg or 70)
    target_weight = target_weight_for_bmi(metrics.height_cm or 170)
    weeks = _timeline_weeks(metrics, feedback)
    high_stress = metrics.stress_score is not None and metrics.stress_score >= 70
    low_sleep = metrics.sleep_hours is not None and metrics.sleep_hours < 7
    low_steps = metrics.steps is None or metrics.steps < 7000
    completion = _completion_ratio(feedback)
    strictness = "recovery" if low_sleep or high_stress else "strict"
    if feedback and (completion < 0.6 or feedback.negative_choices):
        strictness = "progressive"

    activities = [
        _priority_activity(
            "wake-hydrate-sunlight",
            "06:30-07:30",
            "Hydrate, sunlight, and easy walk",
            "recovery",
            "500 ml water plus 10-15 min outdoor walk",
            "Anchors circadian rhythm and starts step accumulation without fatigue.",
            "high",
            "No phone scrolling before this is done.",
            "Add 5 minutes after three consistent days.",
        ),
        _priority_activity(
            "protein-breakfast",
            "07:30-09:00",
            "Protein-first breakfast",
            "nutrition",
            "25-35 g protein, high fiber, no sugary drink",
            "Improves satiety and glucose stability.",
            "high",
            "Breakfast must include a clear protein source.",
            "Increase protein by 5 g if hunger returns before lunch.",
        ),
        _priority_activity(
            "deep-work-breaks",
            "Work blocks",
            "Stress break after each work block",
            "stress",
            "3 minutes nasal breathing or a 5 minute walk every 2-3 hours",
            "Keeps stress from accumulating into evening cravings and poor sleep.",
            "medium",
            "Do not skip two breaks in a row.",
            "If stress is above 70, make the first two breaks non-negotiable.",
        ),
        _priority_activity(
            "lunch-plate",
            "12:30-14:00",
            "Controlled lunch plate",
            "nutrition",
            "Half vegetables, quarter protein, quarter carbs",
            "Supports weight, LDL, BP, and HbA1c direction without a rigid menu.",
            "high",
            "No fried side with lunch today.",
            "Keep carbs lower on non-workout days.",
        ),
        _priority_activity(
            "movement-dose",
            "17:30-19:00",
            "Workout or step catch-up",
            "movement",
            "30-45 min strength/zone-2 or reach today's step target",
            "Progressive movement is the main lever for heart rate, insulin sensitivity, and body composition.",
            "critical" if low_steps else "high",
            "Do the easy version if tired; skipping fully requires a reason in check-in.",
            "Raise target by 750-1000 steps only after two successful days.",
        ),
        _priority_activity(
            "early-dinner",
            "19:00-20:30",
            "Early balanced dinner",
            "nutrition",
            "Protein plus vegetables; light carbs if workout was done",
            "Avoids late heavy meals and improves sleep quality.",
            "high",
            "Finish dinner at least 2.5 hours before sleep.",
            "If dinner was late yesterday, keep today's dinner lighter.",
        ),
        _priority_activity(
            "sleep-lock",
            "22:00-23:00",
            "Sleep lock",
            "sleep",
            "Screens off 45 min before bed; target 7.5-8 hours",
            "Sleep is the recovery base for biomarkers, hunger, and workout adaptation.",
            "critical" if low_sleep else "high",
            "No caffeine after 2 PM and no heavy discussion/work in the last 30 minutes.",
            "Move bedtime 15 minutes earlier each day until sleep target is met.",
        ),
    ]

    supplement_guidance = []
    biomarkers = metrics.biomarkers
    if biomarkers and biomarkers.vitamin_d is not None:
        supplement_guidance.append(
            {
                "name": "Vitamin D3",
                "priority": "critical" if biomarkers.vitamin_d < 20 else "high",
                "why": f"Vitamin D is {biomarkers.vitamin_d:g} ng/mL; food and sunlight plan should support improvement.",
                "suggested_timing": "With a fat-containing meal",
                "safety_note": "Confirm dose with a clinician, especially if kidney disease, high calcium, or other medication exists.",
            }
        )
    if biomarkers and biomarkers.vitamin_b12 is not None:
        supplement_guidance.append(
            {
                "name": "Vitamin B12",
                "priority": "high" if biomarkers.vitamin_b12 < 350 else "optional",
                "why": f"B12 is {biomarkers.vitamin_b12:g} pg/mL; low-normal values can justify food focus and clinician-guided supplementation.",
                "suggested_timing": "Morning or lunch",
                "safety_note": "Use lab-guided dosing and recheck levels instead of taking indefinite high doses.",
            }
        )
    if biomarkers and biomarkers.triglycerides is not None and biomarkers.triglycerides >= 150:
        supplement_guidance.append(
            {
                "name": "Omega-3",
                "priority": "medium",
                "why": "Triglycerides are above ideal, so fatty fish or clinician-approved omega-3 may help.",
                "suggested_timing": "With lunch or dinner",
                "safety_note": "Ask a clinician first if using blood thinners or before surgery.",
            }
        )
    supplement_guidance.append(
        {
            "name": "Magnesium glycinate",
            "priority": "optional",
            "why": "May support sleep routine when diet is low in magnesium-rich foods.",
            "suggested_timing": "Evening",
            "safety_note": "Avoid without medical advice in kidney disease.",
        }
    )

    plan = {
        "user_id": user_id,
        "plan_date": plan_date,
        "generated_by": "fallback",
        "model_used": "deterministic-rule-engine",
        "strictness": strictness,
        "summary": f"Today's plan is strict on sleep, protein, movement, and avoiding relapse triggers. Current BMI estimate is {bmi}; target weight trend is around {target_weight} kg if appropriate for you.",
        "ideal_state": {
            "bmi_range": "22-24.9 unless your clinician sets a different target",
            "sleep_hours": "7.5-8.5 hours with consistent timing",
            "steps": "8000-10000 daily, built progressively",
            "resting_heart_rate_bpm": "60-70 bpm if realistic for your fitness level",
            "blood_pressure": "Around 120/80 mmHg or clinician-defined target",
            "metabolic_markers": "HbA1c near 5.0-5.4, triglycerides <150, LDL direction personalized by risk",
            "nutrition_pattern": "High protein, high fiber, mostly whole foods, minimal sugar/fried foods",
        },
        "timeline": {
            "estimated_weeks": weeks,
            "confidence": "medium" if metrics.sleep_hours or metrics.steps or metrics.biomarkers else "low",
            "summary": f"With 80 percent checklist adherence, expect meaningful movement toward ideal state in about {weeks} weeks.",
            "next_review_date": plan_date + timedelta(days=7),
            "assumptions": [
                "Plan is based on wellness inputs, not diagnosis.",
                "Timeline changes daily based on completion, sleep, steps, stress, and negative choices.",
                "Supplements require clinician confirmation when biomarkers are abnormal.",
            ],
        },
        "activities": activities,
        "negative_options": NEGATIVE_OPTIONS,
        "checkin_prompt": "Tick what you completed, mark what you skipped, select any negative choices, and add context so tomorrow can be stricter or lighter.",
        "nutrition": {
            "macro_distribution": {
                "protein_percent": 30,
                "carbs_percent": 40 if low_steps else 45,
                "fats_percent": 30 if low_steps else 25,
                "fiber_grams": 30,
                "water_liters": 2.7,
            },
            "meals": [
                {
                    "meal": "breakfast",
                    "composition": "Protein 30%, carbs 40%, fats 30%; keep sugar low.",
                    "north_indian_veg": ["Moong dal chilla with curd", "Paneer bhurji with roti"],
                    "north_indian_non_veg": ["Egg bhurji with roti", "Chicken keema with roti"],
                    "south_indian_veg": ["Idli with sambar plus curd", "Pesarattu with chutney"],
                    "south_indian_non_veg": ["Egg dosa with sambar", "Fish curry with small dosa portion"],
                    "note": "Pick one option; keep the composition stable rather than chasing exact dishes.",
                },
                {
                    "meal": "lunch",
                    "composition": "Half vegetables, quarter protein, quarter rice/roti/millet; add dal or curd.",
                    "north_indian_veg": ["Rajma or chole bowl with salad", "Dal, roti, sabzi, curd"],
                    "north_indian_non_veg": ["Grilled chicken tikka bowl", "Egg curry with roti and salad"],
                    "south_indian_veg": ["Sambar rice with extra dal and poriyal", "Curd rice small portion plus sprouts"],
                    "south_indian_non_veg": ["Fish curry with red rice and poriyal", "Chicken curry with millet and vegetables"],
                    "note": "Avoid fried sides and sweet drinks.",
                },
                {
                    "meal": "snack",
                    "composition": "Protein or fiber-led; avoid sugar rebound.",
                    "north_indian_veg": ["Roasted chana", "Curd with nuts"],
                    "north_indian_non_veg": ["Boiled eggs", "Chicken soup"],
                    "south_indian_veg": ["Sundal", "Buttermilk with peanuts"],
                    "south_indian_non_veg": ["Boiled eggs", "Pepper chicken soup"],
                    "note": "Use snack only if hungry or pre-workout.",
                },
                {
                    "meal": "dinner",
                    "composition": "Protein and vegetables first; lighter carbs if steps/workout were low.",
                    "north_indian_veg": ["Paneer/tofu tikka with sabzi", "Dal soup with salad"],
                    "north_indian_non_veg": ["Chicken curry with vegetables", "Egg curry with salad"],
                    "south_indian_veg": ["Vegetable kootu with curd", "Adai with sambar"],
                    "south_indian_non_veg": ["Fish fry grilled style with rasam", "Chicken stew with vegetables"],
                    "note": "Finish early and keep the meal boring if sleep has been poor.",
                },
            ],
            "supplement_guidance": supplement_guidance,
        },
        "safety_notes": [
            MEDICAL_DISCLAIMER,
            "Do not start intense exercise if you have chest pain, dizziness, fever, or acute injury.",
            "Do not self-prescribe high-dose vitamins from lab values alone.",
        ],
    }
    return AdaptivePlanResponse.model_validate(plan)


def _system_prompt() -> str:
    return (
        "You are LifeTwin's preventive wellness planner. Create a strict but safe daily plan that helps the user move "
        "toward an ideal healthy state using progressive behavior change. The output must be practical, checklist-ready, "
        "and culturally appropriate for Indian users. Include North Indian and South Indian vegetarian and non-vegetarian "
        "meal suggestions, but make the diet composition-led, not dish-locked. Use biomarkers only for wellness guidance; "
        "do not diagnose, treat, or prescribe. Supplement guidance must be cautious, biomarker-based, and include a clinician "
        "safety note. If data is missing, say the timeline confidence is low and make conservative assumptions. Always include "
        f"this safety principle: {MEDICAL_DISCLAIMER}"
    )


def _routine_system_prompt() -> str:
    return (
        "You are LifeTwin's routine planner. Create only the daily checklist and progress timeline. "
        "Keep user-facing task text simple, strict, and direct: what to do, target, and any rule. "
        "Avoid long explanations, options, and food dish suggestions. Maintain high wellness quality, "
        "but do not diagnose or prescribe. Include a concise 1-2 sentence summary and concise timeline summary. "
        f"Safety principle: {MEDICAL_DISCLAIMER}"
    )


def _nutrition_system_prompt() -> str:
    return (
        "You are LifeTwin's nutrition planner. Create only the nutrition plan. Keep vitamin and supplement guidance "
        "short, biomarker-based, cautious, and non-prescriptive. Diet must be composition-led with macro percentages, "
        "fiber, water, and flexible North Indian/South Indian veg and non-veg dish suggestions. Do not create a rigid menu. "
        f"Safety principle: {MEDICAL_DISCLAIMER}"
    )


def _biomarker_system_prompt() -> str:
    return (
        "You are LifeTwin's biomarker analyst. Explain the user's current biomarker situation only. "
        "Do not mention projected age, biological age, twin matching, longevity score, or future twin. "
        "Keep it concise, practical, non-diagnostic, and focused on what appears in the provided values. "
        "If data is limited, say so. Suggest only wellness next steps and clinician follow-up where appropriate. "
        f"Safety principle: {MEDICAL_DISCLAIMER}"
    )


def _output_text(response: dict[str, Any]) -> str:
    if isinstance(response.get("output_text"), str):
        return response["output_text"]
    for item in response.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if isinstance(content.get("text"), str):
                return content["text"]
    raise ValueError("OpenAI response did not contain text output.")


def _openai_response_schema(
    response_model: type[AdaptivePlanResponse]
    | type[RoutinePlanResponse]
    | type[NutritionPlanResponse]
    | type[BiomarkerAnalysisResponse],
) -> dict[str, Any]:
    schema = response_model.model_json_schema()

    def normalize(node: Any) -> None:
        if not isinstance(node, dict):
            return
        node.pop("default", None)
        if node.get("type") == "object" and isinstance(node.get("properties"), dict):
            node["required"] = list(node["properties"].keys())
            node["additionalProperties"] = False
        for key in ("properties", "$defs"):
            for child in node.get(key, {}).values():
                normalize(child)
        for key in ("anyOf", "oneOf", "allOf"):
            for child in node.get(key, []):
                normalize(child)
        if isinstance(node.get("items"), dict):
            normalize(node["items"])

    normalize(schema)
    return schema


def _openai_plan(user_id: UUID, plan_date: date, metrics: AdaptiveMetricsInput, feedback: PlanFeedbackInput | None) -> AdaptivePlanResponse:
    settings = get_settings()
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")

    schema = _openai_response_schema(AdaptivePlanResponse)
    request_payload = {
        "user_id": str(user_id),
        "plan_date": plan_date.isoformat(),
        "metrics": metrics.model_dump(mode="json", exclude_none=True),
        "previous_day_feedback": feedback.model_dump(mode="json", exclude_none=True) if feedback else None,
        "negative_options": NEGATIVE_OPTIONS,
        "requirements": [
            "Return 7-10 checklist activities with strict rules and progression notes.",
            "Estimate timeline to ideal state and adjust it based on feedback adherence.",
            "Diet must show macro percentages and flexible dish suggestions.",
            "Vitamins/supplements must be based on biomarkers when present and never framed as prescriptions.",
        ],
    }
    body = {
        "model": settings.openai_model,
        "instructions": _system_prompt(),
        "input": [
            {
                "role": "user",
                "content": [{"type": "input_text", "text": json.dumps(request_payload, default=str)}],
            }
        ],
        "reasoning": {"effort": "medium"},
        "text": {
            "format": {
                "type": "json_schema",
                "name": "lifetwin_adaptive_plan",
                "schema": schema,
            }
        },
        "max_output_tokens": 7000,
    }
    response = _validated_openai_model(body=body, response_model=AdaptivePlanResponse, user_id=user_id, plan_date=plan_date)
    return response if isinstance(response, AdaptivePlanResponse) else AdaptivePlanResponse.model_validate(response)


def _openai_structured_response(
    *,
    user_id: UUID,
    plan_date: date,
    metrics: AdaptiveMetricsInput,
    feedback: PlanFeedbackInput | None,
    response_model: type[RoutinePlanResponse] | type[NutritionPlanResponse] | type[BiomarkerAnalysisResponse],
    schema_name: str,
    instructions: str,
    requirements: list[str],
    max_output_tokens: int,
) -> RoutinePlanResponse | NutritionPlanResponse | BiomarkerAnalysisResponse:
    settings = get_settings()
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")

    request_payload = {
        "user_id": str(user_id),
        "plan_date": plan_date.isoformat(),
        "metrics": metrics.model_dump(mode="json", exclude_none=True),
        "previous_day_feedback": feedback.model_dump(mode="json", exclude_none=True) if feedback else None,
        "negative_options": NEGATIVE_OPTIONS,
        "requirements": requirements,
    }
    body = {
        "model": settings.openai_model,
        "instructions": instructions,
        "input": [
            {
                "role": "user",
                "content": [{"type": "input_text", "text": json.dumps(request_payload, default=str)}],
            }
        ],
        "reasoning": {"effort": "medium"},
        "text": {
            "format": {
                "type": "json_schema",
                "name": schema_name,
                "schema": _openai_response_schema(response_model),
            }
        },
        "max_output_tokens": max_output_tokens,
    }
    response = _validated_openai_model(body=body, response_model=response_model, user_id=user_id, plan_date=plan_date)
    return response_model.model_validate(response)


def _fallback_biomarker_analysis(user_id: UUID, metrics: AdaptiveMetricsInput) -> BiomarkerAnalysisResponse:
    biomarkers = metrics.biomarkers or BiomarkerInput()
    key_findings: list[str] = []
    watch_items: list[str] = []
    next_actions: list[str] = []

    if biomarkers.hba1c is not None:
        key_findings.append(
            f"HbA1c is {biomarkers.hba1c:g}%, which is useful for understanding current glucose control."
        )
        if biomarkers.hba1c >= 5.7:
            watch_items.append("HbA1c is above the usual normal range; discuss repeat testing and risk context with a clinician.")
            next_actions.append("Prioritize protein, fiber, walking after meals, and lower-sugar choices this week.")
    if biomarkers.bp_systolic is not None and biomarkers.bp_diastolic is not None:
        key_findings.append(f"Blood pressure is {biomarkers.bp_systolic}/{biomarkers.bp_diastolic} mmHg.")
        if biomarkers.bp_systolic >= 130 or biomarkers.bp_diastolic >= 85:
            watch_items.append("Blood pressure is worth monitoring with repeated rested readings.")
            next_actions.append("Reduce salty/fried meals, improve sleep, and keep daily walking consistent.")
    if biomarkers.vitamin_d is not None:
        key_findings.append(f"Vitamin D is {biomarkers.vitamin_d:g} ng/mL.")
        if biomarkers.vitamin_d < 30:
            watch_items.append("Vitamin D appears low or insufficient.")
            next_actions.append("Use sunlight, vitamin-D foods, and clinician-guided supplementation if needed.")
    if biomarkers.vitamin_b12 is not None:
        key_findings.append(f"Vitamin B12 is {biomarkers.vitamin_b12:g} pg/mL.")
        if biomarkers.vitamin_b12 < 350:
            watch_items.append("B12 is low-normal or low depending on the lab range.")
            next_actions.append("Add B12-rich foods and discuss supplementation/recheck timing with a clinician.")

    if not key_findings:
        key_findings.append("Only limited biomarker data is available right now.")
        next_actions.append("Add recent lab values to get a more useful interpretation.")

    return BiomarkerAnalysisResponse(
        user_id=user_id,
        generated_by="fallback",
        model_used="deterministic-rule-engine",
        summary="Current biomarker review based on the values available. This is wellness guidance, not a diagnosis.",
        key_findings=key_findings[:5],
        watch_items=watch_items[:5],
        next_actions=next_actions[:5],
        safety_notes=[MEDICAL_DISCLAIMER],
    )


def generate_adaptive_plan(db: Session, user_id: UUID, payload: AdaptivePlanRequest) -> AdaptivePlanResponse:
    plan_date = payload.plan_date or date.today()
    metrics = _metrics_from_storage(db, user_id, payload.metrics)
    feedback = payload.previous_day
    try:
        return _openai_plan(user_id, plan_date, metrics, feedback)
    except (httpx.HTTPError, RuntimeError, ValueError, ValidationError, json.JSONDecodeError) as exc:
        raise _openai_failure("adaptive plan", exc) from exc


def _routine_from_plan(plan: AdaptivePlanResponse) -> RoutinePlanResponse:
    return RoutinePlanResponse.model_validate(
        {
            "user_id": plan.user_id,
            "plan_date": plan.plan_date,
            "generated_by": plan.generated_by,
            "model_used": plan.model_used,
            "strictness": plan.strictness,
            "summary": plan.summary,
            "timeline": plan.timeline,
            "activities": plan.activities,
            "negative_options": plan.negative_options,
            "checkin_prompt": plan.checkin_prompt,
            "safety_notes": plan.safety_notes,
        }
    )


def _bounded_routine_timeline(
    response: RoutinePlanResponse,
    metrics: AdaptiveMetricsInput,
    feedback: PlanFeedbackInput | None,
) -> RoutinePlanResponse:
    bounded = _timeline_weeks(metrics, feedback)
    if response.timeline.estimated_weeks <= bounded:
        return response
    values = response.model_dump()
    values["timeline"]["estimated_weeks"] = bounded
    values["timeline"]["summary"] = (
        f"Realistic estimate: about {bounded} weeks with steady adherence. "
        "One day can adjust the plan, but not drastically change the journey."
    )
    return RoutinePlanResponse.model_validate(values)


def _nutrition_from_plan(plan: AdaptivePlanResponse) -> NutritionPlanResponse:
    return NutritionPlanResponse.model_validate(
        {
            "user_id": plan.user_id,
            "plan_date": plan.plan_date,
            "generated_by": plan.generated_by,
            "model_used": plan.model_used,
            "summary": "Composition-led diet for today, adjusted to available biomarkers and activity.",
            "nutrition": plan.nutrition,
            "safety_notes": plan.safety_notes,
        }
    )


def generate_routine_plan(db: Session, user_id: UUID, payload: AdaptivePlanRequest) -> RoutinePlanResponse:
    plan_date = payload.plan_date or date.today()
    metrics = _metrics_from_storage(db, user_id, payload.metrics)
    feedback = payload.previous_day
    try:
        response = _openai_structured_response(
            user_id=user_id,
            plan_date=plan_date,
            metrics=metrics,
            feedback=feedback,
            response_model=RoutinePlanResponse,
            schema_name="lifetwin_routine_plan",
            instructions=_routine_system_prompt(),
            requirements=[
                "Return 7-10 activities.",
                "Each activity title must be short and action-oriented.",
                "Each target must be concrete and measurable.",
                "why and progression_note must be one short sentence each.",
                "strict_rule must be short and practical.",
                "Summary and timeline summary must be 1-2 short sentences.",
                "Timeline changes must be realistic: never increase by more than 1 week for a normal imperfect day or 2 weeks for a very poor day.",
                "If missed_workout and missed_sleep_window are the only negative choices, timeline can increase by at most 1 week total.",
            ],
            max_output_tokens=4500,
        )
        routine = response if isinstance(response, RoutinePlanResponse) else RoutinePlanResponse.model_validate(response)
        return _bounded_routine_timeline(routine, metrics, feedback)
    except (httpx.HTTPError, RuntimeError, ValueError, ValidationError, json.JSONDecodeError) as exc:
        raise _openai_failure("routine plan", exc) from exc


def generate_nutrition_plan(db: Session, user_id: UUID, payload: AdaptivePlanRequest) -> NutritionPlanResponse:
    plan_date = payload.plan_date or date.today()
    metrics = _metrics_from_storage(db, user_id, payload.metrics)
    feedback = payload.previous_day
    try:
        response = _openai_structured_response(
            user_id=user_id,
            plan_date=plan_date,
            metrics=metrics,
            feedback=feedback,
            response_model=NutritionPlanResponse,
            schema_name="lifetwin_nutrition_plan",
            instructions=_nutrition_system_prompt(),
            requirements=[
                "Return macro distribution, meal compositions, and Indian dish suggestions.",
                "Keep supplement why and safety_note short.",
                "Use biomarkers when present, but do not prescribe doses.",
                "Keep dish suggestions flexible and composition-led.",
            ],
            max_output_tokens=4500,
        )
        return response if isinstance(response, NutritionPlanResponse) else NutritionPlanResponse.model_validate(response)
    except (httpx.HTTPError, RuntimeError, ValueError, ValidationError, json.JSONDecodeError) as exc:
        raise _openai_failure("nutrition plan", exc) from exc


def analyze_biomarkers(db: Session, user_id: UUID, payload: BiomarkerAnalysisRequest) -> BiomarkerAnalysisResponse:
    metrics = _metrics_from_storage(db, user_id, payload.metrics)
    try:
        response = _openai_structured_response(
            user_id=user_id,
            plan_date=date.today(),
            metrics=metrics,
            feedback=None,
            response_model=BiomarkerAnalysisResponse,
            schema_name="lifetwin_biomarker_analysis",
            instructions=_biomarker_system_prompt(),
            requirements=[
                "Explain only current biomarker situation.",
                "Do not mention projected age, biological age, twin, twin match, alignment, or timeline.",
                "Keep summary under 2 sentences.",
                "Each finding/action should be simple and user-readable.",
                "Use clinician follow-up language for abnormal or uncertain values.",
            ],
            max_output_tokens=2500,
        )
        return response if isinstance(response, BiomarkerAnalysisResponse) else BiomarkerAnalysisResponse.model_validate(response)
    except (httpx.HTTPError, RuntimeError, ValueError, ValidationError, json.JSONDecodeError) as exc:
        raise _openai_failure("biomarker analysis", exc) from exc


def save_adaptive_checkin_feedback(db: Session, user_id: UUID, payload: AdaptiveCheckinRequest) -> None:
    user_repository.ensure_user(db, user_id)
    metrics = _metrics_from_storage(db, user_id, payload.metrics)
    feedback = payload.feedback
    checkin = DailyCheckin(
        user_id=user_id,
        checkin_date=payload.plan_date or date.today(),
        sleep_quality="met" if metrics.sleep_hours and metrics.sleep_hours >= 7 else "needs_attention",
        exercise_done=f"{len(feedback.completed_activity_ids)} completed, {len(feedback.skipped_activity_ids)} skipped",
        food_quality="needs_attention"
        if any(choice in feedback.negative_choices for choice in ["high_sugar", "fried_food", "late_heavy_meal"])
        else "planned",
        alcohol_used="alcohol" in feedback.negative_choices,
        smoking_done="smoking" in feedback.negative_choices,
        stress_level=str(metrics.stress_score) if metrics.stress_score is not None else None,
        steps_completed=metrics.steps,
        sleep_hours=metrics.sleep_hours,
        user_notes=json.dumps(
            {
                "completed_activity_ids": feedback.completed_activity_ids,
                "skipped_activity_ids": feedback.skipped_activity_ids,
                "negative_choices": feedback.negative_choices,
                "previous_timeline_weeks": feedback.previous_timeline_weeks,
                "notes": feedback.notes,
            }
        ),
    )
    db.add(checkin)
    db.commit()


def submit_checkin_and_generate_next_plan(db: Session, user_id: UUID, payload: AdaptiveCheckinRequest) -> AdaptivePlanResponse:
    save_adaptive_checkin_feedback(db, user_id, payload)
    metrics = _metrics_from_storage(db, user_id, payload.metrics)
    feedback = payload.feedback
    return generate_adaptive_plan(
        db,
        user_id,
        AdaptivePlanRequest(
            plan_date=(payload.plan_date or date.today()) + timedelta(days=1),
            metrics=metrics,
            previous_day=feedback,
        ),
    )
