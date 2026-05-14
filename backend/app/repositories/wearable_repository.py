from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import utc_now
from app.models.wearable import WearableReading
from app.schemas.wearable import WearableReadingCreate


def create_reading(db: Session, user_id: UUID, payload: WearableReadingCreate) -> WearableReading:
    values = payload.model_dump()
    values["timestamp"] = values["timestamp"] or utc_now()
    reading = WearableReading(user_id=user_id, **values)
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return reading


def bulk_create_readings(
    db: Session, user_id: UUID, payloads: list[WearableReadingCreate]
) -> list[WearableReading]:
    readings = []
    for payload in payloads:
        values = payload.model_dump()
        values["timestamp"] = values["timestamp"] or utc_now()
        readings.append(WearableReading(user_id=user_id, **values))
    db.add_all(readings)
    db.commit()
    for reading in readings:
        db.refresh(reading)
    return readings


def list_readings(
    db: Session,
    user_id: UUID,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    limit: int = 100,
) -> list[WearableReading]:
    stmt = select(WearableReading).where(WearableReading.user_id == user_id)
    if from_date is not None:
        stmt = stmt.where(WearableReading.timestamp >= from_date)
    if to_date is not None:
        stmt = stmt.where(WearableReading.timestamp <= to_date)
    stmt = stmt.order_by(WearableReading.timestamp.desc()).limit(limit)
    return list(db.scalars(stmt))


def get_latest_reading(db: Session, user_id: UUID) -> WearableReading | None:
    return db.scalar(
        select(WearableReading)
        .where(WearableReading.user_id == user_id)
        .order_by(WearableReading.timestamp.desc())
        .limit(1)
    )


def get_recent_readings(db: Session, user_id: UUID, limit: int = 30) -> list[WearableReading]:
    return list(
        db.scalars(
            select(WearableReading)
            .where(WearableReading.user_id == user_id)
            .order_by(WearableReading.timestamp.desc())
            .limit(limit)
        )
    )


def summarize_readings(db: Session, user_id: UUID) -> dict:
    row = db.execute(
        select(
            func.count(WearableReading.id),
            func.avg(WearableReading.steps),
            func.avg(WearableReading.sleep_hours),
            func.avg(WearableReading.resting_heart_rate),
        ).where(WearableReading.user_id == user_id)
    ).one()
    return {
        "count": row[0],
        "average_steps": float(row[1]) if row[1] is not None else None,
        "average_sleep_hours": float(row[2]) if row[2] is not None else None,
        "average_resting_heart_rate": float(row[3]) if row[3] is not None else None,
    }
