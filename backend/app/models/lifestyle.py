import uuid
from typing import Any, TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class LifestyleProfile(TimestampMixin, Base):
    __tablename__ = "lifestyle_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    smoking_status: Mapped[str | None] = mapped_column(String(100))
    alcohol_frequency: Mapped[str | None] = mapped_column(String(100))
    exercise_frequency: Mapped[str | None] = mapped_column(String(100))
    diet_quality: Mapped[str | None] = mapped_column(String(100))
    stress_level: Mapped[str | None] = mapped_column(String(100))
    sleep_goal_hours: Mapped[float | None]
    medical_conditions: Mapped[list[str] | dict[str, Any] | None] = mapped_column(JSONB)
    family_history: Mapped[list[str] | dict[str, Any] | None] = mapped_column(JSONB)

    user: Mapped["User"] = relationship(back_populates="lifestyle_profile")
