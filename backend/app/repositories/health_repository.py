from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.lab_report import LabReport
from app.models.lifestyle import LifestyleProfile
from app.schemas.lab_report import LabReportCreate
from app.schemas.lifestyle import LifestyleCreate, LifestyleUpdate


def upsert_lifestyle(db: Session, user_id: UUID, payload: LifestyleCreate | LifestyleUpdate) -> LifestyleProfile:
    profile = db.scalar(select(LifestyleProfile).where(LifestyleProfile.user_id == user_id))
    values = payload.model_dump(exclude_unset=True)
    if profile is None:
        profile = LifestyleProfile(user_id=user_id, **values)
        db.add(profile)
    else:
        for key, value in values.items():
            setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    return profile


def get_lifestyle(db: Session, user_id: UUID) -> LifestyleProfile | None:
    return db.scalar(select(LifestyleProfile).where(LifestyleProfile.user_id == user_id))


def create_lab_report(db: Session, user_id: UUID, payload: LabReportCreate) -> LabReport:
    report = LabReport(user_id=user_id, **payload.model_dump())
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def list_lab_reports(db: Session, user_id: UUID) -> list[LabReport]:
    return list(
        db.scalars(
            select(LabReport)
            .where(LabReport.user_id == user_id)
            .order_by(LabReport.report_date.desc(), LabReport.created_at.desc())
        )
    )


def get_latest_lab_report(db: Session, user_id: UUID) -> LabReport | None:
    return db.scalar(
        select(LabReport)
        .where(LabReport.user_id == user_id)
        .order_by(LabReport.report_date.desc(), LabReport.created_at.desc())
        .limit(1)
    )
