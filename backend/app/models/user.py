import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Float, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.alert import PreventiveAlert
    from app.models.daily_checkin import DailyCheckin, TwinAction
    from app.models.lab_report import LabReport
    from app.models.lifestyle import LifestyleProfile
    from app.models.risk_score import RiskScore
    from app.models.twin import TwinGoal
    from app.models.wearable import WearableReading


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    gender: Mapped[str | None] = mapped_column(String(50))
    height_cm: Mapped[float] = mapped_column(Float, nullable=False)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    target_age: Mapped[int | None] = mapped_column(Integer)

    lifestyle_profile: Mapped["LifestyleProfile | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )
    wearable_readings: Mapped[list["WearableReading"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    lab_reports: Mapped[list["LabReport"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    risk_scores: Mapped[list["RiskScore"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    twin_goals: Mapped[list["TwinGoal"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    daily_checkins: Mapped[list["DailyCheckin"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    twin_actions: Mapped[list["TwinAction"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    preventive_alerts: Mapped[list["PreventiveAlert"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
