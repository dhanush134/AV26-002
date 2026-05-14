from datetime import date, datetime, timedelta, timezone
from random import Random
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError
from app.models.lab_report import LabReport
from app.models.lifestyle import LifestyleProfile
from app.models.user import User
from app.models.wearable import WearableReading
from app.repositories import user_repository
from app.schemas.user import UserCreate
from app.services import alert_engine, dashboard_service, daily_plan_engine, risk_engine, twin_engine


SCENARIOS = {"normal", "fatigue", "respiratory_risk", "cardiac_strain", "poor_sleep_metabolic_risk"}


def create_demo_user(db: Session) -> User:
    user = user_repository.create_user(
        db,
        UserCreate(
            full_name="Aarav Mehta",
            age=34,
            gender="male",
            height_cm=172,
            weight_kg=92,
            target_age=80,
        ),
    )
    lifestyle = LifestyleProfile(
        user_id=user.id,
        smoking_status="no",
        alcohol_frequency="moderate",
        exercise_frequency="low",
        diet_quality="inconsistent",
        stress_level="high",
        sleep_goal_hours=7.5,
        medical_conditions=[],
        family_history=["cardio-metabolic risk pattern"],
    )
    lab = LabReport(
        user_id=user.id,
        report_date=date.today(),
        bp_systolic=136,
        bp_diastolic=86,
        fasting_glucose=104,
        hba1c=5.8,
        ldl=154,
        hdl=42,
        triglycerides=188,
        vitamin_d=24,
        vitamin_b12=410,
        sgpt=42,
        sgot=33,
        creatinine=0.96,
        notes="Demo values for preventive wellness risk pattern analysis.",
    )
    db.add_all([lifestyle, lab])
    db.add_all(_scenario_readings(user.id, "poor_sleep_metabolic_risk", days=7))
    db.commit()
    db.refresh(user)
    return user


def _scenario_readings(
    user_id: UUID, scenario: str, days: int = 7, interval_minutes: int = 1440
) -> list[WearableReading]:
    rng = Random(f"{user_id}:{scenario}:{days}:{interval_minutes}")
    now = datetime.now(timezone.utc)
    readings: list[WearableReading] = []
    for index in range(days):
        timestamp = now - timedelta(minutes=interval_minutes * (days - index - 1))
        normal_steps = 4500 + (index * 180) + rng.randint(-350, 500)
        values = {
            "heart_rate": rng.randint(65, 85),
            "resting_heart_rate": rng.randint(62, 75),
            "spo2": round(rng.uniform(97, 99), 1),
            "steps": max(0, normal_steps),
            "active_minutes": 30 + rng.randint(-8, 18),
            "sleep_hours": round(rng.uniform(7.0, 8.0), 1),
            "sleep_quality": 78 + rng.uniform(-6, 10),
            "calories": 2200 + rng.randint(-250, 250),
            "stress_score": 30 + rng.uniform(-8, 12),
        }
        if scenario == "fatigue":
            values.update(
                {
                    "heart_rate": rng.randint(84, 102),
                    "resting_heart_rate": rng.randint(80, 92),
                    "sleep_hours": round(rng.uniform(4.5, 5.5), 1),
                    "steps": 2600 + rng.randint(-500, 650),
                    "active_minutes": rng.randint(4, 14),
                    "stress_score": 72 + rng.uniform(-6, 12),
                }
            )
        elif scenario == "respiratory_risk":
            values.update(
                {
                    "spo2": round(rng.uniform(90, 93), 1) if index % 3 != 0 else round(rng.uniform(94, 96), 1),
                    "heart_rate": rng.randint(92, 112),
                    "resting_heart_rate": rng.randint(82, 94),
                    "active_minutes": rng.randint(0, 8),
                    "steps": 1800 + rng.randint(-400, 650),
                }
            )
        elif scenario == "cardiac_strain":
            values.update(
                {
                    "heart_rate": rng.randint(110, 130),
                    "resting_heart_rate": rng.randint(88, 101),
                    "active_minutes": rng.choice([0, 0, 2, 4]),
                    "stress_score": 75 + rng.uniform(-6, 10),
                    "steps": 2200 + rng.randint(-500, 700),
                }
            )
        elif scenario == "poor_sleep_metabolic_risk":
            values.update(
                {
                    "heart_rate": rng.randint(86, 104),
                    "resting_heart_rate": 86 + rng.randint(-3, 8),
                    "steps": 3000 + rng.randint(-600, 700),
                    "active_minutes": 10 + rng.randint(0, 8),
                    "sleep_hours": round(5.2 + rng.uniform(-0.6, 0.5), 1),
                    "sleep_quality": 52 + rng.uniform(-10, 8),
                    "stress_score": 70 + rng.uniform(-8, 10),
                }
            )
        readings.append(WearableReading(user_id=user_id, timestamp=timestamp, source="synthetic", **values))
    return readings


def generate_readings(db: Session, user_id: UUID, scenario: str = "normal", days: int = 7) -> list[WearableReading]:
    user_repository.ensure_user(db, user_id)
    if scenario not in SCENARIOS:
        raise BadRequestError(f"Invalid scenario. Allowed values: {', '.join(sorted(SCENARIOS))}")
    readings = _scenario_readings(user_id, scenario, days)
    db.add_all(readings)
    db.commit()
    for reading in readings:
        db.refresh(reading)
    return readings


def run_scenario(db: Session, user_id: UUID, scenario: str) -> dict:
    readings = generate_readings(db, user_id, scenario=scenario, days=5)
    return {
        "user_id": user_id,
        "scenario": scenario,
        "generated_readings": len(readings),
        "message": "Synthetic wearable stream generated for preventive trajectory testing.",
    }


def run_full_demo(db: Session) -> dict:
    user = create_demo_user(db)
    risk_engine.calculate_and_store_risk(db, user.id)
    twin_engine.generate_twin_goal(db, user)
    daily_plan_engine.ensure_today_actions(db, user.id)
    alert_engine.generate_and_store_alerts(db, user.id)
    return {
        "message": "LifeTwin AI demo user created successfully.",
        "user_id": user.id,
        "demo_scenario": "poor_sleep_metabolic_risk",
        "next_steps": {
            "dashboard": f"/api/v1/users/{user.id}/dashboard",
            "risk": f"/api/v1/users/{user.id}/risk/latest",
            "current_twin": f"/api/v1/users/{user.id}/twin/current",
            "ideal_twin": f"/api/v1/users/{user.id}/twin/ideal",
            "daily_routine": f"/api/v1/users/{user.id}/daily-routine",
            "doctor_report": f"/api/v1/users/{user.id}/doctor-report",
        },
    }


def replay_scenario(db: Session, user_id: UUID, scenario: str, points: int) -> dict:
    user_repository.ensure_user(db, user_id)
    if scenario not in SCENARIOS:
        raise BadRequestError(f"Invalid scenario. Allowed values: {', '.join(sorted(SCENARIOS))}")
    readings = _scenario_readings(user_id, scenario, days=points, interval_minutes=30)
    db.add_all(readings)
    db.commit()
    risk_engine.calculate_and_store_risk(db, user_id)
    alert_engine.generate_and_store_alerts(db, user_id)
    return dashboard_service.build_dashboard(db, user_id)
