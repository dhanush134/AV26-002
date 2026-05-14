from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.repositories import health_repository, user_repository
from app.schemas.lab_report import LabReportCreate, LabReportResponse

router = APIRouter()


@router.post("/users/{user_id}/lab-reports", response_model=LabReportResponse, status_code=201)
def create_lab_report(user_id: UUID, payload: LabReportCreate, db: Session = Depends(get_db)):
    user_repository.ensure_user(db, user_id)
    return health_repository.create_lab_report(db, user_id, payload)


@router.get("/users/{user_id}/lab-reports", response_model=list[LabReportResponse])
def list_lab_reports(user_id: UUID, db: Session = Depends(get_db)):
    user_repository.ensure_user(db, user_id)
    return health_repository.list_lab_reports(db, user_id)


@router.get("/users/{user_id}/lab-reports/latest", response_model=LabReportResponse)
def latest_lab_report(user_id: UUID, db: Session = Depends(get_db)):
    user_repository.ensure_user(db, user_id)
    report = health_repository.get_latest_lab_report(db, user_id)
    if report is None:
        raise NotFoundError("Lab report not found")
    return report
