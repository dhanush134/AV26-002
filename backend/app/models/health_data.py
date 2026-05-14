import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, CreatedAtMixin, TimestampMixin, utc_now


def uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class HealthUserImportMixin:
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    import_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("health_imports.id", ondelete="SET NULL"), index=True
    )
    source: Mapped[str] = mapped_column(String(80), default="samsung_health_export", nullable=False)
    source_file: Mapped[str | None] = mapped_column(String(1000))
    datauuid: Mapped[str | None] = mapped_column(String(255), index=True)
    deviceuuid: Mapped[str | None] = mapped_column(String(255), index=True)


class HealthImport(TimestampMixin, Base):
    __tablename__ = "health_imports"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    source: Mapped[str] = mapped_column(String(80), default="samsung_health_export", nullable=False)
    original_filename: Mapped[str | None] = mapped_column(String(500))
    file_sha256: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    import_status: Mapped[str] = mapped_column(String(50), default="parsed", nullable=False)
    detected_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    files_processed: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    warnings: Mapped[list[str] | None] = mapped_column(JSONB)
    errors: Mapped[list[str] | None] = mapped_column(JSONB)
    record_counts: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (UniqueConstraint("user_id", "file_sha256", name="uq_health_import_user_file_sha"),)


class HealthImportFile(CreatedAtMixin, Base):
    __tablename__ = "health_import_files"

    id: Mapped[uuid.UUID] = uuid_pk()
    import_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("health_imports.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    path: Mapped[str] = mapped_column(String(1000), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100))
    file_type: Mapped[str] = mapped_column(String(20), default="unknown", nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    parsed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    warning_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class HealthHeartRatePeriod(HealthUserImportMixin, TimestampMixin, Base):
    __tablename__ = "health_heart_rate_periods"

    id: Mapped[uuid.UUID] = uuid_pk()
    package_name: Mapped[str | None] = mapped_column(String(255))
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    avg_bpm: Mapped[float | None] = mapped_column(Float)
    min_bpm: Mapped[float | None] = mapped_column(Float)
    max_bpm: Mapped[float | None] = mapped_column(Float)
    heart_beat_count: Mapped[int | None] = mapped_column(Integer)
    binning_data_ref: Mapped[str | None] = mapped_column(String(500))
    time_offset_ms: Mapped[int | None] = mapped_column(Integer)
    create_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    update_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    raw_extra: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    __table_args__ = (
        UniqueConstraint("user_id", "datauuid", name="uq_hr_period_user_datauuid"),
        UniqueConstraint("user_id", "source_file", "start_time", "end_time", "avg_bpm", name="uq_hr_period_fallback"),
        Index("ix_hr_period_user_start", "user_id", "start_time"),
    )


class HealthHeartRateSample(TimestampMixin, Base):
    __tablename__ = "health_heart_rate_samples"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    import_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("health_imports.id", ondelete="SET NULL"), index=True
    )
    parent_period_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("health_heart_rate_periods.id", ondelete="SET NULL"), index=True
    )
    parent_datauuid: Mapped[str | None] = mapped_column(String(255), index=True)
    parent_binning_data_ref: Mapped[str | None] = mapped_column(String(500))
    source: Mapped[str] = mapped_column(String(80), default="samsung_health_export", nullable=False)
    source_json_file: Mapped[str | None] = mapped_column(String(1000))
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    bpm: Mapped[float | None] = mapped_column(Float, index=True)
    min_bpm: Mapped[float | None] = mapped_column(Float)
    max_bpm: Mapped[float | None] = mapped_column(Float)
    raw_extra: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    __table_args__ = (
        UniqueConstraint("user_id", "parent_datauuid", "start_time", "end_time", "bpm", name="uq_hr_sample_identity"),
        Index("ix_hr_sample_user_start", "user_id", "start_time"),
        Index("ix_hr_sample_user_bpm", "user_id", "bpm"),
        Index("ix_hr_sample_user_start_bpm", "user_id", "start_time", "bpm"),
    )


