from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.daily_checkin import (
    DailyAdjustmentResponse,
    DailyCheckinCreate,
    DailyCheckinAdjustmentResponse,
    DailyRoutineResponse,
)
from app.services import daily_plan_engine

router = APIRouter()


@router.get("/users/{user_id}/daily-routine", response_model=DailyRoutineResponse)
def daily_routine(user_id: UUID, db: Session = Depends(get_db)):
    return daily_plan_engine.generate_daily_routine(db, user_id)


@router.post("/users/{user_id}/daily-checkin", response_model=DailyCheckinAdjustmentResponse, status_code=201)
def create_daily_checkin(user_id: UUID, payload: DailyCheckinCreate, db: Session = Depends(get_db)):
    return daily_plan_engine.save_checkin_with_adjustment(db, user_id, payload)


@router.post("/users/{user_id}/daily-adjustment", response_model=DailyAdjustmentResponse)
def daily_adjustment(user_id: UUID, db: Session = Depends(get_db)):
    return daily_plan_engine.generate_daily_adjustment(db, user_id)
