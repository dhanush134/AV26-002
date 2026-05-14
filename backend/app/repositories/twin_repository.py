from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.twin import TwinGoal
from app.schemas.twin import TwinGoalCreate


def create_twin_goal(db: Session, user_id: UUID, payload: TwinGoalCreate) -> TwinGoal:
    goal = TwinGoal(user_id=user_id, **payload.model_dump())
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


def get_latest_twin_goal(db: Session, user_id: UUID) -> TwinGoal | None:
    return db.scalar(
        select(TwinGoal)
        .where(TwinGoal.user_id == user_id)
        .order_by(TwinGoal.created_at.desc())
        .limit(1)
    )