class HealthStepInterval(HealthUserImportMixin, TimestampMixin, Base):
    __tablename__ = "health_step_intervals"

    id: Mapped[uuid.UUID] = uuid_pk()
    package_name: Mapped[str | None] = mapped_column(String(255))
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    steps: Mapped[int | None] = mapped_column(Integer)
    distance_meters: Mapped[float | None] = mapped_column(Float)
    calories: Mapped[float | None] = mapped_column(Float)
    speed: Mapped[float | None] = mapped_column(Float)
    sample_position_type: Mapped[int | None] = mapped_column(Integer)
    time_offset_ms: Mapped[int | None] = mapped_column(Integer)
    create_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    update_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    raw_extra: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    __table_args__ = (
        UniqueConstraint("user_id", "datauuid", name="uq_step_interval_user_datauuid"),
        UniqueConstraint("user_id", "start_time", "end_time", "steps", "source_file", name="uq_step_interval_fallback"),
        Index("ix_step_interval_user_start", "user_id", "start_time"),
    )


class HealthStepDailySummary(HealthUserImportMixin, TimestampMixin, Base):
    __tablename__ = "health_step_daily_summaries"

    id: Mapped[uuid.UUID] = uuid_pk()
    date: Mapped[date | None] = mapped_column(Date, index=True)
    day_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    step_count: Mapped[int | None] = mapped_column(Integer)
    walk_step_count: Mapped[int | None] = mapped_column(Integer)
    run_step_count: Mapped[int | None] = mapped_column(Integer)
    healthy_step: Mapped[int | None] = mapped_column(Integer)
    active_time_seconds: Mapped[int | None] = mapped_column(Integer)
    distance_meters: Mapped[float | None] = mapped_column(Float)
    calories: Mapped[float | None] = mapped_column(Float)
    speed: Mapped[float | None] = mapped_column(Float)
    achievement: Mapped[float | None] = mapped_column(Float)
    recommendation: Mapped[str | None] = mapped_column(Text)
    binning_data_ref: Mapped[str | None] = mapped_column(String(500))
    source_package_name: Mapped[str | None] = mapped_column(String(255))
    package_name: Mapped[str | None] = mapped_column(String(255))
    create_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    update_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    raw_extra: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    __table_args__ = (
        UniqueConstraint("user_id", "date", "datauuid", name="uq_step_daily_user_date_datauuid"),
        UniqueConstraint("user_id", "date", "source_file", name="uq_step_daily_fallback"),
        Index("ix_step_daily_user_date", "user_id", "date"),
    )


class HealthStepTrendSample(TimestampMixin, Base):
    __tablename__ = "health_step_trend_samples"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    import_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("health_imports.id", ondelete="SET NULL"), index=True
    )
    source: Mapped[str] = mapped_column(String(80), default="samsung_health_export", nullable=False)
    parent_datauuid: Mapped[str | None] = mapped_column(String(255), index=True)
    source_json_file: Mapped[str | None] = mapped_column(String(1000))
    sample_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    time_unit: Mapped[str | None] = mapped_column(String(100))
    steps: Mapped[int | None] = mapped_column(Integer)
    walk_step_count: Mapped[int | None] = mapped_column(Integer)
    run_step_count: Mapped[int | None] = mapped_column(Integer)
    distance_meters: Mapped[float | None] = mapped_column(Float)
    calories: Mapped[float | None] = mapped_column(Float)
    speed: Mapped[float | None] = mapped_column(Float)
    raw_extra: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    __table_args__ = (
        UniqueConstraint("user_id", "parent_datauuid", "sample_time", name="uq_step_trend_parent_time"),
        UniqueConstraint("user_id", "source_json_file", "time_unit", name="uq_step_trend_fallback"),
        Index("ix_step_trend_user_time", "user_id", "sample_time"),
    )


