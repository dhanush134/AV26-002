import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, CreatedAtMixin, utc_now

if TYPE_CHECKING:
    from app.models.user import User


class WearableReading(CreatedAtMixin, Base):
    __tablename__ = "wearable_readings"
    __table_args__ = (
        Index("ix_wearable_readings_user_timestamp", "user_id", "timestamp"),
        CheckConstraint(
            "source IN ('manual', 'synthetic', 'dataset', 'watch')",
            name="ck_wearable_readings_source",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, index=True, nullable=False
    )
    heart_rate: Mapped[int | None] = mapped_column(Integer)
    resting_heart_rate: Mapped[int | None] = mapped_column(Integer)
    spo2: Mapped[float | None] = mapped_column(Float)
    steps: Mapped[int | None] = mapped_column(Integer)
    active_minutes: Mapped[int | None] = mapped_column(Integer)
    sleep_hours: Mapped[float | None] = mapped_column(Float)
    sleep_quality: Mapped[float | None] = mapped_column(Float)
    calories: Mapped[float | None] = mapped_column(Float)
    stress_score: Mapped[float | None] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(50), default="manual", nullable=False)

    user: Mapped["User"] = relationship(back_populates="wearable_readings")
