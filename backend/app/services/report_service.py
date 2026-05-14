from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.alert import PreventiveAlert
from app.repositories import health_repository, risk_repository, user_repository, wearable_repository
from app.services.daily_plan_engine import generate_daily_routine


def _user_profile(user) -> dict:
    return {
        "id": user.id,
        "full_name": user.full_name,
        "age": user.age,
        "gender": user.gender,
        "height_cm": user.height_cm,
        "weight_kg": user.weight_kg,
        "target_age": user.target_age,
    }


def _vitals(reading) -> dict | None:
    if reading is None:
        return None
    return {
        "timestamp": reading.timestamp,
        "heart_rate": reading.heart_rate,
        "resting_heart_rate": reading.resting_heart_rate,
        "spo2": reading.spo2,
        "steps": reading.steps,
        "active_minutes": reading.active_minutes,
        "sleep_hours": reading.sleep_hours,
        "stress_score": reading.stress_score,
        "source": reading.source,
    }


def _labs(report) -> dict | None:
    if report is None:
        return None
    return {
        "report_date": report.report_date,
        "bp_systolic": report.bp_systolic,
        "bp_diastolic": report.bp_diastolic,
        "fasting_glucose": report.fasting_glucose,
        "hba1c": report.hba1c,
        "ldl": report.ldl,
        "hdl": report.hdl,
        "triglycerides": report.triglycerides,
        "vitamin_d": report.vitamin_d,
        "vitamin_b12": report.vitamin_b12,
        "sgpt": report.sgpt,
        "sgot": report.sgot,
        "creatinine": report.creatinine,
    }


def _risk(score) -> dict | None:
    if score is None:
        return None
    return {
        "calculated_at": score.calculated_at,
        "cardio_score": score.cardio_score,
        "metabolic_score": score.metabolic_score,
        "sleep_score": score.sleep_score,
        "activity_score": score.activity_score,
        "lifestyle_score": score.lifestyle_score,
        "anomaly_score": score.anomaly_score,
        "twin_alignment_score": score.twin_alignment_score,
        "overall_risk_level": score.overall_risk_level,
        "explanation": score.explanation,
    }


def recent_alerts(db: Session, user_id: UUID, limit: int = 10) -> list[dict]:
    alerts = db.scalars(
        select(PreventiveAlert)
        .where(PreventiveAlert.user_id == user_id)
        .order_by(PreventiveAlert.created_at.desc())
        .limit(limit)
    )
    return [
        {
            "id": alert.id,
            "severity": alert.severity,
            "title": alert.title,
            "message": alert.message,
            "recommended_action": alert.recommended_action,
            "acknowledged": alert.acknowledged,
            "created_at": alert.created_at,
        }
        for alert in alerts
    ]


def build_preventive_plan(db: Session, user_id: UUID) -> dict:
    routine = generate_daily_routine(db, user_id)
    return {
        "user_id": user_id,
        "focus_areas": routine["focus_areas"],
        "daily_routine": routine["actions"],
        "weekly_targets": {
            "steps": "Build toward 8000 steps per day on at least 5 days.",
            "sleep": "Protect 7-8 hours of sleep opportunity on most nights.",
            "cardio": "Accumulate 120-150 minutes of low-to-moderate intensity activity.",
            "nutrition": "Use protein and fiber anchors in at least two meals daily.",
        },
        "follow_up_suggestions": [
            "Review elevated markers with a qualified healthcare professional.",
            "Repeat wearable trend review after 14 days of routine adherence.",
            "Recheck labs based on clinician guidance and personal risk context.",
        ],
    }


def build_doctor_report(db: Session, user_id: UUID) -> dict:
    user = user_repository.ensure_user(db, user_id)
    latest_reading = wearable_repository.get_latest_reading(db, user_id)
    latest_lab = health_repository.get_latest_lab_report(db, user_id)
    latest_risk = risk_repository.get_latest_risk_score(db, user_id)
    return {
        "user_id": user_id,
        "user_profile": _user_profile(user),
        "latest_vitals_summary": _vitals(latest_reading),
        "latest_lab_summary": _labs(latest_lab),
        "latest_risk_scores": _risk(latest_risk),
        "top_risk_factors": latest_risk.risk_factors[:5] if latest_risk else [],
        "recent_alerts": recent_alerts(db, user_id),
        "preventive_plan": build_preventive_plan(db, user_id),
    }