class HealthStressPeriod(HealthUserImportMixin, TimestampMixin, Base):
    __tablename__ = "health_stress_periods"

    id: Mapped[uuid.UUID] = uuid_pk()
    package_name: Mapped[str | None] = mapped_column(String(255))
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    score: Mapped[float | None] = mapped_column(Float)
    min_score: Mapped[float | None] = mapped_column(Float)
    max_score: Mapped[float | None] = mapped_column(Float)
    algorithm: Mapped[str | None] = mapped_column(String(255))
    tag_id: Mapped[str | None] = mapped_column(String(255))
    binning_data_ref: Mapped[str | None] = mapped_column(String(500))
    time_offset_ms: Mapped[int | None] = mapped_column(Integer)
    create_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    update_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    raw_extra: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    __table_args__ = (
        UniqueConstraint("user_id", "datauuid", name="uq_stress_period_user_datauuid"),
        UniqueConstraint("user_id", "start_time", "end_time", "score", "source_file", name="uq_stress_period_fallback"),
        Index("ix_stress_period_user_start", "user_id", "start_time"),
    )


class HealthStressSample(TimestampMixin, Base):
    __tablename__ = "health_stress_samples"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    import_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("health_imports.id", ondelete="SET NULL"), index=True
    )
    source: Mapped[str] = mapped_column(String(80), default="samsung_health_export", nullable=False)
    parent_datauuid: Mapped[str | None] = mapped_column(String(255), index=True)
    source_json_file: Mapped[str | None] = mapped_column(String(1000))
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    score: Mapped[float | None] = mapped_column(Float)
    min_score: Mapped[float | None] = mapped_column(Float)
    max_score: Mapped[float | None] = mapped_column(Float)
    level: Mapped[str | None] = mapped_column(String(100))
    flag: Mapped[str | None] = mapped_column(String(100))
    raw_extra: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    __table_args__ = (
        UniqueConstraint("user_id", "parent_datauuid", "start_time", "end_time", name="uq_stress_sample_identity"),
        Index("ix_stress_sample_user_start", "user_id", "start_time"),
    )


class HealthStressHistogram(HealthUserImportMixin, TimestampMixin, Base):
    __tablename__ = "health_stress_histograms"

    id: Mapped[uuid.UUID] = uuid_pk()
    base_hr: Mapped[float | None] = mapped_column(Float)
    histogram_ref: Mapped[str | None] = mapped_column(String(500))
    decay_time: Mapped[float | None] = mapped_column(Float)
    values_json: Mapped[list[Any] | None] = mapped_column(JSONB)
    version: Mapped[int | None] = mapped_column(Integer)
    source_json_file: Mapped[str | None] = mapped_column(String(1000))
    raw_extra: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    __table_args__ = (UniqueConstraint("user_id", "datauuid", name="uq_stress_hist_user_datauuid"),)


class HealthActivityDaySummary(HealthUserImportMixin, TimestampMixin, Base):
    __tablename__ = "health_activity_day_summaries"

    id: Mapped[uuid.UUID] = uuid_pk()
    date: Mapped[date | None] = mapped_column(Date, index=True)
    day_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    step_count: Mapped[int | None] = mapped_column(Integer)
    distance_meters: Mapped[float | None] = mapped_column(Float)
    calories: Mapped[float | None] = mapped_column(Float)
    active_time_seconds: Mapped[int | None] = mapped_column(Integer)
    walk_time_seconds: Mapped[int | None] = mapped_column(Integer)
    run_time_seconds: Mapped[int | None] = mapped_column(Integer)
    exercise_time_seconds: Mapped[int | None] = mapped_column(Integer)
    dynamic_active_time_seconds: Mapped[int | None] = mapped_column(Integer)
    longest_active_time_seconds: Mapped[int | None] = mapped_column(Integer)
    longest_idle_time_seconds: Mapped[int | None] = mapped_column(Integer)
    move_hourly_count: Mapped[int | None] = mapped_column(Integer)
    floor_count: Mapped[int | None] = mapped_column(Integer)
    score: Mapped[float | None] = mapped_column(Float)
    goal: Mapped[float | None] = mapped_column(Float)
    target: Mapped[float | None] = mapped_column(Float)
    movement_type: Mapped[str | None] = mapped_column(String(100))
    energy_type: Mapped[str | None] = mapped_column(String(100))
    extra_data_ref: Mapped[str | None] = mapped_column(String(500))
    raw_extra: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    __table_args__ = (
        UniqueConstraint("user_id", "date", "datauuid", name="uq_activity_day_user_date_datauuid"),
        UniqueConstraint("user_id", "date", "source_file", name="uq_activity_day_fallback"),
        Index("ix_activity_day_user_date", "user_id", "date"),
    )


