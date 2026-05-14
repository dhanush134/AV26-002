from __future__ import annotations

import hashlib
from collections import Counter
from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.health_data import (
    HealthActivityDaySummary,
    HealthActivityExtraData,
    HealthActivityLevelRecord,
    HealthAiTwinProfile,
    HealthBodyMeasurement,
    HealthDailySummary,
    HealthDeviceProfile,
    HealthExerciseLiveSample,
    HealthExerciseSession,
    HealthHeartRatePeriod,
    HealthHeartRateSample,
    HealthImport,
    HealthImportFile,
    HealthSleepSession,
    HealthStepDailySummary,
    HealthStepInterval,
    HealthStepTrendSample,
    HealthStressHistogram,
    HealthStressPeriod,
    HealthStressSample,
    HealthUserProfileEntry,
)
from app.schemas.health_import_schemas import HealthImportStorageResult, SamsungHealthImportResponse


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def bool_or_none(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes"}:
        return True
    if text in {"0", "false", "no"}:
        return False
    return None


class HealthDataStorageService:
    import_owned_models = (
        HealthImportFile,
        HealthHeartRateSample,
        HealthHeartRatePeriod,
        HealthStepInterval,
        HealthStepDailySummary,
        HealthStepTrendSample,
        HealthStressSample,
        HealthStressPeriod,
        HealthStressHistogram,
        HealthActivityExtraData,
        HealthActivityLevelRecord,
        HealthActivityDaySummary,
        HealthExerciseLiveSample,
        HealthExerciseSession,
        HealthSleepSession,
        HealthBodyMeasurement,
        HealthUserProfileEntry,
        HealthDeviceProfile,
    )

    def store_samsung_import(
        self,
        db: Session,
        user_id: UUID,
        parsed: SamsungHealthImportResponse,
        original_filename: str,
        zip_bytes: bytes,
        force_reprocess: bool = False,
    ) -> HealthImportStorageResult:
        file_sha = hashlib.sha256(zip_bytes).hexdigest()
        existing = db.scalar(
            select(HealthImport).where(HealthImport.user_id == user_id, HealthImport.file_sha256 == file_sha)
        )
        if existing and not force_reprocess:
            return HealthImportStorageResult(
                import_id=str(existing.id),
                status="already_imported",
                already_imported=True,
                message="This Samsung Health export was already imported for this user.",
                existing_import_id=str(existing.id),
                saved_counts=existing.record_counts or {},
            )

        saved: Counter[str] = Counter()
        duplicates: Counter[str] = Counter()
        failed: Counter[str] = Counter()
        warnings = list(parsed.files.warnings)

        try:
            if existing and force_reprocess:
                health_import = existing
                self._delete_import_records(db, existing.id)
                health_import.import_status = "parsed"
                health_import.warnings = warnings
                health_import.errors = []
                health_import.record_counts = {}
            else:
                health_import = HealthImport(
                    user_id=user_id,
                    source=parsed.source,
                    original_filename=original_filename,
                    file_sha256=file_sha,
                    file_size_bytes=len(zip_bytes),
                    import_status="parsed",
                    detected_data=parsed.detected.model_dump(),
                    files_processed=parsed.files.model_dump(),
                    warnings=warnings,
                    errors=[],
                    record_counts={},
                )
                db.add(health_import)
                db.flush()

            self._store_import_files(db, user_id, health_import.id, parsed, saved)
            self._store_heart_rate(db, user_id, health_import.id, parsed, saved, duplicates, failed)
            self._store_steps(db, user_id, health_import.id, parsed, saved, duplicates, failed)
            self._store_stress(db, user_id, health_import.id, parsed, saved, duplicates, failed)
            self._store_activity(db, user_id, health_import.id, parsed, saved, duplicates, failed)
            self._store_exercise(db, user_id, health_import.id, parsed, saved, duplicates, failed)
            self._store_sleep(db, user_id, health_import.id, parsed, saved, duplicates, failed)
            self._store_body_profile(db, user_id, health_import.id, parsed, saved, duplicates, failed)
            self._store_device_profile(db, user_id, health_import.id, parsed, saved, duplicates, failed)

            health_import.import_status = "stored" if not failed else "partial"
            health_import.record_counts = dict(saved)
            health_import.files_processed = parsed.files.model_dump()
            health_import.detected_data = parsed.detected.model_dump()
            health_import.errors = [f"{key}: {value}" for key, value in failed.items()]
            db.flush()
        except Exception:
            db.rollback()
            raise

        affected_dates = self._affected_dates(parsed)
        return HealthImportStorageResult(
            import_id=str(health_import.id),
            status=health_import.import_status,
            already_imported=False,
            saved_counts=dict(saved),
            duplicate_counts=dict(duplicates),
            failed_counts=dict(failed),
            warnings=warnings,
            affected_dates=[day.isoformat() for day in sorted(affected_dates)],
        )

    def _delete_import_records(self, db: Session, import_id: UUID) -> None:
        for model in self.import_owned_models:
            db.execute(delete(model).where(model.import_id == import_id))
        db.flush()

    def _store_import_files(
        self, db: Session, user_id: UUID, import_id: UUID, parsed: SamsungHealthImportResponse, saved: Counter[str]
    ) -> None:
        for path in parsed.files.processed:
            file_type = "json" if path.lower().endswith(".json") else "csv" if path.lower().endswith(".csv") else "unknown"
            category = path.split("/")[1] if path.startswith("jsons/") and "/" in path else path.split(".202")[0]
            db.add(
                HealthImportFile(
                    import_id=import_id,
                    user_id=user_id,
                    path=path,
                    category=category,
                    file_type=file_type,
                    row_count=0,
                    parsed_count=0,
                    warning_count=0,
                )
            )
            saved["health_import_files"] += 1

    def _upsert(
        self,
        db: Session,
        model: type,
        identities: list[dict[str, Any]],
        values: dict[str, Any],
        table_name: str,
        saved: Counter[str],
        duplicates: Counter[str],
    ) -> Any:
        for identity in identities:
            if not identity or any(value is None for value in identity.values()):
                continue
            existing = db.scalar(select(model).filter_by(**identity))
            if existing:
                for key, value in values.items():
                    setattr(existing, key, value)
                duplicates[table_name] += 1
                return existing
        instance = model(**values)
        db.add(instance)
        db.flush()
        saved[table_name] += 1
        return instance

    def _store_heart_rate(
        self,
        db: Session,
        user_id: UUID,
        import_id: UUID,
        parsed: SamsungHealthImportResponse,
        saved: Counter[str],
        duplicates: Counter[str],
        failed: Counter[str],
    ) -> None:
        periods_by_datauuid: dict[str, HealthHeartRatePeriod] = {}
        for period in parsed.heart_rate.periods:
            try:
                values = dict(
                    user_id=user_id,
                    import_id=import_id,
                    source=parsed.source,
                    source_file=period.source_file,
                    datauuid=period.datauuid,
                    deviceuuid=period.deviceuuid,
                    package_name=period.package_name,
                    start_time=parse_dt(period.start_time),
                    end_time=parse_dt(period.end_time),
                    avg_bpm=period.avg_bpm,
                    min_bpm=period.min_bpm,
                    max_bpm=period.max_bpm,
                    heart_beat_count=period.heart_beat_count,
                    binning_data_ref=period.binning_data_ref,
                    time_offset_ms=period.time_offset_ms,
                    create_time=parse_dt(period.create_time),
                    update_time=parse_dt(period.update_time),
                    raw_extra=period.raw_extra,
                )
                row = self._upsert(
                    db,
                    HealthHeartRatePeriod,
                    [
                        {"user_id": user_id, "datauuid": period.datauuid},
                        {
                            "user_id": user_id,
                            "source_file": period.source_file,
                            "start_time": values["start_time"],
                            "end_time": values["end_time"],
                            "avg_bpm": period.avg_bpm,
                        },
                    ],
                    values,
                    "heart_rate_periods",
                    saved,
                    duplicates,
                )
                if period.datauuid:
                    periods_by_datauuid[period.datauuid] = row
            except Exception:
                failed["heart_rate_periods"] += 1
        for sample in parsed.heart_rate.samples:
            try:
                parent = periods_by_datauuid.get(sample.parent_datauuid or "")
                values = dict(
                    user_id=user_id,
                    import_id=import_id,
                    parent_period_id=parent.id if parent else None,
                    parent_datauuid=sample.parent_datauuid,
                    parent_binning_data_ref=sample.parent_binning_data_ref,
                    source=parsed.source,
                    source_json_file=sample.source_json_file,
                    start_time=parse_dt(sample.start_time),
                    end_time=parse_dt(sample.end_time),
                    duration_seconds=int_or_none(sample.duration_seconds),
                    bpm=sample.bpm,
                    min_bpm=sample.min_bpm,
                    max_bpm=sample.max_bpm,
                    raw_extra=sample.raw_extra,
                )
                self._upsert(
                    db,
                    HealthHeartRateSample,
                    [
                        {
                            "user_id": user_id,
                            "parent_datauuid": sample.parent_datauuid,
                            "start_time": values["start_time"],
                            "end_time": values["end_time"],
                            "bpm": sample.bpm,
                        }
                    ],
                    values,
                    "heart_rate_samples",
                    saved,
                    duplicates,
                )
            except Exception:
                failed["heart_rate_samples"] += 1

    def _store_steps(
        self, db: Session, user_id: UUID, import_id: UUID, parsed, saved: Counter[str], duplicates: Counter[str], failed
    ) -> None:
        for interval in parsed.steps.intervals:
            try:
                values = dict(
                    user_id=user_id,
                    import_id=import_id,
                    source=parsed.source,
                    source_file=interval.source_file,
                    datauuid=interval.datauuid,
                    deviceuuid=interval.deviceuuid,
                    package_name=interval.package_name,
                    start_time=parse_dt(interval.start_time),
                    end_time=parse_dt(interval.end_time),
                    duration_seconds=int_or_none(interval.duration_seconds),
                    steps=interval.steps,
                    distance_meters=interval.distance_meters,
                    calories=interval.calories,
                    speed=interval.speed,
                    sample_position_type=int_or_none(interval.sample_position_type),
                    time_offset_ms=interval.time_offset_ms,
                    create_time=parse_dt(interval.create_time),
                    update_time=parse_dt(interval.update_time),
                    raw_extra=interval.raw_extra,
                )
                self._upsert(
                    db,
                    HealthStepInterval,
                    [
                        {"user_id": user_id, "datauuid": interval.datauuid},
                        {
                            "user_id": user_id,
                            "start_time": values["start_time"],
                            "end_time": values["end_time"],
                            "steps": interval.steps,
                            "source_file": interval.source_file,
                        },
                    ],
                    values,
                    "step_intervals",
                    saved,
                    duplicates,
                )
            except Exception:
                failed["step_intervals"] += 1
        for summary in parsed.steps.daily_summaries:
            try:
                values = dict(
                    user_id=user_id,
                    import_id=import_id,
                    source=parsed.source,
                    source_file=summary.source_file,
                    datauuid=summary.datauuid,
                    deviceuuid=summary.deviceuuid,
                    date=parse_date(summary.date),
                    day_time=parse_dt(summary.day_time),
                    step_count=summary.step_count,
                    walk_step_count=summary.walk_step_count,
                    run_step_count=summary.run_step_count,
                    healthy_step=summary.healthy_step,
                    active_time_seconds=int_or_none(summary.active_time),
                    distance_meters=summary.distance_meters,
                    calories=summary.calories,
                    speed=summary.speed,
                    achievement=summary.achievement,
                    recommendation=summary.recommendation,
                    binning_data_ref=summary.binning_data_ref,
                    source_package_name=summary.source_package_name,
                    package_name=summary.package_name,
                    create_time=parse_dt(summary.create_time),
                    update_time=parse_dt(summary.update_time),
                    raw_extra=summary.raw_extra,
                )
                self._upsert(
                    db,
                    HealthStepDailySummary,
                    [
                        {"user_id": user_id, "date": values["date"], "datauuid": summary.datauuid},
                        {"user_id": user_id, "date": values["date"], "source_file": summary.source_file},
                    ],
                    values,
                    "step_daily_summaries",
                    saved,
                    duplicates,
                )
            except Exception:
                failed["step_daily_summaries"] += 1
        for sample in parsed.steps.trend_samples:
            try:
                values = dict(
                    user_id=user_id,
                    import_id=import_id,
                    source=parsed.source,
                    parent_datauuid=sample.parent_datauuid,
                    source_json_file=sample.source_json_file,
                    sample_time=parse_dt(sample.start_time),
                    time_unit=str(sample.time_unit) if sample.time_unit is not None else None,
                    steps=sample.steps,
                    walk_step_count=sample.walk_step_count,
                    run_step_count=sample.run_step_count,
                    distance_meters=sample.distance_meters,
                    calories=sample.calories,
                    speed=sample.speed,
                    raw_extra=sample.raw_extra,
                )
                self._upsert(
                    db,
                    HealthStepTrendSample,
                    [
                        {"user_id": user_id, "parent_datauuid": sample.parent_datauuid, "sample_time": values["sample_time"]},
                        {"user_id": user_id, "source_json_file": sample.source_json_file, "time_unit": values["time_unit"]},
                    ],
                    values,
                    "step_trend_samples",
                    saved,
                    duplicates,
                )
            except Exception:
                failed["step_trend_samples"] += 1

    def _store_stress(self, db: Session, user_id: UUID, import_id: UUID, parsed, saved, duplicates, failed) -> None:
        for period in parsed.stress.periods:
            try:
                values = dict(
                    user_id=user_id,
                    import_id=import_id,
                    source=parsed.source,
                    source_file=period.source_file,
                    datauuid=period.datauuid,
                    deviceuuid=period.deviceuuid,
                    package_name=period.package_name,
                    start_time=parse_dt(period.start_time),
                    end_time=parse_dt(period.end_time),
                    score=period.score,
                    min_score=period.min_score,
                    max_score=period.max_score,
                    algorithm=period.algorithm,
                    tag_id=period.tag_id,
                    binning_data_ref=period.binning_data_ref,
                    time_offset_ms=period.time_offset_ms,
                    create_time=parse_dt(period.create_time),
                    update_time=parse_dt(period.update_time),
                    raw_extra=period.raw_extra,
                )
                self._upsert(
                    db,
                    HealthStressPeriod,
                    [
                        {"user_id": user_id, "datauuid": period.datauuid},
                        {
                            "user_id": user_id,
                            "start_time": values["start_time"],
                            "end_time": values["end_time"],
                            "score": period.score,
                            "source_file": period.source_file,
                        },
                    ],
                    values,
                    "stress_periods",
                    saved,
                    duplicates,
                )
            except Exception:
                failed["stress_periods"] += 1
        for sample in parsed.stress.samples:
            try:
                values = dict(
                    user_id=user_id,
                    import_id=import_id,
                    source=parsed.source,
                    parent_datauuid=sample.parent_datauuid,
                    source_json_file=sample.source_json_file,
                    start_time=parse_dt(sample.start_time),
                    end_time=parse_dt(sample.end_time),
                    score=sample.score,
                    min_score=sample.min_score,
                    max_score=sample.max_score,
                    level=str(sample.level) if sample.level is not None else None,
                    flag=str(sample.flag) if sample.flag is not None else None,
                    raw_extra=sample.raw_extra,
                )
                self._upsert(
                    db,
                    HealthStressSample,
                    [{"user_id": user_id, "parent_datauuid": sample.parent_datauuid, "start_time": values["start_time"], "end_time": values["end_time"]}],
                    values,
                    "stress_samples",
                    saved,
                    duplicates,
                )
            except Exception:
                failed["stress_samples"] += 1
        for histogram in parsed.stress.histograms:
            try:
                values = dict(
                    user_id=user_id,
                    import_id=import_id,
                    source=parsed.source,
                    source_file=histogram.source_file,
                    datauuid=histogram.datauuid,
                    deviceuuid=histogram.deviceuuid,
                    base_hr=histogram.base_hr,
                    histogram_ref=histogram.histogram_ref,
                    decay_time=None,
                    values_json=histogram.values,
                    version=histogram.version,
                    source_json_file=histogram.source_json_file,
                    raw_extra=histogram.raw_extra,
                )
                self._upsert(
                    db,
                    HealthStressHistogram,
                    [{"user_id": user_id, "datauuid": histogram.datauuid}],
                    values,
                    "stress_histograms",
                    saved,
                    duplicates,
                )
            except Exception:
                failed["stress_histograms"] += 1

    def _store_activity(self, db: Session, user_id: UUID, import_id: UUID, parsed, saved, duplicates, failed) -> None:
        for summary in parsed.activity.day_summaries:
            try:
                values = dict(
                    user_id=user_id,
                    import_id=import_id,
                    source=parsed.source,
                    source_file=summary.source_file,
                    datauuid=summary.datauuid,
                    deviceuuid=summary.deviceuuid,
                    date=parse_date(summary.date),
                    day_time=parse_dt(summary.day_time),
                    step_count=summary.step_count,
                    distance_meters=summary.distance_meters,
                    calories=summary.calories,
                    active_time_seconds=int_or_none(summary.active_time),
                    walk_time_seconds=int_or_none(summary.walk_time),
                    run_time_seconds=int_or_none(summary.run_time),
                    exercise_time_seconds=int_or_none(summary.exercise_time),
                    dynamic_active_time_seconds=int_or_none(summary.dynamic_active_time),
                    longest_active_time_seconds=int_or_none(summary.longest_active_time),
                    longest_idle_time_seconds=int_or_none(summary.longest_idle_time),
                    move_hourly_count=summary.move_hourly_count,
                    floor_count=summary.floor_count,
                    score=summary.score,
                    goal=summary.goal,
                    target=summary.target,
                    movement_type=summary.movement_type,
                    energy_type=summary.energy_type,
                    extra_data_ref=summary.extra_data_ref,
                    raw_extra=summary.raw_extra,
                )
                self._upsert(
                    db,
                    HealthActivityDaySummary,
                    [
                        {"user_id": user_id, "date": values["date"], "datauuid": summary.datauuid},
                        {"user_id": user_id, "date": values["date"], "source_file": summary.source_file},
                    ],
                    values,
                    "activity_day_summaries",
                    saved,
                    duplicates,
                )
            except Exception:
                failed["activity_day_summaries"] += 1
        for extra in parsed.activity.extra_data:
            try:
                values = dict(
                    user_id=user_id,
                    import_id=import_id,
                    source=parsed.source,
                    parent_datauuid=extra.parent_datauuid,
                    source_json_file=None,
                    most_active_minutes=int_or_none(extra.mMostActiveMinutes),
                    activity_list=extra.mActivityList,
                    unit_data_list=extra.mUnitDataList,
                    is_goal_achieved=extra.mIsGoalAchieved,
                    streak_day_count=extra.mStreakDayCount,
                    adaptive_goal=extra.mAdaptiveGoal,
                    version=int_or_none((extra.raw_extra or {}).get("version")),
                    raw_extra=extra.raw_extra,
                )
                self._upsert(
                    db,
                    HealthActivityExtraData,
                    [{"user_id": user_id, "parent_datauuid": extra.parent_datauuid}],
                    values,
                    "activity_extra_data",
                    saved,
                    duplicates,
                )
            except Exception:
                failed["activity_extra_data"] += 1
        for level in parsed.activity.activity_levels:
            try:
                values = dict(
                    user_id=user_id,
                    import_id=import_id,
                    source=parsed.source,
                    source_file=level.source_file,
                    datauuid=level.datauuid,
                    deviceuuid=level.deviceuuid,
                    package_name=level.package_name,
                    activity_level=int_or_none(level.activity_level),
                    start_time=parse_dt(level.start_time),
                    time_offset_ms=level.time_offset_ms,
                    create_time=parse_dt(level.create_time),
                    update_time=parse_dt(level.update_time),
                    raw_extra=level.raw_extra,
                )
                self._upsert(
                    db,
                    HealthActivityLevelRecord,
                    [{"user_id": user_id, "datauuid": level.datauuid}],
                    values,
                    "activity_level_records",
                    saved,
                    duplicates,
                )
            except Exception:
                failed["activity_level_records"] += 1

    def _store_exercise(self, db: Session, user_id: UUID, import_id: UUID, parsed, saved, duplicates, failed) -> None:
        for session in parsed.exercise.sessions:
            try:
                values = dict(
                    user_id=user_id,
                    import_id=import_id,
                    source=parsed.source,
                    source_file=session.source_file,
                    datauuid=session.datauuid,
                    deviceuuid=session.deviceuuid,
                    package_name=session.package_name,
                    start_time=parse_dt(session.start_time),
                    end_time=parse_dt(session.end_time),
                    duration_seconds=int_or_none(session.duration_seconds),
                    exercise_type=str(session.exercise_type) if session.exercise_type is not None else None,
                    exercise_custom_type=str(session.exercise_custom_type) if session.exercise_custom_type is not None else None,
                    calories=session.calories,
                    distance_meters=session.distance_meters,
                    count=session.count,
                    count_type=str(session.count_type) if session.count_type is not None else None,
                    mean_heart_rate=session.mean_heart_rate,
                    min_heart_rate=session.min_heart_rate,
                    max_heart_rate=session.max_heart_rate,
                    mean_speed=session.mean_speed,
                    max_speed=session.max_speed,
                    mean_cadence=session.mean_cadence,
                    max_cadence=session.max_cadence,
                    mean_power=session.mean_power,
                    max_power=session.max_power,
                    vo2_max=session.vo2_max,
                    altitude_gain=session.altitude_gain,
                    altitude_loss=session.altitude_loss,
                    max_altitude=session.max_altitude,
                    min_altitude=session.min_altitude,
                    incline_distance=session.incline_distance,
                    decline_distance=session.decline_distance,
                    sweat_loss=session.sweat_loss,
                    live_data_ref=session.live_data_ref,
                    location_data_ref=session.location_data_ref,
                    additional_ref=session.additional_ref,
                    auxiliary_devices=session.auxiliary_devices,
                    create_time=parse_dt(session.create_time),
                    update_time=parse_dt(session.update_time),
                    raw_extra=session.raw_extra,
                )
                self._upsert(
                    db,
                    HealthExerciseSession,
                    [
                        {"user_id": user_id, "datauuid": session.datauuid},
                        {"user_id": user_id, "start_time": values["start_time"], "end_time": values["end_time"], "exercise_type": values["exercise_type"]},
                    ],
                    values,
                    "exercise_sessions",
                    saved,
                    duplicates,
                )
            except Exception:
                failed["exercise_sessions"] += 1
        for sample in parsed.exercise.live_samples:
            try:
                values = dict(
                    user_id=user_id,
                    import_id=import_id,
                    source=parsed.source,
                    parent_datauuid=sample.parent_datauuid,
                    source_json_file=sample.source_json_file,
                    sample_time=parse_dt(sample.start_time),
                    heart_rate=sample.heart_rate,
                    speed=sample.speed,
                    distance_meters=sample.distance,
                    cadence=sample.cadence,
                    raw_extra=sample.raw_extra,
                )
                self._upsert(
                    db,
                    HealthExerciseLiveSample,
                    [{"user_id": user_id, "parent_datauuid": sample.parent_datauuid, "sample_time": values["sample_time"]}],
                    values,
                    "exercise_live_samples",
                    saved,
                    duplicates,
                )
            except Exception:
                failed["exercise_live_samples"] += 1

    def _store_sleep(self, db: Session, user_id: UUID, import_id: UUID, parsed, saved, duplicates, failed) -> None:
        for session in parsed.sleep.sessions:
            try:
                values = dict(
                    user_id=user_id,
                    import_id=import_id,
                    source=parsed.source,
                    source_file=session.source_file,
                    datauuid=session.datauuid,
                    deviceuuid=session.deviceuuid,
                    start_time=parse_dt(session.start_time),
                    end_time=parse_dt(session.end_time),
                    duration_seconds=int_or_none(session.duration_seconds),
                    sleep_score=session.sleep_score,
                    efficiency=session.efficiency,
                    raw_stage_summary=None,
                    raw_extra=session.raw_extra,
                )
                self._upsert(
                    db,
                    HealthSleepSession,
                    [
                        {"user_id": user_id, "datauuid": session.datauuid},
                        {"user_id": user_id, "start_time": values["start_time"], "end_time": values["end_time"], "source": parsed.source},
                    ],
                    values,
                    "sleep_sessions",
                    saved,
                    duplicates,
                )
            except Exception:
                failed["sleep_sessions"] += 1

    def _store_body_profile(self, db: Session, user_id: UUID, import_id: UUID, parsed, saved, duplicates, failed) -> None:
        for measurement in parsed.body_profile.measurements:
            try:
                values = dict(
                    user_id=user_id,
                    import_id=import_id,
                    source=parsed.source,
                    source_file=measurement.source_file,
                    datauuid=measurement.datauuid,
                    deviceuuid=measurement.deviceuuid,
                    measurement_type=measurement.type,
                    start_time=parse_dt(measurement.start_time),
                    height_cm=measurement.height_cm,
                    weight_kg=measurement.weight_kg,
                    body_fat_percent=measurement.body_fat_percent,
                    body_fat_mass=measurement.body_fat_mass,
                    skeletal_muscle=measurement.skeletal_muscle,
                    skeletal_muscle_mass=measurement.skeletal_muscle_mass,
                    muscle_mass=measurement.muscle_mass,
                    basal_metabolic_rate=measurement.basal_metabolic_rate,
                    total_body_water=measurement.total_body_water,
                    fat_free=measurement.fat_free,
                    fat_free_mass=measurement.fat_free_mass,
                    vfa_level=measurement.vfa_level,
                    raw_extra=measurement.raw_extra,
                )
                self._upsert(
                    db,
                    HealthBodyMeasurement,
                    [
                        {
                            "user_id": user_id,
                            "measurement_type": measurement.type,
                            "start_time": values["start_time"],
                            "datauuid": measurement.datauuid,
                        }
                    ],
                    values,
                    "body_measurements",
                    saved,
                    duplicates,
                )
            except Exception:
                failed["body_measurements"] += 1
        for entry in parsed.body_profile.user_profile:
            try:
                value_text = entry.value if isinstance(entry.value, str) else None
                value_number = entry.value if isinstance(entry.value, (int, float)) else None
                value_json = entry.value if isinstance(entry.value, (dict, list)) else None
                values = dict(
                    user_id=user_id,
                    import_id=import_id,
                    source=parsed.source,
                    source_file=entry.source_file,
                    datauuid=entry.datauuid,
                    deviceuuid=entry.deviceuuid,
                    profile_key=entry.key,
                    value_type=entry.value_type,
                    value_text=value_text,
                    value_number=value_number,
                    value_json=value_json,
                    create_time=parse_dt(entry.create_time),
                    update_time=parse_dt(entry.update_time),
                    raw_extra=entry.raw_extra,
                )
                self._upsert(
                    db,
                    HealthUserProfileEntry,
                    [{"user_id": user_id, "profile_key": entry.key, "datauuid": entry.datauuid}],
                    values,
                    "user_profile_entries",
                    saved,
                    duplicates,
                )
            except Exception:
                failed["user_profile_entries"] += 1

    def _store_device_profile(self, db: Session, user_id: UUID, import_id: UUID, parsed, saved, duplicates, failed) -> None:
        capability_by_parent = {cap.parent_datauuid: cap.model_dump(exclude_none=True) for cap in parsed.device_profile.capabilities}
        for device in parsed.device_profile.devices:
            try:
                values = dict(
                    user_id=user_id,
                    import_id=import_id,
                    source=parsed.source,
                    source_file=device.source_file,
                    datauuid=device.datauuid,
                    deviceuuid=device.deviceuuid,
                    name=device.name,
                    manufacturer=device.manufacturer,
                    model=device.model,
                    fixed_name=device.fixed_name,
                    device_group=device.device_group,
                    device_type=device.device_type,
                    connectivity_type=device.connectivity_type,
                    accessory_type=device.accessory_type,
                    step_source_group=device.step_source_group,
                    providing_step_goal=bool_or_none(device.providing_step_goal),
                    backsync_step_goal=bool_or_none(device.backsync_step_goal),
                    capability_ref=device.capability_ref,
                    capability_json=capability_by_parent.get(device.deviceuuid),
                    create_time=parse_dt(device.create_time),
                    update_time=parse_dt(device.update_time),
                    raw_extra=device.raw_extra,
                )
                self._upsert(
                    db,
                    HealthDeviceProfile,
                    [{"user_id": user_id, "deviceuuid": device.deviceuuid}],
                    values,
                    "device_profiles",
                    saved,
                    duplicates,
                )
            except Exception:
                failed["device_profiles"] += 1

    def _affected_dates(self, parsed: SamsungHealthImportResponse) -> set[date]:
        days: set[date] = set()
        for item in parsed.daily_health:
            parsed_date = parse_date(item.date)
            if parsed_date:
                days.add(parsed_date)
        for collection, attr in (
            (parsed.heart_rate.samples, "start_time"),
            (parsed.steps.intervals, "start_time"),
            (parsed.stress.samples, "start_time"),
            (parsed.exercise.sessions, "start_time"),
            (parsed.sleep.sessions, "start_time"),
        ):
            for record in collection:
                value = parse_dt(getattr(record, attr, None))
                if value:
                    days.add(value.date())
        return days
