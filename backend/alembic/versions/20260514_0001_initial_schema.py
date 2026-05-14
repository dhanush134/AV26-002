"""initial schema

Revision ID: 20260514_0001
Revises:
Create Date: 2026-05-14 00:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260514_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("age", sa.Integer(), nullable=False),
        sa.Column("gender", sa.String(length=50), nullable=True),
        sa.Column("height_cm", sa.Float(), nullable=False),
        sa.Column("weight_kg", sa.Float(), nullable=False),
        sa.Column("target_age", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "lifestyle_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("smoking_status", sa.String(length=100), nullable=True),
        sa.Column("alcohol_frequency", sa.String(length=100), nullable=True),
        sa.Column("exercise_frequency", sa.String(length=100), nullable=True),
        sa.Column("diet_quality", sa.String(length=100), nullable=True),
        sa.Column("stress_level", sa.String(length=100), nullable=True),
        sa.Column("sleep_goal_hours", sa.Float(), nullable=True),
        sa.Column("medical_conditions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("family_history", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(op.f("ix_lifestyle_profiles_user_id"), "lifestyle_profiles", ["user_id"], unique=True)
    op.create_table(
        "wearable_readings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("heart_rate", sa.Integer(), nullable=True),
        sa.Column("resting_heart_rate", sa.Integer(), nullable=True),
        sa.Column("spo2", sa.Float(), nullable=True),
        sa.Column("steps", sa.Integer(), nullable=True),
        sa.Column("active_minutes", sa.Integer(), nullable=True),
        sa.Column("sleep_hours", sa.Float(), nullable=True),
        sa.Column("sleep_quality", sa.Float(), nullable=True),
        sa.Column("calories", sa.Float(), nullable=True),
        sa.Column("stress_score", sa.Float(), nullable=True),
        sa.Column("source", sa.String(length=50), server_default="manual", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("source IN ('manual', 'synthetic', 'dataset', 'watch')", name="ck_wearable_readings_source"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_wearable_readings_timestamp"), "wearable_readings", ["timestamp"], unique=False)
    op.create_index(op.f("ix_wearable_readings_user_id"), "wearable_readings", ["user_id"], unique=False)
    op.create_index("ix_wearable_readings_user_timestamp", "wearable_readings", ["user_id", "timestamp"], unique=False)
    op.create_table(
        "lab_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("report_date", sa.Date(), nullable=False),
        sa.Column("bp_systolic", sa.Integer(), nullable=True),
        sa.Column("bp_diastolic", sa.Integer(), nullable=True),
        sa.Column("fasting_glucose", sa.Float(), nullable=True),
        sa.Column("hba1c", sa.Float(), nullable=True),
        sa.Column("ldl", sa.Float(), nullable=True),
        sa.Column("hdl", sa.Float(), nullable=True),
        sa.Column("triglycerides", sa.Float(), nullable=True),
        sa.Column("vitamin_d", sa.Float(), nullable=True),
        sa.Column("vitamin_b12", sa.Float(), nullable=True),
        sa.Column("sgpt", sa.Float(), nullable=True),
        sa.Column("sgot", sa.Float(), nullable=True),
        sa.Column("creatinine", sa.Float(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_lab_reports_report_date"), "lab_reports", ["report_date"], unique=False)
    op.create_index(op.f("ix_lab_reports_user_id"), "lab_reports", ["user_id"], unique=False)
    op.create_table(
        "risk_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("cardio_score", sa.Float(), nullable=False),
        sa.Column("metabolic_score", sa.Float(), nullable=False),
        sa.Column("sleep_score", sa.Float(), nullable=False),
        sa.Column("activity_score", sa.Float(), nullable=False),
        sa.Column("lifestyle_score", sa.Float(), nullable=False),
        sa.Column("anomaly_score", sa.Float(), nullable=False),
        sa.Column("twin_alignment_score", sa.Float(), nullable=False),
        sa.Column("overall_risk_level", sa.String(length=50), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("risk_factors", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("recommendations", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_risk_scores_calculated_at"), "risk_scores", ["calculated_at"], unique=False)
    op.create_index(op.f("ix_risk_scores_user_id"), "risk_scores", ["user_id"], unique=False)
    op.create_table(
        "twin_goals",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_age", sa.Integer(), nullable=False),
        sa.Column("target_weight_kg", sa.Float(), nullable=True),
        sa.Column("target_sleep_hours", sa.Float(), nullable=True),
        sa.Column("target_steps", sa.Integer(), nullable=True),
        sa.Column("target_resting_hr", sa.Integer(), nullable=True),
        sa.Column("target_bp_systolic", sa.Integer(), nullable=True),
        sa.Column("target_bp_diastolic", sa.Integer(), nullable=True),
        sa.Column("target_ldl", sa.Float(), nullable=True),
        sa.Column("goal_description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_twin_goals_user_id"), "twin_goals", ["user_id"], unique=False)
    op.create_table(
        "daily_checkins",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("checkin_date", sa.Date(), nullable=False),
        sa.Column("sleep_quality", sa.String(length=100), nullable=True),
        sa.Column("exercise_done", sa.String(length=100), nullable=True),
        sa.Column("food_quality", sa.String(length=100), nullable=True),
        sa.Column("alcohol_used", sa.Boolean(), nullable=True),
        sa.Column("smoking_done", sa.Boolean(), nullable=True),
        sa.Column("stress_level", sa.String(length=100), nullable=True),
        sa.Column("steps_completed", sa.Integer(), nullable=True),
        sa.Column("sleep_hours", sa.Float(), nullable=True),
        sa.Column("user_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_daily_checkins_checkin_date"), "daily_checkins", ["checkin_date"], unique=False)
    op.create_index(op.f("ix_daily_checkins_user_id"), "daily_checkins", ["user_id"], unique=False)
    op.create_table(
        "twin_actions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action_date", sa.Date(), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("recommended_action", sa.Text(), nullable=False),
        sa.Column("priority", sa.String(length=50), nullable=False),
        sa.Column("completed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_twin_actions_action_date"), "twin_actions", ["action_date"], unique=False)
    op.create_index(op.f("ix_twin_actions_user_id"), "twin_actions", ["user_id"], unique=False)
    op.create_table(
        "preventive_alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("alert_type", sa.String(length=100), nullable=False),
        sa.Column("severity", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("recommended_action", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=True),
        sa.Column("acknowledged", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("severity IN ('info', 'warning', 'critical')", name="ck_preventive_alerts_severity"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_preventive_alerts_user_id"), "preventive_alerts", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_preventive_alerts_user_id"), table_name="preventive_alerts")
    op.drop_table("preventive_alerts")
    op.drop_index(op.f("ix_twin_actions_user_id"), table_name="twin_actions")
    op.drop_index(op.f("ix_twin_actions_action_date"), table_name="twin_actions")
    op.drop_table("twin_actions")
    op.drop_index(op.f("ix_daily_checkins_user_id"), table_name="daily_checkins")
    op.drop_index(op.f("ix_daily_checkins_checkin_date"), table_name="daily_checkins")
    op.drop_table("daily_checkins")
    op.drop_index(op.f("ix_twin_goals_user_id"), table_name="twin_goals")
    op.drop_table("twin_goals")
    op.drop_index(op.f("ix_risk_scores_user_id"), table_name="risk_scores")
    op.drop_index(op.f("ix_risk_scores_calculated_at"), table_name="risk_scores")
    op.drop_table("risk_scores")
    op.drop_index(op.f("ix_lab_reports_user_id"), table_name="lab_reports")
    op.drop_index(op.f("ix_lab_reports_report_date"), table_name="lab_reports")
    op.drop_table("lab_reports")
    op.drop_index("ix_wearable_readings_user_timestamp", table_name="wearable_readings")
    op.drop_index(op.f("ix_wearable_readings_user_id"), table_name="wearable_readings")
    op.drop_index(op.f("ix_wearable_readings_timestamp"), table_name="wearable_readings")
    op.drop_table("wearable_readings")
    op.drop_index(op.f("ix_lifestyle_profiles_user_id"), table_name="lifestyle_profiles")
    op.drop_table("lifestyle_profiles")
    op.drop_table("users")
