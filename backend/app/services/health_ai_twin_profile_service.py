from __future__ import annotations

from statistics import median
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import utc_now
from app.models.health_data import HealthAiTwinProfile, HealthDailySummary, HealthHeartRateSample


class HealthAiTwinProfileService:
    data_types = ["heart_rate", "steps", "stress", "activity", "exercise", "sleep"]

    def refresh_for_user(self, db: Session, user_id: UUID) -> HealthAiTwinProfile:
        summaries = list(
            db.scalars(select(HealthDailySummary).where(HealthDailySummary.user_id == user_id).order_by(HealthDailySummary.date))
        )
        available = sorted({source for summary in summaries for source in (summary.data_sources or [])})
        missing = sorted(set(self.data_types) - set(available))
        score = self._readiness_score(available)
        level = "high" if score >= 75 else "medium" if score >= 45 else "low"
        steps = [summary.steps for summary in summaries if summary.steps is not None]
        hr_values = [summary.avg_heart_rate for summary in summaries if summary.avg_heart_rate is not None]
        stress_values = [summary.stress_avg_score for summary in summaries if summary.stress_avg_score is not None]
        active_days = [summary for summary in summaries if summary.steps or summary.active_time_seconds]
        exercise_days = [summary for summary in summaries if summary.exercise_sessions_count]

        high_bpm_events = sum(summary.high_bpm_count or 0 for summary in summaries)
        hr_sample_count = sum(summary.heart_rate_sample_count or 0 for summary in summaries)
        low_bpm_events = sum(summary.low_bpm_count or 0 for summary in summaries)

        most_active_hours = self._most_active_hours(db, user_id)
        baseline = {
            "avg_daily_steps": round(sum(steps) / len(steps), 2) if steps else None,
            "median_daily_steps": median(steps) if steps else None,
            "avg_heart_rate": round(sum(hr_values) / len(hr_values), 2) if hr_values else None,
            "resting_like_heart_rate_estimate": min(hr_values) if hr_values else None,
            "high_bpm_frequency": round(high_bpm_events / hr_sample_count, 4) if hr_sample_count else None,
            "low_bpm_frequency": round(low_bpm_events / hr_sample_count, 4) if hr_sample_count else None,
            "avg_stress_score": round(sum(stress_values) / len(stress_values), 2) if stress_values else None,
            "active_days_count": len(active_days),
            "exercise_days_count": len(exercise_days),
            "sleep_available": "sleep" in available,
        }
        patterns = {
            "most_active_hours": most_active_hours,
            "common_high_heart_rate_windows": most_active_hours,
            "low_activity_days": [summary.date.isoformat() for summary in summaries if summary.steps is not None and summary.steps < 3000][:30],
            "heart_rate_coverage_quality": "high" if hr_sample_count >= 500 else "medium" if hr_sample_count else "none",
            "stress_activity_relation": "Available after more overlapping stress and activity days."
            if "stress" in available and "activity" in available
            else None,
            "missing_sleep_limitation": "Sleep data was not found; sleep-related AI twin insights are limited."
            if "sleep" not in available
            else None,
        }
        warnings = []
        if "sleep" not in available:
            warnings.append("Sleep data was not found in stored health records.")
        if "heart_rate" not in available:
            warnings.append("Detailed heart-rate data is missing.")
        if not summaries:
            warnings.append("No daily health summaries are available yet.")

        profile = db.scalar(select(HealthAiTwinProfile).where(HealthAiTwinProfile.user_id == user_id))
        values = dict(
            readiness_score=score,
            readiness_level=level,
            available_data_types=available,
            missing_data_types=missing,
            date_range_start=summaries[0].date if summaries else None,
            date_range_end=summaries[-1].date if summaries else None,
            baseline_json=baseline,
            patterns_json=patterns,
            warnings=warnings,
            last_computed_at=utc_now(),
        )
        if profile:
            for key, value in values.items():
                setattr(profile, key, value)
        else:
            profile = HealthAiTwinProfile(user_id=user_id, **values)
            db.add(profile)
        db.flush()
        return profile

    def _readiness_score(self, available: list[str]) -> int:
        score = 0
        if "heart_rate" in available:
            score += 35
        if "steps" in available:
            score += 25
        if "stress" in available:
            score += 15
        if "activity" in available:
            score += 10
        if "exercise" in available:
            score += 10
        if "sleep" in available:
            score += 20
        return min(score, 100)

    def _most_active_hours(self, db: Session, user_id: UUID) -> list[dict[str, int]]:
        rows = db.execute(
            select(func.extract("hour", HealthHeartRateSample.start_time).label("hour"), func.count(HealthHeartRateSample.id))
            .where(HealthHeartRateSample.user_id == user_id, HealthHeartRateSample.bpm >= 120)
            .group_by("hour")
            .order_by(func.count(HealthHeartRateSample.id).desc())
            .limit(5)
        ).all()
        return [{"hour": int(hour), "high_bpm_samples": int(count)} for hour, count in rows if hour is not None]
