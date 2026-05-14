import uuid
from datetime import datetime
from typing import Any, TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, CreatedAtMixin, utc_now

if TYPE_CHECKING:
    from app.models.user import User


class RiskScore(CreatedAtMixin, Base):
    __tablename__ = "risk_scores"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, index=True, nullable=False
    )
    cardio_score: Mapped[float] = mapped_column(Float, nullable=False)
    metabolic_score: Mapped[float] = mapped_column(Float, nullable=False)
    sleep_score: Mapped[float] = mapped_column(Float, nullable=False)
    activity_score: Mapped[float] = mapped_column(Float, nullable=False)
    lifestyle_score: Mapped[float] = mapped_column(Float, nullable=False)
    anomaly_score: Mapped[float] = mapped_column(Float, nullable=False)
    twin_alignment_score: Mapped[float] = mapped_column(Float, nullable=False)
    overall_risk_level: Mapped[str] = mapped_column(String(50), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    risk_factors: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    recommendations: Mapped[list[dict[str, Any]] | list[str]] = mapped_column(JSONB, nullable=False)

    user: Mapped["User"] = relationship(back_populates="risk_scores")
