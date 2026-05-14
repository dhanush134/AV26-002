"""add health samsung import tables

Revision ID: 20260514_0002
Revises: 20260514_0001
Create Date: 2026-05-14 00:02:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260514_0002"
down_revision: Union[str, None] = "20260514_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


UUID = postgresql.UUID(as_uuid=True)
JSONB = postgresql.JSONB(astext_type=sa.Text())


def id_col() -> sa.Column:
    return sa.Column("id", UUID, nullable=False)


def timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    ]


def created_at() -> sa.Column:
    return sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False)


def user_fk() -> sa.Column:
    return sa.Column("user_id", UUID, nullable=False)


def import_fk(nullable: bool = True) -> sa.Column:
    return sa.Column("import_id", UUID, nullable=nullable)


def source_cols(include_datauuid: bool = True) -> list[sa.Column]:
    cols = [
        sa.Column("source", sa.String(length=80), server_default="samsung_health_export", nullable=False),
        sa.Column("source_file", sa.String(length=1000), nullable=True),
    ]
    if include_datauuid:
        cols.extend(
            [
                sa.Column("datauuid", sa.String(length=255), nullable=True),
                sa.Column("deviceuuid", sa.String(length=255), nullable=True),
            ]
        )
    return cols


def fk_constraints(import_delete: str = "SET NULL") -> list:
    return [
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["import_id"], ["health_imports.id"], ondelete=import_delete),
    ]


def pk() -> sa.PrimaryKeyConstraint:
    return sa.PrimaryKeyConstraint("id")


def upgrade() -> None:
    op.create_table(
        "health_imports",
        id_col(),
        user_fk(),
        sa.Column("source", sa.String(length=80), server_default="samsung_health_export", nullable=False),
        sa.Column("original_filename", sa.String(length=500), nullable=True),
        sa.Column("file_sha256", sa.String(length=64), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("import_status", sa.String(length=50), server_default="parsed", nullable=False),
        sa.Column("detected_data", JSONB, nullable=True),
        sa.Column("files_processed", JSONB, nullable=True),
        sa.Column("warnings", JSONB, nullable=True),
        sa.Column("errors", JSONB, nullable=True),
        sa.Column("record_counts", JSONB, nullable=True),
        sa.Column("imported_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        pk(),
        sa.UniqueConstraint("user_id", "file_sha256", name="uq_health_import_user_file_sha"),
    )
    op.create_index("ix_health_imports_user_id", "health_imports", ["user_id"])
    op.create_index("ix_health_imports_file_sha256", "health_imports", ["file_sha256"])

    op.create_table(
        "health_import_files",
        id_col(),
        import_fk(nullable=False),
        user_fk(),
        sa.Column("path", sa.String(length=1000), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("file_type", sa.String(length=20), server_default="unknown", nullable=False),
        sa.Column("row_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("parsed_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("warning_count", sa.Integer(), server_default="0", nullable=False),
        created_at(),
        *fk_constraints(import_delete="CASCADE"),
        pk(),
    )
    op.create_index("ix_health_import_files_import_id", "health_import_files", ["import_id"])
    op.create_index("ix_health_import_files_user_id", "health_import_files", ["user_id"])

    op.create_table(
        "health_heart_rate_periods",
        id_col(),
        user_fk(),
        import_fk(),
        *source_cols(),
        sa.Column("package_name", sa.String(length=255), nullable=True),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("avg_bpm", sa.Float(), nullable=True),
        sa.Column("min_bpm", sa.Float(), nullable=True),
        sa.Column("max_bpm", sa.Float(), nullable=True),
        sa.Column("heart_beat_count", sa.Integer(), nullable=True),
        sa.Column("binning_data_ref", sa.String(length=500), nullable=True),
        sa.Column("time_offset_ms", sa.Integer(), nullable=True),
        sa.Column("create_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("update_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_extra", JSONB, nullable=True),
        *timestamps(),
        *fk_constraints(),
        pk(),
        sa.UniqueConstraint("user_id", "datauuid", name="uq_hr_period_user_datauuid"),
        sa.UniqueConstraint("user_id", "source_file", "start_time", "end_time", "avg_bpm", name="uq_hr_period_fallback"),
    )
    op.create_index("ix_hr_period_user_start", "health_heart_rate_periods", ["user_id", "start_time"])
    op.create_index("ix_health_heart_rate_periods_import_id", "health_heart_rate_periods", ["import_id"])
    op.create_index("ix_health_heart_rate_periods_deviceuuid", "health_heart_rate_periods", ["deviceuuid"])
    op.create_index("ix_health_heart_rate_periods_datauuid", "health_heart_rate_periods", ["datauuid"])
    op.create_index("ix_health_heart_rate_periods_start_time", "health_heart_rate_periods", ["start_time"])
    op.create_index("ix_health_heart_rate_periods_end_time", "health_heart_rate_periods", ["end_time"])

    op.create_table(
        "health_heart_rate_samples",
        id_col(),
        user_fk(),
        import_fk(),
        sa.Column("parent_period_id", UUID, nullable=True),
        sa.Column("parent_datauuid", sa.String(length=255), nullable=True),
        sa.Column("parent_binning_data_ref", sa.String(length=500), nullable=True),
        sa.Column("source", sa.String(length=80), server_default="samsung_health_export", nullable=False),
        sa.Column("source_json_file", sa.String(length=1000), nullable=True),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("bpm", sa.Float(), nullable=True),
        sa.Column("min_bpm", sa.Float(), nullable=True),
        sa.Column("max_bpm", sa.Float(), nullable=True),
        sa.Column("raw_extra", JSONB, nullable=True),
        *timestamps(),
        *fk_constraints(),
        sa.ForeignKeyConstraint(["parent_period_id"], ["health_heart_rate_periods.id"], ondelete="SET NULL"),
        pk(),
        sa.UniqueConstraint("user_id", "parent_datauuid", "start_time", "end_time", "bpm", name="uq_hr_sample_identity"),
    )
    for name, cols in {
        "ix_hr_sample_user_start": ["user_id", "start_time"],
        "ix_hr_sample_user_bpm": ["user_id", "bpm"],
        "ix_hr_sample_user_start_bpm": ["user_id", "start_time", "bpm"],
        "ix_health_heart_rate_samples_parent_period_id": ["parent_period_id"],
        "ix_health_heart_rate_samples_parent_datauuid": ["parent_datauuid"],
        "ix_health_heart_rate_samples_import_id": ["import_id"],
        "ix_health_heart_rate_samples_start_time": ["start_time"],
        "ix_health_heart_rate_samples_end_time": ["end_time"],
        "ix_health_heart_rate_samples_bpm": ["bpm"],
    }.items():
        op.create_index(name, "health_heart_rate_samples", cols)

    op.create_table(
        "health_step_intervals",
        id_col(),
        user_fk(),
        import_fk(),
        *source_cols(),
        sa.Column("package_name", sa.String(length=255), nullable=True),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("steps", sa.Integer(), nullable=True),
        sa.Column("distance_meters", sa.Float(), nullable=True),
        sa.Column("calories", sa.Float(), nullable=True),
        sa.Column("speed", sa.Float(), nullable=True),
        sa.Column("sample_position_type", sa.Integer(), nullable=True),
        sa.Column("time_offset_ms", sa.Integer(), nullable=True),
        sa.Column("create_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("update_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_extra", JSONB, nullable=True),
        *timestamps(),
        *fk_constraints(),
        pk(),
        sa.UniqueConstraint("user_id", "datauuid", name="uq_step_interval_user_datauuid"),
        sa.UniqueConstraint("user_id", "start_time", "end_time", "steps", "source_file", name="uq_step_interval_fallback"),
    )
    for name, cols in {
        "ix_step_interval_user_start": ["user_id", "start_time"],
        "ix_health_step_intervals_import_id": ["import_id"],
        "ix_health_step_intervals_datauuid": ["datauuid"],
        "ix_health_step_intervals_deviceuuid": ["deviceuuid"],
        "ix_health_step_intervals_start_time": ["start_time"],
        "ix_health_step_intervals_end_time": ["end_time"],
    }.items():
        op.create_index(name, "health_step_intervals", cols)

    op.create_table(
        "health_step_daily_summaries",
        id_col(),
        user_fk(),
        import_fk(),
        *source_cols(),
        sa.Column("date", sa.Date(), nullable=True),
        sa.Column("day_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("step_count", sa.Integer(), nullable=True),
        sa.Column("walk_step_count", sa.Integer(), nullable=True),
        sa.Column("run_step_count", sa.Integer(), nullable=True),
        sa.Column("healthy_step", sa.Integer(), nullable=True),
        sa.Column("active_time_seconds", sa.Integer(), nullable=True),
        sa.Column("distance_meters", sa.Float(), nullable=True),
        sa.Column("calories", sa.Float(), nullable=True),
        sa.Column("speed", sa.Float(), nullable=True),
        sa.Column("achievement", sa.Float(), nullable=True),
        sa.Column("recommendation", sa.Text(), nullable=True),
        sa.Column("binning_data_ref", sa.String(length=500), nullable=True),
        sa.Column("source_package_name", sa.String(length=255), nullable=True),
        sa.Column("package_name", sa.String(length=255), nullable=True),
        sa.Column("create_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("update_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_extra", JSONB, nullable=True),
        *timestamps(),
        *fk_constraints(),
        pk(),
        sa.UniqueConstraint("user_id", "date", "datauuid", name="uq_step_daily_user_date_datauuid"),
        sa.UniqueConstraint("user_id", "date", "source_file", name="uq_step_daily_fallback"),
    )
    op.create_index("ix_step_daily_user_date", "health_step_daily_summaries", ["user_id", "date"])
    op.create_index("ix_health_step_daily_summaries_date", "health_step_daily_summaries", ["date"])
    op.create_index("ix_health_step_daily_summaries_import_id", "health_step_daily_summaries", ["import_id"])

    op.create_table(
        "health_step_trend_samples",
        id_col(),
        user_fk(),
        import_fk(),
        sa.Column("source", sa.String(length=80), server_default="samsung_health_export", nullable=False),
        sa.Column("parent_datauuid", sa.String(length=255), nullable=True),
        sa.Column("source_json_file", sa.String(length=1000), nullable=True),
        sa.Column("sample_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("time_unit", sa.String(length=100), nullable=True),
        sa.Column("steps", sa.Integer(), nullable=True),
        sa.Column("walk_step_count", sa.Integer(), nullable=True),
        sa.Column("run_step_count", sa.Integer(), nullable=True),
        sa.Column("distance_meters", sa.Float(), nullable=True),
        sa.Column("calories", sa.Float(), nullable=True),
        sa.Column("speed", sa.Float(), nullable=True),
        sa.Column("raw_extra", JSONB, nullable=True),
        *timestamps(),
        *fk_constraints(),
        pk(),
        sa.UniqueConstraint("user_id", "parent_datauuid", "sample_time", name="uq_step_trend_parent_time"),
        sa.UniqueConstraint("user_id", "source_json_file", "time_unit", name="uq_step_trend_fallback"),
    )
    op.create_index("ix_step_trend_user_time", "health_step_trend_samples", ["user_id", "sample_time"])
    op.create_index("ix_health_step_trend_samples_parent_datauuid", "health_step_trend_samples", ["parent_datauuid"])
    op.create_index("ix_health_step_trend_samples_import_id", "health_step_trend_samples", ["import_id"])
    op.create_index("ix_health_step_trend_samples_sample_time", "health_step_trend_samples", ["sample_time"])

    op.create_table(
        "health_stress_periods",
        id_col(),
        user_fk(),
        import_fk(),
        *source_cols(),
        sa.Column("package_name", sa.String(length=255), nullable=True),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("min_score", sa.Float(), nullable=True),
        sa.Column("max_score", sa.Float(), nullable=True),
        sa.Column("algorithm", sa.String(length=255), nullable=True),
        sa.Column("tag_id", sa.String(length=255), nullable=True),
        sa.Column("binning_data_ref", sa.String(length=500), nullable=True),
        sa.Column("time_offset_ms", sa.Integer(), nullable=True),
        sa.Column("create_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("update_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_extra", JSONB, nullable=True),
        *timestamps(),
        *fk_constraints(),
        pk(),
        sa.UniqueConstraint("user_id", "datauuid", name="uq_stress_period_user_datauuid"),
        sa.UniqueConstraint("user_id", "start_time", "end_time", "score", "source_file", name="uq_stress_period_fallback"),
    )
    op.create_index("ix_stress_period_user_start", "health_stress_periods", ["user_id", "start_time"])
    op.create_index("ix_health_stress_periods_import_id", "health_stress_periods", ["import_id"])
    op.create_index("ix_health_stress_periods_start_time", "health_stress_periods", ["start_time"])
    op.create_index("ix_health_stress_periods_end_time", "health_stress_periods", ["end_time"])

    op.create_table(
        "health_stress_samples",
        id_col(),
        user_fk(),
        import_fk(),
        sa.Column("source", sa.String(length=80), server_default="samsung_health_export", nullable=False),
        sa.Column("parent_datauuid", sa.String(length=255), nullable=True),
        sa.Column("source_json_file", sa.String(length=1000), nullable=True),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("min_score", sa.Float(), nullable=True),
        sa.Column("max_score", sa.Float(), nullable=True),
        sa.Column("level", sa.String(length=100), nullable=True),
        sa.Column("flag", sa.String(length=100), nullable=True),
        sa.Column("raw_extra", JSONB, nullable=True),
        *timestamps(),
        *fk_constraints(),
        pk(),
        sa.UniqueConstraint("user_id", "parent_datauuid", "start_time", "end_time", name="uq_stress_sample_identity"),
    )
    op.create_index("ix_stress_sample_user_start", "health_stress_samples", ["user_id", "start_time"])
    op.create_index("ix_health_stress_samples_import_id", "health_stress_samples", ["import_id"])
    op.create_index("ix_health_stress_samples_parent_datauuid", "health_stress_samples", ["parent_datauuid"])
    op.create_index("ix_health_stress_samples_start_time", "health_stress_samples", ["start_time"])
    op.create_index("ix_health_stress_samples_end_time", "health_stress_samples", ["end_time"])

    op.create_table(
        "health_stress_histograms",
        id_col(),
        user_fk(),
        import_fk(),
        *source_cols(),
        sa.Column("base_hr", sa.Float(), nullable=True),
        sa.Column("histogram_ref", sa.String(length=500), nullable=True),
        sa.Column("decay_time", sa.Float(), nullable=True),
        sa.Column("values_json", JSONB, nullable=True),
        sa.Column("version", sa.Integer(), nullable=True),
        sa.Column("source_json_file", sa.String(length=1000), nullable=True),
        sa.Column("raw_extra", JSONB, nullable=True),
        *timestamps(),
        *fk_constraints(),
        pk(),
        sa.UniqueConstraint("user_id", "datauuid", name="uq_stress_hist_user_datauuid"),
    )
    op.create_index("ix_health_stress_histograms_import_id", "health_stress_histograms", ["import_id"])

    op.create_table(
        "health_activity_day_summaries",
        id_col(),
        user_fk(),
        import_fk(),
        *source_cols(),
        sa.Column("date", sa.Date(), nullable=True),
        sa.Column("day_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("step_count", sa.Integer(), nullable=True),
        sa.Column("distance_meters", sa.Float(), nullable=True),
        sa.Column("calories", sa.Float(), nullable=True),
        sa.Column("active_time_seconds", sa.Integer(), nullable=True),
        sa.Column("walk_time_seconds", sa.Integer(), nullable=True),
        sa.Column("run_time_seconds", sa.Integer(), nullable=True),
        sa.Column("exercise_time_seconds", sa.Integer(), nullable=True),
        sa.Column("dynamic_active_time_seconds", sa.Integer(), nullable=True),
        sa.Column("longest_active_time_seconds", sa.Integer(), nullable=True),
        sa.Column("longest_idle_time_seconds", sa.Integer(), nullable=True),
        sa.Column("move_hourly_count", sa.Integer(), nullable=True),
        sa.Column("floor_count", sa.Integer(), nullable=True),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("goal", sa.Float(), nullable=True),
        sa.Column("target", sa.Float(), nullable=True),
        sa.Column("movement_type", sa.String(length=100), nullable=True),
        sa.Column("energy_type", sa.String(length=100), nullable=True),
        sa.Column("extra_data_ref", sa.String(length=500), nullable=True),
        sa.Column("raw_extra", JSONB, nullable=True),
        *timestamps(),
        *fk_constraints(),
        pk(),
        sa.UniqueConstraint("user_id", "date", "datauuid", name="uq_activity_day_user_date_datauuid"),
        sa.UniqueConstraint("user_id", "date", "source_file", name="uq_activity_day_fallback"),
    )
    op.create_index("ix_activity_day_user_date", "health_activity_day_summaries", ["user_id", "date"])
    op.create_index("ix_health_activity_day_summaries_date", "health_activity_day_summaries", ["date"])
    op.create_index("ix_health_activity_day_summaries_import_id", "health_activity_day_summaries", ["import_id"])

    op.create_table(
        "health_activity_extra_data",
        id_col(),
        user_fk(),
        import_fk(),
        sa.Column("source", sa.String(length=80), server_default="samsung_health_export", nullable=False),
        sa.Column("parent_datauuid", sa.String(length=255), nullable=True),
        sa.Column("source_json_file", sa.String(length=1000), nullable=True),
        sa.Column("most_active_minutes", sa.Integer(), nullable=True),
        sa.Column("activity_list", JSONB, nullable=True),
        sa.Column("unit_data_list", JSONB, nullable=True),
        sa.Column("is_goal_achieved", sa.Boolean(), nullable=True),
        sa.Column("streak_day_count", sa.Integer(), nullable=True),
        sa.Column("adaptive_goal", JSONB, nullable=True),
        sa.Column("version", sa.Integer(), nullable=True),
        sa.Column("raw_extra", JSONB, nullable=True),
        created_at(),
        *fk_constraints(),
        pk(),
        sa.UniqueConstraint("user_id", "parent_datauuid", name="uq_activity_extra_parent"),
    )
    op.create_index("ix_health_activity_extra_data_parent_datauuid", "health_activity_extra_data", ["parent_datauuid"])
    op.create_index("ix_health_activity_extra_data_import_id", "health_activity_extra_data", ["import_id"])

    op.create_table(
        "health_activity_level_records",
        id_col(),
        user_fk(),
        import_fk(),
        *source_cols(),
        sa.Column("package_name", sa.String(length=255), nullable=True),
        sa.Column("activity_level", sa.Integer(), nullable=True),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("time_offset_ms", sa.Integer(), nullable=True),
        sa.Column("create_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("update_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_extra", JSONB, nullable=True),
        created_at(),
        *fk_constraints(),
        pk(),
        sa.UniqueConstraint("user_id", "datauuid", name="uq_activity_level_user_datauuid"),
    )
    op.create_index("ix_activity_level_user_start", "health_activity_level_records", ["user_id", "start_time"])
    op.create_index("ix_health_activity_level_records_start_time", "health_activity_level_records", ["start_time"])
    op.create_index("ix_health_activity_level_records_import_id", "health_activity_level_records", ["import_id"])

    op.create_table(
        "health_exercise_sessions",
        id_col(),
        user_fk(),
        import_fk(),
        *source_cols(),
        sa.Column("package_name", sa.String(length=255), nullable=True),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("exercise_type", sa.String(length=100), nullable=True),
        sa.Column("exercise_custom_type", sa.String(length=100), nullable=True),
        sa.Column("calories", sa.Float(), nullable=True),
        sa.Column("distance_meters", sa.Float(), nullable=True),
        sa.Column("count", sa.Float(), nullable=True),
        sa.Column("count_type", sa.String(length=100), nullable=True),
        sa.Column("mean_heart_rate", sa.Float(), nullable=True),
        sa.Column("min_heart_rate", sa.Float(), nullable=True),
        sa.Column("max_heart_rate", sa.Float(), nullable=True),
        sa.Column("mean_speed", sa.Float(), nullable=True),
        sa.Column("max_speed", sa.Float(), nullable=True),
        sa.Column("mean_cadence", sa.Float(), nullable=True),
        sa.Column("max_cadence", sa.Float(), nullable=True),
        sa.Column("mean_power", sa.Float(), nullable=True),
        sa.Column("max_power", sa.Float(), nullable=True),
        sa.Column("vo2_max", sa.Float(), nullable=True),
        sa.Column("altitude_gain", sa.Float(), nullable=True),
        sa.Column("altitude_loss", sa.Float(), nullable=True),
        sa.Column("max_altitude", sa.Float(), nullable=True),
        sa.Column("min_altitude", sa.Float(), nullable=True),
        sa.Column("incline_distance", sa.Float(), nullable=True),
        sa.Column("decline_distance", sa.Float(), nullable=True),
        sa.Column("sweat_loss", sa.Float(), nullable=True),
        sa.Column("live_data_ref", sa.String(length=500), nullable=True),
        sa.Column("location_data_ref", sa.String(length=500), nullable=True),
        sa.Column("additional_ref", sa.String(length=500), nullable=True),
        sa.Column("auxiliary_devices", JSONB, nullable=True),
        sa.Column("create_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("update_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_extra", JSONB, nullable=True),
        *timestamps(),
        *fk_constraints(),
        pk(),
        sa.UniqueConstraint("user_id", "datauuid", name="uq_exercise_user_datauuid"),
        sa.UniqueConstraint("user_id", "start_time", "end_time", "exercise_type", name="uq_exercise_fallback"),
    )
    op.create_index("ix_exercise_user_start", "health_exercise_sessions", ["user_id", "start_time"])
    op.create_index("ix_health_exercise_sessions_start_time", "health_exercise_sessions", ["start_time"])
    op.create_index("ix_health_exercise_sessions_end_time", "health_exercise_sessions", ["end_time"])
    op.create_index("ix_health_exercise_sessions_import_id", "health_exercise_sessions", ["import_id"])

    op.create_table(
        "health_exercise_live_samples",
        id_col(),
        user_fk(),
        import_fk(),
        sa.Column("source", sa.String(length=80), server_default="samsung_health_export", nullable=False),
        sa.Column("parent_datauuid", sa.String(length=255), nullable=True),
        sa.Column("source_json_file", sa.String(length=1000), nullable=True),
        sa.Column("sample_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("heart_rate", sa.Float(), nullable=True),
        sa.Column("speed", sa.Float(), nullable=True),
        sa.Column("distance_meters", sa.Float(), nullable=True),
        sa.Column("cadence", sa.Float(), nullable=True),
        sa.Column("raw_extra", JSONB, nullable=True),
        created_at(),
        *fk_constraints(),
        pk(),
        sa.UniqueConstraint("user_id", "parent_datauuid", "sample_time", name="uq_exercise_live_parent_time"),
    )
    op.create_index("ix_exercise_live_user_time", "health_exercise_live_samples", ["user_id", "sample_time"])
    op.create_index("ix_health_exercise_live_samples_sample_time", "health_exercise_live_samples", ["sample_time"])
    op.create_index("ix_health_exercise_live_samples_import_id", "health_exercise_live_samples", ["import_id"])

    op.create_table(
        "health_sleep_sessions",
        id_col(),
        user_fk(),
        import_fk(),
        *source_cols(),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("sleep_score", sa.Float(), nullable=True),
        sa.Column("efficiency", sa.Float(), nullable=True),
        sa.Column("raw_stage_summary", JSONB, nullable=True),
        sa.Column("raw_extra", JSONB, nullable=True),
        *timestamps(),
        *fk_constraints(),
        pk(),
        sa.UniqueConstraint("user_id", "datauuid", name="uq_sleep_session_user_datauuid"),
        sa.UniqueConstraint("user_id", "start_time", "end_time", "source", name="uq_sleep_session_fallback"),
    )
    op.create_index("ix_sleep_session_user_start", "health_sleep_sessions", ["user_id", "start_time"])
    op.create_index("ix_health_sleep_sessions_start_time", "health_sleep_sessions", ["start_time"])
    op.create_index("ix_health_sleep_sessions_end_time", "health_sleep_sessions", ["end_time"])
    op.create_index("ix_health_sleep_sessions_import_id", "health_sleep_sessions", ["import_id"])

    op.create_table(
        "health_sleep_stages",
        id_col(),
        user_fk(),
        import_fk(),
        sa.Column("sleep_session_id", UUID, nullable=True),
        sa.Column("datauuid", sa.String(length=255), nullable=True),
        sa.Column("deviceuuid", sa.String(length=255), nullable=True),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("stage", sa.String(length=100), nullable=True),
        sa.Column("stage_code", sa.String(length=100), nullable=True),
        sa.Column("raw_extra", JSONB, nullable=True),
        created_at(),
        *fk_constraints(),
        sa.ForeignKeyConstraint(["sleep_session_id"], ["health_sleep_sessions.id"], ondelete="SET NULL"),
        pk(),
    )
    op.create_index("ix_health_sleep_stages_sleep_session_id", "health_sleep_stages", ["sleep_session_id"])
    op.create_index("ix_health_sleep_stages_start_time", "health_sleep_stages", ["start_time"])
    op.create_index("ix_health_sleep_stages_end_time", "health_sleep_stages", ["end_time"])
    op.create_index("ix_health_sleep_stages_import_id", "health_sleep_stages", ["import_id"])

    op.create_table(
        "health_body_measurements",
        id_col(),
        user_fk(),
        import_fk(),
        *source_cols(),
        sa.Column("measurement_type", sa.String(length=50), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("height_cm", sa.Float(), nullable=True),
        sa.Column("weight_kg", sa.Float(), nullable=True),
        sa.Column("body_fat_percent", sa.Float(), nullable=True),
        sa.Column("body_fat_mass", sa.Float(), nullable=True),
        sa.Column("skeletal_muscle", sa.Float(), nullable=True),
        sa.Column("skeletal_muscle_mass", sa.Float(), nullable=True),
        sa.Column("muscle_mass", sa.Float(), nullable=True),
        sa.Column("basal_metabolic_rate", sa.Float(), nullable=True),
        sa.Column("total_body_water", sa.Float(), nullable=True),
        sa.Column("fat_free", sa.Float(), nullable=True),
        sa.Column("fat_free_mass", sa.Float(), nullable=True),
        sa.Column("vfa_level", sa.Float(), nullable=True),
        sa.Column("raw_extra", JSONB, nullable=True),
        *timestamps(),
        *fk_constraints(),
        pk(),
        sa.UniqueConstraint("user_id", "measurement_type", "start_time", "datauuid", name="uq_body_measurement_identity"),
    )
    op.create_index("ix_body_measurement_user_start", "health_body_measurements", ["user_id", "start_time"])
    op.create_index("ix_health_body_measurements_start_time", "health_body_measurements", ["start_time"])
    op.create_index("ix_health_body_measurements_import_id", "health_body_measurements", ["import_id"])

    op.create_table(
        "health_user_profile_entries",
        id_col(),
        user_fk(),
        import_fk(),
        *source_cols(),
        sa.Column("profile_key", sa.String(length=255), nullable=True),
        sa.Column("value_type", sa.String(length=50), nullable=True),
        sa.Column("value_text", sa.Text(), nullable=True),
        sa.Column("value_number", sa.Float(), nullable=True),
        sa.Column("value_json", JSONB, nullable=True),
        sa.Column("create_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("update_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_extra", JSONB, nullable=True),
        *timestamps(),
        *fk_constraints(),
        pk(),
        sa.UniqueConstraint("user_id", "profile_key", "datauuid", name="uq_user_profile_entry_identity"),
    )
    op.create_index("ix_health_user_profile_entries_profile_key", "health_user_profile_entries", ["profile_key"])
    op.create_index("ix_health_user_profile_entries_import_id", "health_user_profile_entries", ["import_id"])

    op.create_table(
        "health_device_profiles",
        id_col(),
        user_fk(),
        import_fk(),
        *source_cols(),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("manufacturer", sa.String(length=255), nullable=True),
        sa.Column("model", sa.String(length=255), nullable=True),
        sa.Column("fixed_name", sa.String(length=255), nullable=True),
        sa.Column("device_group", sa.String(length=100), nullable=True),
        sa.Column("device_type", sa.String(length=100), nullable=True),
        sa.Column("connectivity_type", sa.String(length=100), nullable=True),
        sa.Column("accessory_type", sa.String(length=100), nullable=True),
        sa.Column("step_source_group", sa.String(length=100), nullable=True),
        sa.Column("providing_step_goal", sa.Boolean(), nullable=True),
        sa.Column("backsync_step_goal", sa.Boolean(), nullable=True),
        sa.Column("capability_ref", sa.String(length=500), nullable=True),
        sa.Column("capability_json", JSONB, nullable=True),
        sa.Column("create_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("update_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_extra", JSONB, nullable=True),
        *timestamps(),
        *fk_constraints(),
        pk(),
        sa.UniqueConstraint("user_id", "deviceuuid", name="uq_device_profile_user_deviceuuid"),
    )
    op.create_index("ix_health_device_profiles_deviceuuid", "health_device_profiles", ["deviceuuid"])
    op.create_index("ix_health_device_profiles_import_id", "health_device_profiles", ["import_id"])

    op.create_table(
        "health_daily_summaries",
        id_col(),
        user_fk(),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("import_ids", JSONB, nullable=True),
        sa.Column("steps", sa.Integer(), nullable=True),
        sa.Column("walking_steps", sa.Integer(), nullable=True),
        sa.Column("running_steps", sa.Integer(), nullable=True),
        sa.Column("distance_meters", sa.Float(), nullable=True),
        sa.Column("calories", sa.Float(), nullable=True),
        sa.Column("active_time_seconds", sa.Integer(), nullable=True),
        sa.Column("walk_time_seconds", sa.Integer(), nullable=True),
        sa.Column("run_time_seconds", sa.Integer(), nullable=True),
        sa.Column("exercise_time_seconds", sa.Integer(), nullable=True),
        sa.Column("floor_count", sa.Integer(), nullable=True),
        sa.Column("stand_time_seconds", sa.Integer(), nullable=True),
        sa.Column("avg_heart_rate", sa.Float(), nullable=True),
        sa.Column("min_heart_rate", sa.Float(), nullable=True),
        sa.Column("max_heart_rate", sa.Float(), nullable=True),
        sa.Column("heart_rate_sample_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("high_bpm_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("low_bpm_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("stress_avg_score", sa.Float(), nullable=True),
        sa.Column("stress_min_score", sa.Float(), nullable=True),
        sa.Column("stress_max_score", sa.Float(), nullable=True),
        sa.Column("stress_sample_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("exercise_sessions_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("exercise_calories", sa.Float(), nullable=True),
        sa.Column("sleep_minutes", sa.Integer(), nullable=True),
        sa.Column("sleep_score", sa.Float(), nullable=True),
        sa.Column("data_sources", JSONB, server_default="[]", nullable=False),
        sa.Column("data_quality", JSONB, server_default="{}", nullable=False),
        sa.Column("ai_twin_notes", JSONB, nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        pk(),
        sa.UniqueConstraint("user_id", "date", name="uq_health_daily_user_date"),
    )
    op.create_index("ix_health_daily_user_date", "health_daily_summaries", ["user_id", "date"])
    op.create_index("ix_health_daily_user_avg_hr", "health_daily_summaries", ["user_id", "avg_heart_rate"])
    op.create_index("ix_health_daily_user_steps", "health_daily_summaries", ["user_id", "steps"])
    op.create_index("ix_health_daily_summaries_date", "health_daily_summaries", ["date"])

    op.create_table(
        "health_ai_twin_profiles",
        id_col(),
        user_fk(),
        sa.Column("readiness_score", sa.Integer(), server_default="0", nullable=False),
        sa.Column("readiness_level", sa.String(length=50), server_default="low", nullable=False),
        sa.Column("available_data_types", JSONB, server_default="[]", nullable=False),
        sa.Column("missing_data_types", JSONB, server_default="[]", nullable=False),
        sa.Column("date_range_start", sa.Date(), nullable=True),
        sa.Column("date_range_end", sa.Date(), nullable=True),
        sa.Column("baseline_json", JSONB, server_default="{}", nullable=False),
        sa.Column("patterns_json", JSONB, server_default="{}", nullable=False),
        sa.Column("warnings", JSONB, server_default="[]", nullable=False),
        sa.Column("last_computed_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        pk(),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_health_ai_twin_profiles_user_id", "health_ai_twin_profiles", ["user_id"], unique=True)


def downgrade() -> None:
    for table in (
        "health_ai_twin_profiles",
        "health_daily_summaries",
        "health_device_profiles",
        "health_user_profile_entries",
        "health_body_measurements",
        "health_sleep_stages",
        "health_sleep_sessions",
        "health_exercise_live_samples",
        "health_exercise_sessions",
        "health_activity_level_records",
        "health_activity_extra_data",
        "health_activity_day_summaries",
        "health_stress_histograms",
        "health_stress_samples",
        "health_stress_periods",
        "health_step_trend_samples",
        "health_step_daily_summaries",
        "health_step_intervals",
        "health_heart_rate_samples",
        "health_heart_rate_periods",
        "health_import_files",
        "health_imports",
    ):
        op.drop_table(table)
