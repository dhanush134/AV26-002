from uuid import UUID

from sqlalchemy.orm import Session

from app.core.database import utc_now
from app.models.lab_report import LabReport
from app.models.lifestyle import LifestyleProfile
from app.models.user import User
from app.models.wearable import WearableReading
from app.repositories import health_repository, risk_repository, user_repository, wearable_repository
from app.services.twin_engine import calculate_bmi, get_twin_snapshot


def clamp(value: float) -> float:
    return round(max(0, min(100, value)), 1)


def risk_level(score: float) -> str:
    if score <= 30:
        return "low"
    if score <= 60:
        return "moderate"
    if score <= 80:
        return "high"
    return "critical"


def add_factor(
    factors: list[dict],
    category: str,
    factor: str,
    severity: str,
    reason: str,
    suggested_action: str,
) -> None:
    factors.append(
        {
            "category": category,
            "factor": factor,
            "severity": severity,
            "reason": reason,
            "suggested_action": suggested_action,
        }
    )


def calculate_scores(
    user: User,
    lifestyle: LifestyleProfile | None,
    latest_reading: WearableReading | None,
    latest_lab: LabReport | None,
    twin_alignment_score: float,
) -> dict:
    cardio = metabolic = sleep = activity = lifestyle_score = anomaly = 10.0
    factors: list[dict] = []
    bmi = calculate_bmi(user.height_cm, user.weight_kg)

    if bmi > 30:
        metabolic += 25
        lifestyle_score += 15
        add_factor(
            factors,
            "metabolic",
            "BMI above preferred healthspan range",
            "warning",
            "BMI is above 30, which can align with a higher preventive metabolic risk pattern.",
            "Prioritize gradual weight reduction through daily movement, protein-forward meals, and sleep consistency.",
        )

    if latest_reading:
        if latest_reading.sleep_hours is not None and latest_reading.sleep_hours < 6:
            sleep += 30
            lifestyle_score += 10
            add_factor(
                factors,
                "sleep",
                "Short sleep duration",
                "warning",
                "Recent sleep is below 6 hours, which may affect recovery and metabolic regulation.",
                "Set a consistent wind-down time and protect a 7-8 hour sleep opportunity.",
            )
        if latest_reading.steps is not None and latest_reading.steps < 4000:
            activity += 30
            lifestyle_score += 10
            add_factor(
                factors,
                "activity",
                "Low step count",
                "warning",
                "Recent activity is below 4000 steps.",
                "Add two short walks and aim for a steady 6000-8000 step progression.",
            )
        if latest_reading.resting_heart_rate is not None and latest_reading.resting_heart_rate > 85:
            cardio += 25
            add_factor(
                factors,
                "cardio",
                "Elevated resting heart rate",
                "warning",
                "Resting HR is above preferred range.",
                "Improve sleep, hydration, and low-intensity activity; consult a professional if persistent.",
            )
        if (
            latest_reading.heart_rate is not None
            and latest_reading.heart_rate > 110
            and (latest_reading.active_minutes or 0) == 0
        ):
            anomaly += 35
            cardio += 10
            add_factor(
                factors,
                "anomaly",
                "Higher heart rate while inactive",
                "warning",
                "Heart rate appears elevated without recorded active minutes.",
                "Rest, hydrate, recheck the reading, and consult a medical professional if symptoms occur.",
            )
        if latest_reading.spo2 is not None and latest_reading.spo2 < 94:
            anomaly += 40
            add_factor(
                factors,
                "respiratory",
                "Lower oxygen saturation pattern",
                "critical" if latest_reading.spo2 < 90 else "warning",
                "SpO2 is below a preferred wellness range.",
                "Recheck with a reliable device and consult a qualified healthcare professional if persistent.",
            )

    if latest_lab:
        if (
            latest_lab.bp_systolic is not None
            and latest_lab.bp_systolic >= 130
            or latest_lab.bp_diastolic is not None
            and latest_lab.bp_diastolic >= 80
        ):
            cardio += 25
            add_factor(
                factors,
                "cardio",
                "Elevated blood pressure pattern",
                "warning",
                "Latest blood pressure values are above preferred preventive targets.",
                "Track readings, reduce sodium-heavy meals, walk daily, and consult a medical professional.",
            )
        if latest_lab.ldl is not None and latest_lab.ldl >= 130:
            cardio += 20
            metabolic += 10
            add_factor(
                factors,
                "cardio",
                "Elevated LDL pattern",
                "warning",
                "LDL is above preferred preventive range.",
                "Increase soluble fiber, reduce fried foods, and review results with a clinician.",
            )
        if latest_lab.hba1c is not None and latest_lab.hba1c >= 5.7:
            metabolic += 25
            add_factor(
                factors,
                "metabolic",
                "Elevated glucose regulation pattern",
                "warning",
                "HbA1c is above preferred preventive range.",
                "Prioritize post-meal walks, consistent sleep, and professional lab review.",
            )

    if lifestyle:
        smoking = (lifestyle.smoking_status or "").lower()
        alcohol = (lifestyle.alcohol_frequency or "").lower()
        exercise = (lifestyle.exercise_frequency or "").lower()
        if smoking and smoking not in {"none", "never", "no"}:
            cardio += 25
            lifestyle_score += 30
            add_factor(
                factors,
                "lifestyle",
                "Smoking exposure",
                "warning",
                "Smoking status increases preventive cardio and lifestyle risk pattern.",
                "Use a structured cessation plan and seek professional support.",
            )
        if any(token in alcohol for token in ["frequent", "daily", "high"]):
            lifestyle_score += 20
            add_factor(
                factors,
                "lifestyle",
                "Frequent alcohol use",
                "info",
                "Alcohol frequency may affect sleep quality, recovery, and metabolic healthspan alignment.",
                "Set alcohol-free days and avoid alcohol close to bedtime.",
            )
        if any(token in exercise for token in ["low", "rare", "none", "sedentary"]):
            activity += 15

    twin_misalignment = 100 - twin_alignment_score
    activity += twin_misalignment * 0.08
    lifestyle_score += twin_misalignment * 0.08
    metabolic += twin_misalignment * 0.05

    scores = {
        "cardio_score": clamp(cardio),
        "metabolic_score": clamp(metabolic),
        "sleep_score": clamp(sleep),
        "activity_score": clamp(activity),
        "lifestyle_score": clamp(lifestyle_score),
        "anomaly_score": clamp(anomaly),
        "twin_alignment_score": clamp(twin_alignment_score),
    }
    overall = (
        scores["cardio_score"] * 0.22
        + scores["metabolic_score"] * 0.2
        + scores["sleep_score"] * 0.14
        + scores["activity_score"] * 0.14
        + scores["lifestyle_score"] * 0.14
        + scores["anomaly_score"] * 0.16
    )
    scores["overall_risk_level"] = risk_level(overall)
    scores["explanation"] = (
        "This score reflects preventive risk patterns and healthspan alignment signals "
        "from profile, lifestyle, wearable, and lab data. It is not a diagnosis."
    )
    scores["risk_factors"] = factors
    scores["recommendations"] = [
        {
            "category": factor["category"],
            "action": factor["suggested_action"],
        }
        for factor in factors[:6]
    ] or [
        {
            "category": "general",
            "action": "Maintain consistent sleep, regular activity, balanced meals, and periodic preventive checkups.",
        }
    ]
    scores["calculated_at"] = utc_now()
    return scores


def calculate_and_store_risk(db: Session, user_id: UUID):
    user = user_repository.ensure_user(db, user_id)
    lifestyle = health_repository.get_lifestyle(db, user_id)
    latest_reading = wearable_repository.get_latest_reading(db, user_id)
    latest_lab = health_repository.get_latest_lab_report(db, user_id)
    twin_snapshot = get_twin_snapshot(db, user)
    payload = calculate_scores(
        user,
        lifestyle,
        latest_reading,
        latest_lab,
        twin_snapshot["twin_alignment_score"],
    )
    return risk_repository.save_risk_score(db, user_id, payload)
