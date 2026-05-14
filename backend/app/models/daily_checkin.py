import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, CreatedAtMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class DailyCheckin(CreatedAtMixin, Base):
    __tablename__ = "daily_checkins"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    checkin_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    sleep_quality: Mapped[str | None] = mapped_column(String(100))
    exercise_done: Mapped[str | None] = mapped_column(String(100))
    food_quality: Mapped[str | None] = mapped_column(String(100))
    alcohol_used: Mapped[bool | None] = mapped_column(Boolean)
    smoking_done: Mapped[bool | None] = mapped_column(Boolean)
    stress_level: Mapped[str | None] = mapped_column(String(100))
    steps_completed: Mapped[int | None] = mapped_column(Integer)
    sleep_hours: Mapped[float | None]
    user_notes: Mapped[str | None] = mapped_column(Text)

    user: Mapped["User"] = relationship(back_populates="daily_checkins")


class TwinAction(TimestampMixin, Base):
    __tablename__ = "twin_actions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    action_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    recommended_action: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(50), nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["User"] = relationship(back_populates="twin_actions")
