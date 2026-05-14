from math import isfinite
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.lab_report import LabReport
from app.models.lifestyle import LifestyleProfile
from app.models.twin import TwinGoal
from app.models.user import User
from app.models.wearable import WearableReading
from app.repositories import health_repository, twin_repository, wearable_repository
from app.schemas.twin import TwinGoalCreate


def calculate_bmi(height_cm: float, weight_kg: float) -> float:
    height_m = height_cm / 100
    if height_m <= 0:
        return 0
    return round(weight_kg / (height_m * height_m), 1)


def target_weight_for_bmi(height_cm: float, target_bmi: float = 24) -> float:
    height_m = height_cm / 100
    return round(target_bmi * height_m * height_m, 1)


def build_current_twin(
    user: User,
    lifestyle: LifestyleProfile | None,
    latest_reading: WearableReading | None,
    latest_lab: LabReport | None,
) -> dict:
    return {
        "profile": {
            "age": user.age,
            "height_cm": user.height_cm,
            "weight_kg": user.weight_kg,
            "bmi": calculate_bmi(user.height_cm, user.weight_kg),
            "target_age": user.target_age,
        },
        "lifestyle": {
            "smoking_status": lifestyle.smoking_status if lifestyle else None,
            "alcohol_frequency": lifestyle.alcohol_frequency if lifestyle else None,
            "exercise_frequency": lifestyle.exercise_frequency if lifestyle else None,
            "diet_quality": lifestyle.diet_quality if lifestyle else None,
            "stress_level": lifestyle.stress_level if lifestyle else None,
            "sleep_goal_hours": lifestyle.sleep_goal_hours if lifestyle else None,
        },
        "latest_wearable": {
            "timestamp": latest_reading.timestamp if latest_reading else None,
            "resting_heart_rate": latest_reading.resting_heart_rate if latest_reading else None,
            "heart_rate": latest_reading.heart_rate if latest_reading else None,
            "spo2": latest_reading.spo2 if latest_reading else None,
            "steps": latest_reading.steps if latest_reading else None,
            "active_minutes": latest_reading.active_minutes if latest_reading else None,
            "sleep_hours": latest_reading.sleep_hours if latest_reading else None,
            "stress_score": latest_reading.stress_score if latest_reading else None,
        },
        "latest_labs": {
            "report_date": latest_lab.report_date if latest_lab else None,
            "bp_systolic": latest_lab.bp_systolic if latest_lab else None,
            "bp_diastolic": latest_lab.bp_diastolic if latest_lab else None,
            "ldl": latest_lab.ldl if latest_lab else None,
            "hba1c": latest_lab.hba1c if latest_lab else None,
            "fasting_glucose": latest_lab.fasting_glucose if latest_lab else None,
            "triglycerides": latest_lab.triglycerides if latest_lab else None,
        },
    }


def default_goal_for_user(user: User) -> TwinGoalCreate:
    return TwinGoalCreate(
        target_age=user.target_age or max(user.age + 25, 80),
        target_weight_kg=target_weight_for_bmi(user.height_cm),
        target_sleep_hours=7.5,
        target_steps=8000,
        target_resting_hr=68,
        target_bp_systolic=120,
        target_bp_diastolic=80,
        target_ldl=95,
        goal_description=(
            "Healthspan alignment target focused on sustainable weight, restorative sleep, "
            "regular activity, cardiometabolic markers, and lower-risk lifestyle patterns."
        ),
    )


def ideal_twin_from_goal(goal: TwinGoal | TwinGoalCreate) -> dict:
    return {
        "target_age": goal.target_age,
        "target_weight_kg": goal.target_weight_kg,
        "target_bmi_range": "22-25",
        "target_sleep_hours": goal.target_sleep_hours,
        "target_steps": goal.target_steps,
        "target_resting_hr": goal.target_resting_hr,
        "target_bp": {
            "systolic": goal.target_bp_systolic,
            "diastolic": goal.target_bp_diastolic,
        },
        "target_ldl": goal.target_ldl,
        "lifestyle_targets": {
            "smoking": "none",
            "alcohol": "controlled or minimal",
            "activity": "regular zone-2 and strength-supporting movement",
            "nutrition": "high-fiber, high-protein, minimally processed meals",
        },
        "goal_description": goal.goal_description,
    }


