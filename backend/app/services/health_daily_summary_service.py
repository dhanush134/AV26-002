from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.health_data import (
    HealthActivityDaySummary,
    HealthDailySummary,
    HealthExerciseSession,
    HealthHeartRatePeriod,
    HealthHeartRateSample,
    HealthSleepSession,
    HealthStepDailySummary,
    HealthStepInterval,
    HealthStressPeriod,
    HealthStressSample,
)


def day_bounds(day: date) -> tuple[datetime, datetime]:
    start = datetime.combine(day, time.min, tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    return start, end


class HealthDailySummaryService:
    def recompute_for_user(
        self, db: Session, user_id: UUID, from_date: date | None = None, to_date: date | None = None
    ) -> int:
        dates = self._resolve_dates(db, user_id, from_date, to_date)
        count = 0
        for day in dates:
            self.recompute_day(db, user_id, day)
            count += 1
        db.flush()
        return count

    def recompute_day(self, db: Session, user_id: UUID, day: date) -> HealthDailySummary:
        start, end = day_bounds(day)
        data_sources: set[str] = set()
        import_ids: set[str] = set()

        step_daily = db.scalar(
            select(HealthStepDailySummary)
            .where(HealthStepDailySummary.user_id == user_id, HealthStepDailySummary.date == day)
            .order_by(HealthStepDailySummary.updated_at.desc())
            .limit(1)
        )
        step_interval_stats = db.execute(
            select(
                func.sum(HealthStepInterval.steps),
                func.sum(HealthStepInterval.distance_meters),
                func.sum(HealthStepInterval.calories),
            ).where(
                HealthStepInterval.user_id == user_id,
                HealthStepInterval.start_time >= start,
                HealthStepInterval.start_time < end,
            )
        ).one()

        hr_sample_stats = db.execute(
            select(
                func.avg(HealthHeartRateSample.bpm),
                func.min(func.coalesce(HealthHeartRateSample.min_bpm, HealthHeartRateSample.bpm)),
                func.max(func.coalesce(HealthHeartRateSample.max_bpm, HealthHeartRateSample.bpm)),
                func.count(HealthHeartRateSample.id),
            ).where(
                HealthHeartRateSample.user_id == user_id,
                HealthHeartRateSample.start_time >= start,
                HealthHeartRateSample.start_time < end,
            )
        ).one()
        high_bpm_count = db.scalar(
            select(func.count(HealthHeartRateSample.id)).where(
                HealthHeartRateSample.user_id == user_id,
                HealthHeartRateSample.start_time >= start,
                HealthHeartRateSample.start_time < end,
                HealthHeartRateSample.bpm >= 120,
            )
        )
        low_bpm_count = db.scalar(
            select(func.count(HealthHeartRateSample.id)).where(
                HealthHeartRateSample.user_id == user_id,
                HealthHeartRateSample.start_time >= start,
                HealthHeartRateSample.start_time < end,
                HealthHeartRateSample.bpm <= 50,
            )
        )
        if not hr_sample_stats[3]:
            hr_sample_stats = db.execute(
                select(
                    func.avg(HealthHeartRatePeriod.avg_bpm),
                    func.min(HealthHeartRatePeriod.min_bpm),
                    func.max(HealthHeartRatePeriod.max_bpm),
                    func.count(HealthHeartRatePeriod.id),
                ).where(
                    HealthHeartRatePeriod.user_id == user_id,
                    HealthHeartRatePeriod.start_time >= start,
                    HealthHeartRatePeriod.start_time < end,
                )
            ).one()
            high_bpm_count = db.scalar(
                select(func.count(HealthHeartRatePeriod.id)).where(
                    HealthHeartRatePeriod.user_id == user_id,
                    HealthHeartRatePeriod.start_time >= start,
                    HealthHeartRatePeriod.start_time < end,
                    HealthHeartRatePeriod.avg_bpm >= 120,
                )
            )
            low_bpm_count = db.scalar(
                select(func.count(HealthHeartRatePeriod.id)).where(
                    HealthHeartRatePeriod.user_id == user_id,
                    HealthHeartRatePeriod.start_time >= start,
                    HealthHeartRatePeriod.start_time < end,
                    HealthHeartRatePeriod.avg_bpm <= 50,
                )
            )

        stress_stats = db.execute(
            select(
                func.avg(HealthStressSample.score),
                func.min(func.coalesce(HealthStressSample.min_score, HealthStressSample.score)),
                func.max(func.coalesce(HealthStressSample.max_score, HealthStressSample.score)),
                func.count(HealthStressSample.id),
            ).where(
                HealthStressSample.user_id == user_id,
                HealthStressSample.start_time >= start,
                HealthStressSample.start_time < end,
            )
        ).one()
        if not stress_stats[3]:
            stress_stats = db.execute(
                select(
                    func.avg(HealthStressPeriod.score),
                    func.min(HealthStressPeriod.min_score),
                    func.max(HealthStressPeriod.max_score),
                    func.count(HealthStressPeriod.id),
                ).where(
                    HealthStressPeriod.user_id == user_id,
                    HealthStressPeriod.start_time >= start,
                    HealthStressPeriod.start_time < end,
                )
            ).one()

        activity = db.scalar(
            select(HealthActivityDaySummary)
            .where(HealthActivityDaySummary.user_id == user_id, HealthActivityDaySummary.date == day)
            .order_by(HealthActivityDaySummary.updated_at.desc())
            .limit(1)
        )
        exercise_stats = db.execute(
            select(
                func.count(HealthExerciseSession.id),
                func.sum(HealthExerciseSession.calories),
                func.sum(HealthExerciseSession.duration_seconds),
            ).where(
                HealthExerciseSession.user_id == user_id,
                HealthExerciseSession.start_time >= start,
                HealthExerciseSession.start_time < end,
            )
        ).one()
        sleep = db.scalar(
            select(HealthSleepSession)
            .where(
                HealthSleepSession.user_id == user_id,
                HealthSleepSession.start_time >= start,
                HealthSleepSession.start_time < end,
            )
            .order_by(HealthSleepSession.duration_seconds.desc().nullslast())
            .limit(1)
        )

        if step_daily or step_interval_stats[0]:
            data_sources.add("steps")
        if hr_sample_stats[3]:
            data_sources.add("heart_rate")
        if stress_stats[3]:
            data_sources.add("stress")
        if activity:
            data_sources.add("activity")
        if exercise_stats[0]:
            data_sources.add("exercise")
        if sleep:
            data_sources.add("sleep")

        steps = step_daily.step_count if step_daily and step_daily.step_count is not None else int(step_interval_stats[0] or 0) or None
        distance = (
            step_daily.distance_meters
            if step_daily and step_daily.distance_meters is not None
            else float(step_interval_stats[1] or 0) or None
        )
        calories = (
            step_daily.calories
            if step_daily and step_daily.calories is not None
            else float(step_interval_stats[2] or 0) or None
        )

        if step_daily and step_daily.import_id:
            import_ids.add(str(step_daily.import_id))
        if activity and activity.import_id:
            import_ids.add(str(activity.import_id))
        if sleep and sleep.import_id:
            import_ids.add(str(sleep.import_id))

        summary = db.scalar(select(HealthDailySummary).where(HealthDailySummary.user_id == user_id, HealthDailySummary.date == day))
        values = dict(
            import_ids=sorted(import_ids),
            steps=steps,
            walking_steps=step_daily.walk_step_count if step_daily else None,
            running_steps=step_daily.run_step_count if step_daily else None,
            distance_meters=distance if distance is not None else (activity.distance_meters if activity else None),
            calories=calories if calories is not None else (activity.calories if activity else None),
            active_time_seconds=(step_daily.active_time_seconds if step_daily else None) or (activity.active_time_seconds if activity else None),
            walk_time_seconds=activity.walk_time_seconds if activity else None,
            run_time_seconds=activity.run_time_seconds if activity else None,
            exercise_time_seconds=(activity.exercise_time_seconds if activity else None) or int(exercise_stats[2] or 0) or None,
            floor_count=activity.floor_count if activity else None,
            avg_heart_rate=float(hr_sample_stats[0]) if hr_sample_stats[0] is not None else None,
            min_heart_rate=float(hr_sample_stats[1]) if hr_sample_stats[1] is not None else None,
            max_heart_rate=float(hr_sample_stats[2]) if hr_sample_stats[2] is not None else None,
            heart_rate_sample_count=int(hr_sample_stats[3] or 0),
            high_bpm_count=int(high_bpm_count or 0),
            low_bpm_count=int(low_bpm_count or 0),
            stress_avg_score=float(stress_stats[0]) if stress_stats[0] is not None else None,
            stress_min_score=float(stress_stats[1]) if stress_stats[1] is not None else None,
            stress_max_score=float(stress_stats[2]) if stress_stats[2] is not None else None,
            stress_sample_count=int(stress_stats[3] or 0),
            exercise_sessions_count=int(exercise_stats[0] or 0),
            exercise_calories=float(exercise_stats[1]) if exercise_stats[1] is not None else None,
            sleep_minutes=int(sleep.duration_seconds / 60) if sleep and sleep.duration_seconds else None,
            sleep_score=sleep.sleep_score if sleep else None,
            data_sources=sorted(data_sources),
            data_quality={
                "missing_signals": sorted(set(["heart_rate", "steps", "stress", "activity", "exercise", "sleep"]) - data_sources),
                "confidence": "high" if len(data_sources) >= 4 else "medium" if len(data_sources) >= 2 else "low",
            },
            ai_twin_notes={
                "sleep_limitation": "Sleep data not available for this date." if "sleep" not in data_sources else None
            },
        )
        if summary:
            for key, value in values.items():
                setattr(summary, key, value)
        else:
            summary = HealthDailySummary(user_id=user_id, date=day, **values)
            db.add(summary)
        return summary

    def _resolve_dates(self, db: Session, user_id: UUID, from_date: date | None, to_date: date | None) -> list[date]:
        if from_date and to_date:
            days: list[date] = []
            current = from_date
            while current <= to_date:
                days.append(current)
                current += timedelta(days=1)
            return days
        candidates: set[date] = set()
        for model in (HealthStepDailySummary, HealthActivityDaySummary, HealthDailySummary):
            for day in db.scalars(select(model.date).where(model.user_id == user_id, model.date.is_not(None))):
                candidates.add(day)
        for model in (
            HealthStepInterval,
            HealthHeartRateSample,
            HealthHeartRatePeriod,
            HealthStressSample,
            HealthStressPeriod,
            HealthExerciseSession,
            HealthSleepSession,
        ):
            for value in db.scalars(select(model.start_time).where(model.user_id == user_id, model.start_time.is_not(None))):
                candidates.add(value.date())
        if from_date:
            candidates = {day for day in candidates if day >= from_date}
        if to_date:
            candidates = {day for day in candidates if day <= to_date}
        return sorted(candidates)
