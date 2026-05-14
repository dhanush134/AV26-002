from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.risk_score import RiskScore


def save_risk_score(db: Session, user_id: UUID, payload: dict) -> RiskScore:
    risk_score = RiskScore(user_id=user_id, **payload)
    db.add(risk_score)
    db.commit()
    db.refresh(risk_score)
    return risk_score


def get_latest_risk_score(db: Session, user_id: UUID) -> RiskScore | None:
    return db.scalar(
        select(RiskScore)
        .where(RiskScore.user_id == user_id)
        .order_by(RiskScore.calculated_at.desc())
        .limit(1)
    )


def list_risk_scores(db: Session, user_id: UUID, limit: int = 20) -> list[RiskScore]:
    return list(
        db.scalars(
            select(RiskScore)
            .where(RiskScore.user_id == user_id)
            .order_by(RiskScore.calculated_at.desc())
            .limit(limit)
        )
    )
