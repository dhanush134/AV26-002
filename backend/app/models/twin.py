import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class TwinGoal(TimestampMixin, Base):
    __tablename__ = "twin_goals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    target_age: Mapped[int] = mapped_column(Integer, nullable=False)
    target_weight_kg: Mapped[float | None] = mapped_column(Float)
    target_sleep_hours: Mapped[float | None] = mapped_column(Float)
    target_steps: Mapped[int | None] = mapped_column(Integer)
    target_resting_hr: Mapped[int | None] = mapped_column(Integer)
    target_bp_systolic: Mapped[int | None] = mapped_column(Integer)
    target_bp_diastolic: Mapped[int | None] = mapped_column(Integer)
    target_ldl: Mapped[float | None] = mapped_column(Float)
    goal_description: Mapped[str | None] = mapped_column(Text)

    user: Mapped["User"] = relationship(back_populates="twin_goals")
