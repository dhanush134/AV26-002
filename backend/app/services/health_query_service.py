from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.health_data import (
    HealthActivityDaySummary,
    HealthAiTwinProfile,
    HealthDailySummary,
    HealthExerciseSession,
    HealthHeartRatePeriod,
    HealthHeartRateSample,
    HealthImport,
    HealthStepDailySummary,
    HealthStepInterval,
    HealthStepTrendSample,
    HealthStressPeriod,
    HealthStressSample,
)


class HealthQueryService:
    def overview(self, db: Session, user_id: UUID) -> dict:
        latest_import = db.scalar(
            select(HealthImport).where(HealthImport.user_id == user_id).order_by(HealthImport.imported_at.desc()).limit(1)
        )
        latest_daily = db.scalar(
            select(HealthDailySummary)
            .where(HealthDailySummary.user_id == user_id)
            .order_by(HealthDailySummary.date.desc())
            .limit(1)
        )
        profile = db.scalar(select(HealthAiTwinProfile).where(HealthAiTwinProfile.user_id == user_id))
        date_range = db.execute(
            select(func.min(HealthDailySummary.date), func.max(HealthDailySummary.date)).where(HealthDailySummary.user_id == user_id)
        ).one()
        return {
            "user_id": str(user_id),
            "latest_import": self._import_dict(latest_import),
            "available_data_types": profile.available_data_types if profile else [],
            "date_range": {
                "start": date_range[0].isoformat() if date_range[0] else None,
                "end": date_range[1].isoformat() if date_range[1] else None,
            },
            "ai_twin_readiness": self._profile_readiness(profile),
            "latest_daily_summary": self._row_dict(latest_daily),
            "total_records_by_type": self.record_counts(db, user_id),
        }

    def record_counts(self, db: Session, user_id: UUID) -> dict[str, int]:
        models = {
            "heart_rate_periods": HealthHeartRatePeriod,
            "heart_rate_samples": HealthHeartRateSample,
            "step_intervals": HealthStepInterval,
            "step_daily_summaries": HealthStepDailySummary,
            "step_trend_samples": HealthStepTrendSample,
            "stress_periods": HealthStressPeriod,
            "stress_samples": HealthStressSample,
            "activity_day_summaries": HealthActivityDaySummary,
            "exercise_sessions": HealthExerciseSession,
            "daily_summaries": HealthDailySummary,
            "imports": HealthImport,
        }
        return {name: int(db.scalar(select(func.count()).select_from(model).where(model.user_id == user_id)) or 0) for name, model in models.items()}

    def daily_summaries(self, db: Session, user_id: UUID, from_date: date | None, to_date: date | None) -> list[dict]:
        stmt = select(HealthDailySummary).where(HealthDailySummary.user_id == user_id)
        if from_date:
            stmt = stmt.where(HealthDailySummary.date >= from_date)
        if to_date:
            stmt = stmt.where(HealthDailySummary.date <= to_date)
        return [self._row_dict(row) for row in db.scalars(stmt.order_by(HealthDailySummary.date))]

    def heart_rate_detail(
        self, db: Session, user_id: UUID, from_time: datetime | None, to_time: datetime | None, limit: int
    ) -> dict:
        period_stmt = select(HealthHeartRatePeriod).where(HealthHeartRatePeriod.user_id == user_id)
        sample_stmt = select(HealthHeartRateSample).where(HealthHeartRateSample.user_id == user_id)
        if from_time:
            period_stmt = period_stmt.where(HealthHeartRatePeriod.start_time >= from_time)
            sample_stmt = sample_stmt.where(HealthHeartRateSample.start_time >= from_time)
        if to_time:
            period_stmt = period_stmt.where(HealthHeartRatePeriod.start_time <= to_time)
            sample_stmt = sample_stmt.where(HealthHeartRateSample.start_time <= to_time)
        samples = list(db.scalars(sample_stmt.order_by(HealthHeartRateSample.start_time).limit(limit)))
        return {
            "periods": [self._row_dict(row) for row in db.scalars(period_stmt.order_by(HealthHeartRatePeriod.start_time).limit(limit))],
            "samples": [self._row_dict(row) for row in samples],
            "hourly_aggregates": self._hourly_hr(samples),
        }

    def step_detail(self, db: Session, user_id: UUID, from_time: datetime | None, to_time: datetime | None, limit: int) -> dict:
        interval_stmt = select(HealthStepInterval).where(HealthStepInterval.user_id == user_id)
        trend_stmt = select(HealthStepTrendSample).where(HealthStepTrendSample.user_id == user_id)
        if from_time:
            interval_stmt = interval_stmt.where(HealthStepInterval.start_time >= from_time)
            trend_stmt = trend_stmt.where(HealthStepTrendSample.sample_time >= from_time)
        if to_time:
            interval_stmt = interval_stmt.where(HealthStepInterval.start_time <= to_time)
            trend_stmt = trend_stmt.where(HealthStepTrendSample.sample_time <= to_time)
        intervals = list(db.scalars(interval_stmt.order_by(HealthStepInterval.start_time).limit(limit)))
        daily_summaries = list(
            db.scalars(
                select(HealthStepDailySummary)
                .where(HealthStepDailySummary.user_id == user_id)
                .order_by(HealthStepDailySummary.date.desc())
                .limit(limit)
            )
        )
        trend_samples = list(db.scalars(trend_stmt.order_by(HealthStepTrendSample.sample_time).limit(limit)))
        return {
            "intervals": [self._row_dict(row) for row in intervals],
            "daily_summaries": [self._row_dict(row) for row in daily_summaries],
            "trend_samples": [self._row_dict(row) for row in trend_samples],
            "hourly_aggregates": self._hourly_steps(intervals, trend_samples),
            "daily_aggregates": self._daily_steps(intervals, trend_samples, daily_summaries),
        }

    def stress_detail(
        self, db: Session, user_id: UUID, from_time: datetime | None, to_time: datetime | None, limit: int
    ) -> dict:
        period_stmt = select(HealthStressPeriod).where(HealthStressPeriod.user_id == user_id)
        sample_stmt = select(HealthStressSample).where(HealthStressSample.user_id == user_id)
        if from_time:
            period_stmt = period_stmt.where(HealthStressPeriod.start_time >= from_time)
            sample_stmt = sample_stmt.where(HealthStressSample.start_time >= from_time)
        if to_time:
            period_stmt = period_stmt.where(HealthStressPeriod.start_time <= to_time)
            sample_stmt = sample_stmt.where(HealthStressSample.start_time <= to_time)
        samples = list(db.scalars(sample_stmt.order_by(HealthStressSample.start_time).limit(limit)))
        return {
            "periods": [self._row_dict(row) for row in db.scalars(period_stmt.order_by(HealthStressPeriod.start_time).limit(limit))],
            "samples": [self._row_dict(row) for row in samples],
            "hourly_aggregates": self._hourly_stress(samples),
        }

    def ai_twin_context(self, db: Session, user_id: UUID) -> dict:
        profile = db.scalar(select(HealthAiTwinProfile).where(HealthAiTwinProfile.user_id == user_id))
        return {
            "user_id": str(user_id),
            "user_baseline": profile.baseline_json if profile else {},
            "average_steps": (profile.baseline_json or {}).get("avg_daily_steps") if profile else None,
            "heart_rate_patterns": {
                "avg_heart_rate": (profile.baseline_json or {}).get("avg_heart_rate") if profile else None,
                "resting_like_heart_rate_estimate": (profile.baseline_json or {}).get("resting_like_heart_rate_estimate") if profile else None,
                "coverage": (profile.patterns_json or {}).get("heart_rate_coverage_quality") if profile else None,
            },
            "stress_patterns": {"avg_stress_score": (profile.baseline_json or {}).get("avg_stress_score") if profile else None},
            "activity_patterns": profile.patterns_json if profile else {},
            "sleep_availability": {"available": "sleep" in (profile.available_data_types if profile else [])},
            "missing_data_warnings": profile.warnings if profile else ["AI twin profile has not been computed yet."],
            "date_range_used": {
                "start": profile.date_range_start.isoformat() if profile and profile.date_range_start else None,
                "end": profile.date_range_end.isoformat() if profile and profile.date_range_end else None,
            },
            "confidence": {
                "readiness_score": profile.readiness_score if profile else 0,
                "readiness_level": profile.readiness_level if profile else "low",
            },
        }

    def _row_dict(self, row) -> dict | None:
        if row is None:
            return None
        data = {}
        for column in row.__table__.columns:
            value = getattr(row, column.name)
            if hasattr(value, "isoformat"):
                value = value.isoformat()
            elif isinstance(value, UUID):
                value = str(value)
            data[column.name] = value
        return data

    def _import_dict(self, row: HealthImport | None) -> dict | None:
        if not row:
            return None
        return {
            "id": str(row.id),
            "source": row.source,
            "original_filename": row.original_filename,
            "import_status": row.import_status,
            "imported_at": row.imported_at.isoformat(),
            "record_counts": row.record_counts or {},
        }

    def _profile_readiness(self, profile: HealthAiTwinProfile | None) -> dict | None:
        if not profile:
            return None
        return {
            "score": profile.readiness_score,
            "level": profile.readiness_level,
            "available_data_types": profile.available_data_types,
            "missing_data_types": profile.missing_data_types,
            "warnings": profile.warnings,
        }

    def _hourly_hr(self, rows: list[HealthHeartRateSample]) -> list[dict]:
        buckets: dict[str, list[float]] = {}
        for row in rows:
            if row.start_time and row.bpm is not None:
                key = row.start_time.replace(minute=0, second=0, microsecond=0).isoformat()
                buckets.setdefault(key, []).append(row.bpm)
        return [{"hour": hour, "avg_bpm": round(sum(values) / len(values), 2), "sample_count": len(values)} for hour, values in sorted(buckets.items())]

    def _hourly_steps(self, intervals: list[HealthStepInterval], trend_samples: list[HealthStepTrendSample]) -> list[dict]:
        buckets: dict[str, int] = {}
        rows = intervals if intervals else trend_samples
        for row in rows:
            row_time = getattr(row, "start_time", None) or getattr(row, "sample_time", None)
            if row_time:
                key = row_time.replace(minute=0, second=0, microsecond=0).isoformat()
                buckets[key] = buckets.get(key, 0) + (row.steps or 0)
        return [{"hour": hour, "steps": steps} for hour, steps in sorted(buckets.items())]

    def _daily_steps(
        self,
        intervals: list[HealthStepInterval],
        trend_samples: list[HealthStepTrendSample],
        summaries: list[HealthStepDailySummary],
    ) -> list[dict]:
        buckets: dict[str, int] = {}
        rows = intervals if intervals else trend_samples
        for row in rows:
            row_time = getattr(row, "start_time", None) or getattr(row, "sample_time", None)
            if row_time:
                key = row_time.date().isoformat()
                buckets[key] = buckets.get(key, 0) + (row.steps or 0)
        for row in summaries:
            if row.date and row.date.isoformat() not in buckets:
                buckets[row.date.isoformat()] = row.step_count or 0
        return [{"date": day, "steps": steps} for day, steps in sorted(buckets.items())]

    def _hourly_stress(self, rows: list[HealthStressSample]) -> list[dict]:
        buckets: dict[str, list[float]] = {}
        for row in rows:
            if row.start_time and row.score is not None:
                key = row.start_time.replace(minute=0, second=0, microsecond=0).isoformat()
                buckets.setdefault(key, []).append(row.score)
        return [{"hour": hour, "avg_score": round(sum(values) / len(values), 2), "sample_count": len(values)} for hour, values in sorted(buckets.items())]
