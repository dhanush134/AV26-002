from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.daily_checkin import DailyCheckin, TwinAction
from app.repositories import user_repository
from app.services.twin_engine import get_twin_snapshot


def _action(category: str, recommended_action: str, priority: str) -> dict:
    return {
        "category": category,
        "recommended_action": recommended_action,
        "priority": priority,
        "completed": False,
    }


def generate_daily_routine(db: Session, user_id: UUID) -> dict:
    user = user_repository.ensure_user(db, user_id)
    snapshot = get_twin_snapshot(db, user)
    gap = snapshot["twin_gap"]
    actions = [
        _action("hydration", "Drink 2-3 liters of water across the day.", "medium"),
        _action("sunlight", "Get 10-15 minutes of morning sunlight exposure.", "low"),
        _action("nutrition", "Choose a high-protein, high-fiber breakfast.", "medium"),
    ]
    focus_areas = ["healthspan alignment"]

    if gap["sleep"]["status"] == "needs_attention":
        actions.append(_action("sleep", "Start wind-down by 10:15 PM and sleep before 10:45 PM.", "high"))
        focus_areas.append("sleep recovery")
    if gap["steps"]["status"] == "needs_attention":
        actions.append(_action("activity", "Walk 6000-8000 steps using two short walk blocks.", "high"))
        focus_areas.append("daily movement")
    if gap["resting_heart_rate"]["status"] == "needs_attention":
        actions.append(_action("cardio", "Do 20-30 minutes of easy zone-2 cardio if you feel well.", "medium"))
        focus_areas.append("cardio recovery")
    if gap["weight"]["status"] == "needs_attention" or gap["ldl"]["status"] == "needs_attention":
        actions.append(
            _action(
                "nutrition",
                "Reduce fried food and late-night heavy meals; add vegetables or legumes to two meals.",
                "high",
            )
        )
        focus_areas.append("metabolic habits")
    actions.append(_action("avoidance", "Avoid alcohol and smoking today to improve recovery signals.", "medium"))

    return {
        "user_id": user_id,
        "routine_date": date.today(),
        "focus_areas": sorted(set(focus_areas)),
        "actions": actions,
    }


def save_checkin(db: Session, user_id: UUID, payload) -> DailyCheckin:
    user_repository.ensure_user(db, user_id)
    values = payload.model_dump(exclude_unset=True)
    values["checkin_date"] = values.get("checkin_date") or date.today()
    checkin = DailyCheckin(user_id=user_id, **values)
    db.add(checkin)
    db.commit()
    db.refresh(checkin)
    return checkin


def save_checkin_with_adjustment(db: Session, user_id: UUID, payload) -> dict:
    checkin = save_checkin(db, user_id, payload)
    adjustment = generate_daily_adjustment(db, user_id)
    return {"checkin": checkin, **adjustment}


def latest_checkin(db: Session, user_id: UUID) -> DailyCheckin | None:
    return db.scalar(
        select(DailyCheckin)
        .where(DailyCheckin.user_id == user_id)
        .order_by(DailyCheckin.checkin_date.desc(), DailyCheckin.created_at.desc())
        .limit(1)
    )


def generate_daily_adjustment(db: Session, user_id: UUID) -> dict:
    user_repository.ensure_user(db, user_id)
    checkin = latest_checkin(db, user_id)
    if checkin is None:
        raise NotFoundError("Daily check-in not found")

    missed_items: list[str] = []
    alignment_delta = 0.0
    tomorrow_actions: list[dict] = []
    previous_alignment = get_twin_snapshot(db, user_repository.ensure_user(db, user_id))[
        "twin_alignment_score"
    ]

    if checkin.sleep_hours is not None and checkin.sleep_hours < 7:
        missed_items.append("Sleep target missed")
        alignment_delta -= 8
        tomorrow_actions.append(
            _action("sleep", "Prioritize 7 hours sleep before increasing workout intensity.", "high")
        )
    if checkin.steps_completed is not None and checkin.steps_completed < 6000:
        missed_items.append("Step goal missed")
        alignment_delta -= 6
        tomorrow_actions.append(_action("activity", "Walk 6000 steps minimum tomorrow.", "high"))
    if checkin.alcohol_used:
        missed_items.append("Alcohol-free target missed")
        alignment_delta -= 4
        tomorrow_actions.append(_action("recovery", "Keep tomorrow alcohol-free and hydrate earlier.", "medium"))
    if checkin.smoking_done:
        missed_items.append("Smoking avoidance missed")
        alignment_delta -= 8
        tomorrow_actions.append(_action("avoidance", "Use a planned smoking replacement cue and seek support.", "high"))
    if (checkin.food_quality or "").lower() in {"poor", "fried", "heavy"}:
        missed_items.append("Food quality target missed")
        alignment_delta -= 5
        tomorrow_actions.append(_action("nutrition", "Avoid late heavy dinner.", "medium"))
    if not missed_items:
        alignment_delta = 6
        tomorrow_actions.append(_action("consistency", "Repeat today's routine and keep the same sleep window.", "medium"))

    for payload in tomorrow_actions:
        db.add(
            TwinAction(
                user_id=user_id,
                action_date=date.today() + timedelta(days=1),
                **payload,
            )
        )
    db.commit()

    return {
        "user_id": user_id,
        "alignment_delta": alignment_delta,
        "previous_alignment": previous_alignment,
        "new_alignment": max(0, min(100, round(previous_alignment + alignment_delta, 1))),
        "missed_items": missed_items,
        "tomorrow_adjustments": tomorrow_actions,
        "encouraging_message": (
            "One bad day does not break the journey. Tomorrow's plan has been adjusted."
            if missed_items
            else "Strong alignment today. Keep the routine boring, repeatable, and easy to win."
        ),
    }


def get_latest_actions(db: Session, user_id: UUID, limit: int = 8) -> list[TwinAction]:
    return list(
        db.scalars(
            select(TwinAction)
            .where(TwinAction.user_id == user_id)
            .order_by(TwinAction.action_date.desc(), TwinAction.created_at.desc())
            .limit(limit)
        )
    )


def ensure_today_actions(db: Session, user_id: UUID) -> list[TwinAction]:
    today = date.today()
    existing = list(
        db.scalars(
            select(TwinAction)
            .where(TwinAction.user_id == user_id, TwinAction.action_date == today)
            .order_by(TwinAction.created_at.asc())
        )
    )
    if existing:
        return existing

    routine = generate_daily_routine(db, user_id)
    actions = [
        TwinAction(
            user_id=user_id,
            action_date=today,
            category=action["category"],
            recommended_action=action["recommended_action"],
            priority=action["priority"],
            completed=False,
        )
        for action in routine["actions"][:8]
    ]
    db.add_all(actions)
    db.commit()
    for action in actions:
        db.refresh(action)
    return actions
