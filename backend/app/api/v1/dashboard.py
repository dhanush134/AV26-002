from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.dashboard import DashboardResponse
from app.services import dashboard_service

router = APIRouter()


@router.get("/users/{user_id}/dashboard", response_model=DashboardResponse)
def get_dashboard(user_id: UUID, db: Session = Depends(get_db)):
    return dashboard_service.build_dashboard(db, user_id)