def _metric_gap(current: float | int | None, target: float | int | None, direction: str) -> dict:
    if current is None or target is None:
        return {"current": current, "target": target, "status": "insufficient_data", "gap": None}
    gap = round(float(current) - float(target), 2)
    aligned = current <= target if direction == "lower" else current >= target
    return {
        "current": current,
        "target": target,
        "status": "aligned" if aligned else "needs_attention",
        "gap": gap,
    }


def calculate_twin_gap(current_twin: dict, ideal_twin: dict) -> dict:
    profile = current_twin["profile"]
    wearable = current_twin["latest_wearable"]
    labs = current_twin["latest_labs"]
    return {
        "weight": _metric_gap(profile["weight_kg"], ideal_twin["target_weight_kg"], "lower"),
        "sleep": _metric_gap(wearable["sleep_hours"], ideal_twin["target_sleep_hours"], "higher"),
        "steps": _metric_gap(wearable["steps"], ideal_twin["target_steps"], "higher"),
        "resting_heart_rate": _metric_gap(
            wearable["resting_heart_rate"], ideal_twin["target_resting_hr"], "lower"
        ),
        "bp_systolic": _metric_gap(
            labs["bp_systolic"], ideal_twin["target_bp"]["systolic"], "lower"
        ),
        "bp_diastolic": _metric_gap(
            labs["bp_diastolic"], ideal_twin["target_bp"]["diastolic"], "lower"
        ),
        "ldl": _metric_gap(labs["ldl"], ideal_twin["target_ldl"], "lower"),
    }


def calculate_alignment_score(gap: dict) -> float:
    penalties = 0.0
    weights = {
        "weight": 12,
        "sleep": 16,
        "steps": 16,
        "resting_heart_rate": 16,
        "bp_systolic": 12,
        "bp_diastolic": 10,
        "ldl": 18,
    }
    for key, weight in weights.items():
        item = gap.get(key, {})
        if item.get("status") != "needs_attention" or item.get("gap") is None:
            continue
        current = item["current"]
        target = item["target"]
        if not isinstance(current, (int, float)) or not isinstance(target, (int, float)):
            continue
        relative_gap = abs(float(current) - float(target)) / max(abs(float(target)), 1)
        if isfinite(relative_gap):
            penalties += min(weight, relative_gap * weight * 2)
    return round(max(0, min(100, 100 - penalties)), 1)


def get_twin_snapshot(db: Session, user: User, persist_goal: bool = False) -> dict:
    lifestyle = health_repository.get_lifestyle(db, user.id)
    latest_reading = wearable_repository.get_latest_reading(db, user.id)
    latest_lab = health_repository.get_latest_lab_report(db, user.id)
    goal = twin_repository.get_latest_twin_goal(db, user.id)
    if goal is None:
        default_goal = default_goal_for_user(user)
        goal_obj: TwinGoal | TwinGoalCreate
        goal_obj = twin_repository.create_twin_goal(db, user.id, default_goal) if persist_goal else default_goal
    else:
        goal_obj = goal
    current_twin = build_current_twin(user, lifestyle, latest_reading, latest_lab)
    ideal_twin = ideal_twin_from_goal(goal_obj)
    twin_gap = calculate_twin_gap(current_twin, ideal_twin)
    return {
        "user_id": user.id,
        "current_twin": current_twin,
        "ideal_twin": ideal_twin,
        "twin_gap": twin_gap,
        "twin_alignment_score": calculate_alignment_score(twin_gap),
    }


def generate_twin_goal(db: Session, user: User) -> TwinGoal:
    return twin_repository.create_twin_goal(db, user.id, default_goal_for_user(user))


def snapshot_for_user_id(db: Session, user_id: UUID) -> dict:
    from app.repositories.user_repository import ensure_user

    user = ensure_user(db, user_id)
    return get_twin_snapshot(db, user)
