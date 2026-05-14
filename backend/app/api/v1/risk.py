from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.repositories import risk_repository, user_repository
from app.schemas.risk_score import RiskScoreResponse
from app.services import alert_engine, risk_engine

router = APIRouter()


@router.post("/users/{user_id}/risk/calculate", response_model=RiskScoreResponse, status_code=201)
def calculate_risk(user_id: UUID, db: Session = Depends(get_db)):
    risk_score = risk_engine.calculate_and_store_risk(db, user_id)
    alert_engine.generate_and_store_alerts(db, user_id)
    return risk_score


@router.get("/users/{user_id}/risk/latest", response_model=RiskScoreResponse)
def latest_risk(user_id: UUID, db: Session = Depends(get_db)):
    user_repository.ensure_user(db, user_id)
    risk_score = risk_repository.get_latest_risk_score(db, user_id)
    if risk_score is None:
        raise NotFoundError("Risk score not found")
    return risk_score


@router.get("/users/{user_id}/risk/history", response_model=list[RiskScoreResponse])
def risk_history(
    user_id: UUID,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    user_repository.ensure_user(db, user_id)
    return risk_repository.list_risk_scores(db, user_id, limit=limit)
