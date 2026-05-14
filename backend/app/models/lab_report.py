import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, Float, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class LabReport(TimestampMixin, Base):
    __tablename__ = "lab_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    report_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    bp_systolic: Mapped[int | None] = mapped_column(Integer)
    bp_diastolic: Mapped[int | None] = mapped_column(Integer)
    fasting_glucose: Mapped[float | None] = mapped_column(Float)
    hba1c: Mapped[float | None] = mapped_column(Float)
    ldl: Mapped[float | None] = mapped_column(Float)
    hdl: Mapped[float | None] = mapped_column(Float)
    triglycerides: Mapped[float | None] = mapped_column(Float)
    vitamin_d: Mapped[float | None] = mapped_column(Float)
    vitamin_b12: Mapped[float | None] = mapped_column(Float)
    sgpt: Mapped[float | None] = mapped_column(Float)
    sgot: Mapped[float | None] = mapped_column(Float)
    creatinine: Mapped[float | None] = mapped_column(Float)
    notes: Mapped[str | None] = mapped_column(Text)

    user: Mapped["User"] = relationship(back_populates="lab_reports")