class HealthActivityExtraData(CreatedAtMixin, Base):
    __tablename__ = "health_activity_extra_data"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    import_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("health_imports.id", ondelete="SET NULL"), index=True
    )
    source: Mapped[str] = mapped_column(String(80), default="samsung_health_export", nullable=False)
    parent_datauuid: Mapped[str | None] = mapped_column(String(255), index=True)
    source_json_file: Mapped[str | None] = mapped_column(String(1000))
    most_active_minutes: Mapped[int | None] = mapped_column(Integer)
    activity_list: Mapped[Any | None] = mapped_column(JSONB)
    unit_data_list: Mapped[Any | None] = mapped_column(JSONB)
    is_goal_achieved: Mapped[bool | None] = mapped_column(Boolean)
    streak_day_count: Mapped[int | None] = mapped_column(Integer)
    adaptive_goal: Mapped[Any | None] = mapped_column(JSONB)
    version: Mapped[int | None] = mapped_column(Integer)
    raw_extra: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    __table_args__ = (UniqueConstraint("user_id", "parent_datauuid", name="uq_activity_extra_parent"),)


class HealthActivityLevelRecord(HealthUserImportMixin, CreatedAtMixin, Base):
    __tablename__ = "health_activity_level_records"

    id: Mapped[uuid.UUID] = uuid_pk()
    package_name: Mapped[str | None] = mapped_column(String(255))
    activity_level: Mapped[int | None] = mapped_column(Integer)
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    time_offset_ms: Mapped[int | None] = mapped_column(Integer)
    create_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    update_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    raw_extra: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    __table_args__ = (
        UniqueConstraint("user_id", "datauuid", name="uq_activity_level_user_datauuid"),
        Index("ix_activity_level_user_start", "user_id", "start_time"),
    )


class HealthExerciseSession(HealthUserImportMixin, TimestampMixin, Base):
    __tablename__ = "health_exercise_sessions"

    id: Mapped[uuid.UUID] = uuid_pk()
    package_name: Mapped[str | None] = mapped_column(String(255))
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    exercise_type: Mapped[str | None] = mapped_column(String(100))
    exercise_custom_type: Mapped[str | None] = mapped_column(String(100))
    calories: Mapped[float | None] = mapped_column(Float)
    distance_meters: Mapped[float | None] = mapped_column(Float)
    count: Mapped[float | None] = mapped_column(Float)
    count_type: Mapped[str | None] = mapped_column(String(100))
    mean_heart_rate: Mapped[float | None] = mapped_column(Float)
    min_heart_rate: Mapped[float | None] = mapped_column(Float)
    max_heart_rate: Mapped[float | None] = mapped_column(Float)
    mean_speed: Mapped[float | None] = mapped_column(Float)
    max_speed: Mapped[float | None] = mapped_column(Float)
    mean_cadence: Mapped[float | None] = mapped_column(Float)
    max_cadence: Mapped[float | None] = mapped_column(Float)
    mean_power: Mapped[float | None] = mapped_column(Float)
    max_power: Mapped[float | None] = mapped_column(Float)
    vo2_max: Mapped[float | None] = mapped_column(Float)
    altitude_gain: Mapped[float | None] = mapped_column(Float)
    altitude_loss: Mapped[float | None] = mapped_column(Float)
    max_altitude: Mapped[float | None] = mapped_column(Float)
    min_altitude: Mapped[float | None] = mapped_column(Float)
    incline_distance: Mapped[float | None] = mapped_column(Float)
    decline_distance: Mapped[float | None] = mapped_column(Float)
    sweat_loss: Mapped[float | None] = mapped_column(Float)
    live_data_ref: Mapped[str | None] = mapped_column(String(500))
    location_data_ref: Mapped[str | None] = mapped_column(String(500))
    additional_ref: Mapped[str | None] = mapped_column(String(500))
    auxiliary_devices: Mapped[Any | None] = mapped_column(JSONB)
    create_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    update_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    raw_extra: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    __table_args__ = (
        UniqueConstraint("user_id", "datauuid", name="uq_exercise_user_datauuid"),
        UniqueConstraint("user_id", "start_time", "end_time", "exercise_type", name="uq_exercise_fallback"),
        Index("ix_exercise_user_start", "user_id", "start_time"),
    )


