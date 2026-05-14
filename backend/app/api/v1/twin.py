from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories import user_repository
from app.schemas.twin import TwinGoalResponse, TwinSummaryResponse
from app.services import twin_engine

router = APIRouter()


@router.post("/users/{user_id}/twin/generate", response_model=TwinGoalResponse, status_code=201)
def generate_twin(user_id: UUID, db: Session = Depends(get_db)):
    user = user_repository.ensure_user(db, user_id)
    return twin_engine.generate_twin_goal(db, user)


@router.get("/users/{user_id}/twin/current", response_model=TwinSummaryResponse)
def current_twin(user_id: UUID, db: Session = Depends(get_db)):
    return twin_engine.snapshot_for_user_id(db, user_id)


@router.get("/users/{user_id}/twin/ideal", response_model=TwinSummaryResponse)
def ideal_twin(user_id: UUID, db: Session = Depends(get_db)):
    return twin_engine.snapshot_for_user_id(db, user_id)


@router.get("/users/{user_id}/twin/gap", response_model=TwinSummaryResponse)
def twin_gap(user_id: UUID, db: Session = Depends(get_db)):
    return twin_engine.snapshot_for_user_id(db, user_id)
