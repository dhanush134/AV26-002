from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.report import DoctorReportResponse, PreventivePlanResponse
from app.services import report_service

router = APIRouter()


@router.get("/users/{user_id}/doctor-report", response_model=DoctorReportResponse)
def doctor_report(user_id: UUID, db: Session = Depends(get_db)):
    return report_service.build_doctor_report(db, user_id)


@router.get("/users/{user_id}/preventive-plan", response_model=PreventivePlanResponse)
def preventive_plan(user_id: UUID, db: Session = Depends(get_db)):
    return report_service.build_preventive_plan(db, user_id)