class HealthExerciseLiveSample(CreatedAtMixin, Base):
    __tablename__ = "health_exercise_live_samples"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    import_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("health_imports.id", ondelete="SET NULL"), index=True
    )
    source: Mapped[str] = mapped_column(String(80), default="samsung_health_export", nullable=False)
    parent_datauuid: Mapped[str | None] = mapped_column(String(255), index=True)
    source_json_file: Mapped[str | None] = mapped_column(String(1000))
    sample_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    heart_rate: Mapped[float | None] = mapped_column(Float)
    speed: Mapped[float | None] = mapped_column(Float)
    distance_meters: Mapped[float | None] = mapped_column(Float)
    cadence: Mapped[float | None] = mapped_column(Float)
    raw_extra: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    __table_args__ = (
        UniqueConstraint("user_id", "parent_datauuid", "sample_time", name="uq_exercise_live_parent_time"),
        Index("ix_exercise_live_user_time", "user_id", "sample_time"),
    )


class HealthSleepSession(HealthUserImportMixin, TimestampMixin, Base):
    __tablename__ = "health_sleep_sessions"

    id: Mapped[uuid.UUID] = uuid_pk()
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    sleep_score: Mapped[float | None] = mapped_column(Float)
    efficiency: Mapped[float | None] = mapped_column(Float)
    raw_stage_summary: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    raw_extra: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    __table_args__ = (
        UniqueConstraint("user_id", "datauuid", name="uq_sleep_session_user_datauuid"),
        UniqueConstraint("user_id", "start_time", "end_time", "source", name="uq_sleep_session_fallback"),
        Index("ix_sleep_session_user_start", "user_id", "start_time"),
    )


class HealthSleepStage(CreatedAtMixin, Base):
    __tablename__ = "health_sleep_stages"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    import_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("health_imports.id", ondelete="SET NULL"), index=True
    )
    sleep_session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("health_sleep_sessions.id", ondelete="SET NULL"), index=True
    )
    datauuid: Mapped[str | None] = mapped_column(String(255), index=True)
    deviceuuid: Mapped[str | None] = mapped_column(String(255), index=True)
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    stage: Mapped[str | None] = mapped_column(String(100))
    stage_code: Mapped[str | None] = mapped_column(String(100))
    raw_extra: Mapped[dict[str, Any] | None] = mapped_column(JSONB)


class HealthBodyMeasurement(HealthUserImportMixin, TimestampMixin, Base):
    __tablename__ = "health_body_measurements"

    id: Mapped[uuid.UUID] = uuid_pk()
    measurement_type: Mapped[str] = mapped_column(String(50), nullable=False)
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    height_cm: Mapped[float | None] = mapped_column(Float)
    weight_kg: Mapped[float | None] = mapped_column(Float)
    body_fat_percent: Mapped[float | None] = mapped_column(Float)
    body_fat_mass: Mapped[float | None] = mapped_column(Float)
    skeletal_muscle: Mapped[float | None] = mapped_column(Float)
    skeletal_muscle_mass: Mapped[float | None] = mapped_column(Float)
    muscle_mass: Mapped[float | None] = mapped_column(Float)
    basal_metabolic_rate: Mapped[float | None] = mapped_column(Float)
    total_body_water: Mapped[float | None] = mapped_column(Float)
    fat_free: Mapped[float | None] = mapped_column(Float)
    fat_free_mass: Mapped[float | None] = mapped_column(Float)
    vfa_level: Mapped[float | None] = mapped_column(Float)
    raw_extra: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    __table_args__ = (
        UniqueConstraint("user_id", "measurement_type", "start_time", "datauuid", name="uq_body_measurement_identity"),
        Index("ix_body_measurement_user_start", "user_id", "start_time"),
    )


