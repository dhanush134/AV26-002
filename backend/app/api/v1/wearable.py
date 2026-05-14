from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories import user_repository, wearable_repository
from app.schemas.wearable import (
    WearableBulkCreate,
    WearableReadingCreate,
    WearableReadingResponse,
    WearableSummary,
)

router = APIRouter()


@router.post("/users/{user_id}/wearable-readings", response_model=WearableReadingResponse, status_code=201)
def create_wearable_reading(
    user_id: UUID, payload: WearableReadingCreate, db: Session = Depends(get_db)
):
    user_repository.ensure_user(db, user_id)
    return wearable_repository.create_reading(db, user_id, payload)


@router.post("/users/{user_id}/wearable-readings/bulk", response_model=list[WearableReadingResponse], status_code=201)
def create_wearable_readings_bulk(
    user_id: UUID, payload: WearableBulkCreate, db: Session = Depends(get_db)
):
    user_repository.ensure_user(db, user_id)
    return wearable_repository.bulk_create_readings(db, user_id, payload.readings)


@router.get("/users/{user_id}/wearable-readings", response_model=list[WearableReadingResponse])
def list_wearable_readings(
    user_id: UUID,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    user_repository.ensure_user(db, user_id)
    return wearable_repository.list_readings(db, user_id, from_date, to_date, limit)


@router.get("/users/{user_id}/wearable-summary", response_model=WearableSummary)
def wearable_summary(user_id: UUID, db: Session = Depends(get_db)):
    user_repository.ensure_user(db, user_id)
    summary = wearable_repository.summarize_readings(db, user_id)
    summary["latest_reading"] = wearable_repository.get_latest_reading(db, user_id)
    return summary
