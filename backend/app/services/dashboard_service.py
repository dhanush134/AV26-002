from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.alert import PreventiveAlert
from app.repositories import health_repository, risk_repository, user_repository, wearable_repository
from app.schemas.common import MEDICAL_DISCLAIMER
from app.services import alert_engine, daily_plan_engine, risk_engine
from app.services.twin_engine import calculate_bmi


def _risk_or_create(db: Session, user_id: UUID):
    risk_score = risk_repository.get_latest_risk_score(db, user_id)
    if risk_score is None:
        risk_score = risk_engine.calculate_and_store_risk(db, user_id)
    return risk_score


def _latest_alerts(db: Session, user_id: UUID, limit: int = 5) -> list[dict]:
    alert_engine.generate_and_store_alerts(db, user_id)
    alerts = db.scalars(
        select(PreventiveAlert)
        .where(PreventiveAlert.user_id == user_id)
        .order_by(PreventiveAlert.created_at.desc())
        .limit(limit)
    )
    return [
        {
            "severity": alert.severity,
            "title": alert.title,
            "message": alert.message,
        }
        for alert in alerts
    ]


def _risk_factors(risk_score, limit: int = 5) -> list[dict]:
    factors = risk_score.risk_factors or []
    return [
        {
            "category": factor.get("category", "general"),
            "factor": factor.get("factor", "Preventive risk pattern"),
            "severity": factor.get("severity", "info"),
            "suggested_action": factor.get(
                "suggested_action",
                "Maintain consistent sleep, activity, nutrition, and preventive check-ins.",
            ),
        }
        for factor in factors[:limit]
    ]


def _today_actions(db: Session, user_id: UUID) -> list[dict]:
    actions = daily_plan_engine.ensure_today_actions(db, user_id)
    return [
        {
            "category": action.category,
            "recommended_action": action.recommended_action,
            "priority": action.priority,
            "completed": action.completed,
        }
        for action in actions
    ]


def _trend(readings, field: str) -> list[dict]:
    points = []
    for reading in reversed(readings):
        value = getattr(reading, field)
        if value is None:
            continue
        points.append({"timestamp": reading.timestamp, "value": float(value)})
    return points


def build_dashboard(db: Session, user_id: UUID) -> dict:
    user = user_repository.ensure_user(db, user_id)
    latest_reading = wearable_repository.get_latest_reading(db, user_id)
    health_repository.get_latest_lab_report(db, user_id)
    risk_score = _risk_or_create(db, user_id)
    recent_readings = wearable_repository.get_recent_readings(db, user_id, limit=50)

    alignment = float(risk_score.twin_alignment_score)
    return {
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "age": user.age,
            "gender": user.gender,
            "height_cm": user.height_cm,
            "weight_kg": user.weight_kg,
            "bmi": calculate_bmi(user.height_cm, user.weight_kg),
            "target_age": user.target_age,
        },
        "current_status": {
            "overall_risk_level": risk_score.overall_risk_level,
            "twin_alignment_score": alignment,
            "anomaly_score": float(risk_score.anomaly_score),
            "summary_message": (
                f"Your health twin is currently {round(alignment)}% aligned with your target future self."
            ),
        },
        "latest_vitals": {
            "heart_rate": latest_reading.heart_rate if latest_reading else None,
            "resting_heart_rate": latest_reading.resting_heart_rate if latest_reading else None,
            "spo2": latest_reading.spo2 if latest_reading else None,
            "steps": latest_reading.steps if latest_reading else None,
            "sleep_hours": latest_reading.sleep_hours if latest_reading else None,
            "active_minutes": latest_reading.active_minutes if latest_reading else None,
            "timestamp": latest_reading.timestamp if latest_reading else None,
        },
        "risk_scores": {
            "cardio_score": float(risk_score.cardio_score),
            "metabolic_score": float(risk_score.metabolic_score),
            "sleep_score": float(risk_score.sleep_score),
            "activity_score": float(risk_score.activity_score),
            "lifestyle_score": float(risk_score.lifestyle_score),
        },
        "top_risk_factors": _risk_factors(risk_score),
        "today_actions": _today_actions(db, user_id),
        "recent_alerts": _latest_alerts(db, user_id),
        "charts": {
            "heart_rate_trend": _trend(recent_readings, "heart_rate"),
            "sleep_trend": _trend(recent_readings, "sleep_hours"),
            "steps_trend": _trend(recent_readings, "steps"),
            "risk_breakdown": [
                {"label": "Cardio", "value": float(risk_score.cardio_score)},
                {"label": "Metabolic", "value": float(risk_score.metabolic_score)},
                {"label": "Sleep", "value": float(risk_score.sleep_score)},
                {"label": "Activity", "value": float(risk_score.activity_score)},
                {"label": "Lifestyle", "value": float(risk_score.lifestyle_score)},
                {"label": "Anomaly", "value": float(risk_score.anomaly_score)},
            ],
        },
        "disclaimer": MEDICAL_DISCLAIMER,
    }