class HealthUserProfileEntry(HealthUserImportMixin, TimestampMixin, Base):
    __tablename__ = "health_user_profile_entries"

    id: Mapped[uuid.UUID] = uuid_pk()
    profile_key: Mapped[str | None] = mapped_column(String(255), index=True)
    value_type: Mapped[str | None] = mapped_column(String(50))
    value_text: Mapped[str | None] = mapped_column(Text)
    value_number: Mapped[float | None] = mapped_column(Float)
    value_json: Mapped[Any | None] = mapped_column(JSONB)
    create_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    update_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    raw_extra: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    __table_args__ = (UniqueConstraint("user_id", "profile_key", "datauuid", name="uq_user_profile_entry_identity"),)


class HealthDeviceProfile(HealthUserImportMixin, TimestampMixin, Base):
    __tablename__ = "health_device_profiles"

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str | None] = mapped_column(String(255))
    manufacturer: Mapped[str | None] = mapped_column(String(255))
    model: Mapped[str | None] = mapped_column(String(255))
    fixed_name: Mapped[str | None] = mapped_column(String(255))
    device_group: Mapped[str | None] = mapped_column(String(100))
    device_type: Mapped[str | None] = mapped_column(String(100))
    connectivity_type: Mapped[str | None] = mapped_column(String(100))
    accessory_type: Mapped[str | None] = mapped_column(String(100))
    step_source_group: Mapped[str | None] = mapped_column(String(100))
    providing_step_goal: Mapped[bool | None] = mapped_column(Boolean)
    backsync_step_goal: Mapped[bool | None] = mapped_column(Boolean)
    capability_ref: Mapped[str | None] = mapped_column(String(500))
    capability_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    create_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    update_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    raw_extra: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    __table_args__ = (UniqueConstraint("user_id", "deviceuuid", name="uq_device_profile_user_deviceuuid"),)


class HealthDailySummary(TimestampMixin, Base):
    __tablename__ = "health_daily_summaries"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    import_ids: Mapped[list[str] | None] = mapped_column(JSONB)
    steps: Mapped[int | None] = mapped_column(Integer)
    walking_steps: Mapped[int | None] = mapped_column(Integer)
    running_steps: Mapped[int | None] = mapped_column(Integer)
    distance_meters: Mapped[float | None] = mapped_column(Float)
    calories: Mapped[float | None] = mapped_column(Float)
    active_time_seconds: Mapped[int | None] = mapped_column(Integer)
    walk_time_seconds: Mapped[int | None] = mapped_column(Integer)
    run_time_seconds: Mapped[int | None] = mapped_column(Integer)
    exercise_time_seconds: Mapped[int | None] = mapped_column(Integer)
    floor_count: Mapped[int | None] = mapped_column(Integer)
    stand_time_seconds: Mapped[int | None] = mapped_column(Integer)
    avg_heart_rate: Mapped[float | None] = mapped_column(Float)
    min_heart_rate: Mapped[float | None] = mapped_column(Float)
    max_heart_rate: Mapped[float | None] = mapped_column(Float)
    heart_rate_sample_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    high_bpm_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    low_bpm_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    stress_avg_score: Mapped[float | None] = mapped_column(Float)
    stress_min_score: Mapped[float | None] = mapped_column(Float)
    stress_max_score: Mapped[float | None] = mapped_column(Float)
    stress_sample_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    exercise_sessions_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    exercise_calories: Mapped[float | None] = mapped_column(Float)
    sleep_minutes: Mapped[int | None] = mapped_column(Integer)
    sleep_score: Mapped[float | None] = mapped_column(Float)
    data_sources: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    data_quality: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    ai_twin_notes: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_health_daily_user_date"),
        Index("ix_health_daily_user_date", "user_id", "date"),
        Index("ix_health_daily_user_avg_hr", "user_id", "avg_heart_rate"),
        Index("ix_health_daily_user_steps", "user_id", "steps"),
    )


class HealthAiTwinProfile(TimestampMixin, Base):
    __tablename__ = "health_ai_twin_profiles"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )
    readiness_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    readiness_level: Mapped[str] = mapped_column(String(50), default="low", nullable=False)
    available_data_types: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    missing_data_types: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    date_range_start: Mapped[date | None] = mapped_column(Date)
    date_range_end: Mapped[date | None] = mapped_column(Date)
    baseline_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    patterns_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    warnings: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    last_computed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
