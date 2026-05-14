from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.models.alert import PreventiveAlert
from app.repositories import user_repository
from app.schemas.alert import AlertResponse
from app.services import alert_engine

router = APIRouter()


@router.get("/users/{user_id}/alerts", response_model=list[AlertResponse])
def list_alerts(user_id: UUID, db: Session = Depends(get_db)):
    user_repository.ensure_user(db, user_id)
    alert_engine.generate_and_store_alerts(db, user_id)
    return list(
        db.scalars(
            select(PreventiveAlert)
            .where(PreventiveAlert.user_id == user_id)
            .order_by(PreventiveAlert.created_at.desc())
        )
    )


@router.post("/users/{user_id}/alerts/{alert_id}/acknowledge", response_model=AlertResponse)
def acknowledge_alert(user_id: UUID, alert_id: UUID, db: Session = Depends(get_db)):
    user_repository.ensure_user(db, user_id)
    alert = db.scalar(
        select(PreventiveAlert).where(
            PreventiveAlert.id == alert_id,
            PreventiveAlert.user_id == user_id,
        )
    )
    if alert is None:
        raise NotFoundError("Alert not found")
    alert.acknowledged = True
    db.commit()
    db.refresh(alert)
    return alert
