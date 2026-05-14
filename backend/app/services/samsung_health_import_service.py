from __future__ import annotations

import re
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from io import BytesIO
from pathlib import PurePosixPath
from typing import Any

from app.schemas.health_import_schemas import (
    ActivityDaySummary,
    ActivityExtraData,
    ActivityLevelRecord,
    ActivitySection,
    AiTwinReadiness,
    BodyMeasurement,
    BodyProfileSection,
    DailyHealthSummary,
    DetectedHealthSignals,
    DeviceCapability,
    DeviceProfile,
    DeviceProfileSection,
    ExerciseLiveSample,
    ExerciseSection,
    ExerciseSession,
    HeartRatePeriod,
    HeartRateSample,
    HeartRateSection,
    ImportFileReport,
    SamsungHealthImportResponse,
    SamsungHealthPreviewResponse,
    SleepSection,
    SleepSession,
    StepDailySummary,
    StepInterval,
    StepsSection,
    StepTrendSample,
    StressHistogram,
    StressPeriod,
    StressSample,
    StressSection,
    TimeAggregate,
    TimelineEvent,
    UserProfileEntry,
)
from app.services.samsung_health_parsers.base import (
    average,
    date_bucket,
    duration_seconds,
    flatten_json_items,
    group_by,
    hour_bucket,
    limit_records,
    max_value,
    min_value,
    non_empty_raw,
    parent_id_from_json_file,
    parse_json_bytes,
    parse_samsung_csv,
    parse_samsung_date,
    parse_samsung_datetime,
    to_float,
    to_int,
)


MAX_UNCOMPRESSED_BYTES = 100 * 1024 * 1024
MAX_ZIP_FILES = 1000


class SamsungHealthImportError(Exception):
    status_code = 400
    message = "Invalid Samsung Health export ZIP"

    def __init__(self, message: str | None = None, status_code: int | None = None) -> None:
        self.message = message or self.message
        if status_code is not None:
            self.status_code = status_code


class InvalidSamsungZipError(SamsungHealthImportError):
    status_code = 400
    message = "Invalid Samsung Health export ZIP"


class UnsafeSamsungZipPathError(SamsungHealthImportError):
    status_code = 400
    message = "ZIP file contains unsafe paths"


class NoSupportedSamsungFilesError(SamsungHealthImportError):
    status_code = 422
    message = "No supported Samsung Health files found"


@dataclass(frozen=True)
class ImportOptions:
    include_raw_records: bool = True
    include_samples: bool = True
    include_raw_extra: bool = False
    sample_limit: int = 5000
    include_debug_files: bool = False


@dataclass(frozen=True)
class ZipEntry:
    name: str
    data: bytes
    kind: str


class SamsungHealthImportService:
    def preview(self, zip_bytes: bytes, include_debug_files: bool = False) -> SamsungHealthPreviewResponse:
        warnings: list[str] = []
        entries, unsupported = self._read_zip(zip_bytes, warnings)
        counts = Counter(entry.kind for entry in entries)
        record_counts = self._preview_record_counts(entries, warnings)
        detected = self._detected_from_entries(entries)
        debug_files = None
        if include_debug_files:
            debug_files = {
                "processed_candidates": [{"name": entry.name, "kind": entry.kind, "bytes": len(entry.data)} for entry in entries],
                "unsupported_count": len(unsupported),
            }
        return SamsungHealthPreviewResponse(
            supported_files=[entry.name for entry in entries],
            unsupported_files=unsupported,
            counts_by_file_type=dict(counts),
            record_counts=record_counts,
            detected=detected,
            warnings=warnings,
            debug_files=debug_files,
        )

    def parse(self, zip_bytes: bytes, options: ImportOptions) -> SamsungHealthImportResponse:
        warnings: list[str] = []
        entries, unsupported = self._read_zip(zip_bytes, warnings)
        if not entries:
            raise NoSupportedSamsungFilesError()

        processed = [entry.name for entry in entries]
        heart_rate = self._parse_heart_rate(entries, options, warnings)
        steps = self._parse_steps(entries, options, warnings)
        stress = self._parse_stress(entries, options, warnings)
        activity = self._parse_activity(entries, options, warnings)
        exercise = self._parse_exercise(entries, options, warnings)
        sleep = self._parse_sleep(entries, options, warnings)
        body_profile = self._parse_body_profile(entries, options, warnings)
        device_profile = self._parse_device_profile(entries, options, warnings)

        detected = DetectedHealthSignals(
            heart_rate=heart_rate.detected,
            steps=steps.detected,
            sleep=sleep.detected,
            stress=stress.detected,
            activity=activity.detected,
            exercise=exercise.detected,
            body_profile=body_profile.detected,
            device_profile=device_profile.detected,
        )
        daily_health = self._build_daily_health(heart_rate, steps, stress, activity, exercise, sleep)
        timeline_events = self._build_timeline_events(
            heart_rate, steps, stress, activity, exercise, sleep, options.sample_limit
        )
        readiness = self._compute_readiness(heart_rate, steps, stress, activity, exercise, sleep)
        return SamsungHealthImportResponse(
            ai_twin_ready=readiness.score >= 50 and (heart_rate.detected or steps.detected),
            ai_twin_readiness=readiness,
            detected=detected,
            files=ImportFileReport(processed=processed, unsupported=unsupported, warnings=warnings),
            heart_rate=heart_rate,
            steps=steps,
            stress=stress,
            activity=activity,
            exercise=exercise,
            sleep=sleep,
            body_profile=body_profile,
            device_profile=device_profile,
            daily_health=daily_health,
            timeline_events=timeline_events,
        )

    def _read_zip(self, zip_bytes: bytes, warnings: list[str]) -> tuple[list[ZipEntry], list[str]]:
        if not zipfile.is_zipfile(BytesIO(zip_bytes)):
            raise InvalidSamsungZipError()
        try:
            with zipfile.ZipFile(BytesIO(zip_bytes)) as archive:
                infos = [info for info in archive.infolist() if not info.is_dir()]
                if len(infos) > MAX_ZIP_FILES:
                    raise InvalidSamsungZipError("Too many files in ZIP")
                total_size = sum(info.file_size for info in infos)
                if total_size > MAX_UNCOMPRESSED_BYTES:
                    raise InvalidSamsungZipError("File too large")
                entries: list[ZipEntry] = []
                unsupported: list[str] = []
                for info in infos:
                    if self._is_unsafe_zip_path(info.filename):
                        raise UnsafeSamsungZipPathError()
                    normalized = info.filename.replace("\\", "/")
                    kind = self._classify_file(normalized)
                    if not kind:
                        unsupported.append(normalized)
                        continue
                    try:
                        entries.append(ZipEntry(name=normalized, data=archive.read(info), kind=kind))
                    except (OSError, zipfile.BadZipFile) as exc:
                        warnings.append(f"Could not read {normalized}: {exc}")
                return entries, unsupported
        except SamsungHealthImportError:
            raise
        except zipfile.BadZipFile as exc:
            raise InvalidSamsungZipError() from exc

    def _is_unsafe_zip_path(self, path: str) -> bool:
        if "\\" in path or path.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:", path):
            return True
        normalized = path.replace("\\", "/")
        parts = PurePosixPath(normalized).parts
        return any(part in {"..", ""} for part in parts)

    def _classify_file(self, name: str) -> str | None:
        lower = name.lower()
        base = PurePosixPath(lower).name
        if not (lower.endswith(".csv") or lower.endswith(".json")):
            return None
        if "sleep" in lower:
            return "sleep_json" if lower.endswith(".json") else "sleep_csv"
        if base.startswith("com.samsung.health.heart_rate.") and lower.endswith(".csv"):
            return "heart_rate_csv"
        if lower.startswith("jsons/com.samsung.health.heart_rate/") and lower.endswith(".binning_data.json"):
            return "heart_rate_json"
        if base.startswith("com.samsung.health.step_count.") and lower.endswith(".csv"):
            return "step_interval_csv"
        if base.startswith("com.samsung.shealth.tracker.pedometer_day_summary.") and lower.endswith(".csv"):
            return "pedometer_daily_csv"
        if base.startswith("com.samsung.shealth.step_daily_trend.") and lower.endswith(".csv"):
            return "step_daily_trend_csv"
        if lower.startswith("jsons/com.samsung.shealth.tracker.pedometer_day_summary/") and lower.endswith(
            ".binning_data.json"
        ):
            return "pedometer_daily_json"
        if lower.startswith("jsons/com.samsung.shealth.step_daily_trend/") and lower.endswith(".binning_data.json"):
            return "step_daily_trend_json"
        if base.startswith("com.samsung.shealth.stress.histogram.") and lower.endswith(".csv"):
            return "stress_histogram_csv"
        if lower.startswith("jsons/com.samsung.shealth.stress.histogram/") and lower.endswith(".histogram.json"):
            return "stress_histogram_json"
        if base.startswith("com.samsung.shealth.stress.") and lower.endswith(".csv"):
            return "stress_csv"
        if lower.startswith("jsons/com.samsung.shealth.stress/") and lower.endswith(".binning_data.json"):
            return "stress_json"
        if base.startswith("com.samsung.shealth.activity.day_summary.") and lower.endswith(".csv"):
            return "activity_day_csv"
        if lower.startswith("jsons/com.samsung.shealth.activity.day_summary/") and lower.endswith(".extra_data.json"):
            return "activity_extra_json"
        if base.startswith("com.samsung.shealth.activity_level.") and lower.endswith(".csv"):
            return "activity_level_csv"
        if base.startswith("com.samsung.shealth.stand_day_summary.") and lower.endswith(".csv"):
            return "stand_day_summary_csv"
        if base.startswith("com.samsung.shealth.floor_goal.") and lower.endswith(".csv"):
            return "floor_goal_csv"
        if base.startswith("com.samsung.health.exercise.") and lower.endswith(".csv"):
            return "exercise_csv"
        if lower.startswith("jsons/com.samsung.health.exercise/") and lower.endswith(".live_data.json"):
            return "exercise_live_json"
        if base.startswith("com.samsung.health.height.") and lower.endswith(".csv"):
            return "height_csv"
        if base.startswith("com.samsung.health.weight.") and lower.endswith(".csv"):
            return "weight_csv"
        if base.startswith("com.samsung.health.user_profile.") and lower.endswith(".csv"):
            return "user_profile_csv"
        if lower.startswith("jsons/com.samsung.health.user_profile/") and lower.endswith(".blob_value.json"):
            return "user_profile_blob_json"
        if base.startswith("com.samsung.health.device_profile.") and lower.endswith(".csv"):
            return "device_profile_csv"
        if lower.startswith("jsons/com.samsung.health.device_profile/") and lower.endswith(".capability.json"):
            return "device_capability_json"
        if base.startswith("com.samsung.shealth.tracker.pedometer_recommendation.") and lower.endswith(".csv"):
            return "pedometer_recommendation_csv"
        if any(token in base for token in ("permission", "preferences", "rewards")):
            return "debug_csv"
        return None

    def _detected_from_entries(self, entries: list[ZipEntry]) -> DetectedHealthSignals:
        kinds = {entry.kind for entry in entries}
        return DetectedHealthSignals(
            heart_rate=bool(kinds & {"heart_rate_csv", "heart_rate_json"}),
            steps=bool(
                kinds
                & {
                    "step_interval_csv",
                    "pedometer_daily_csv",
                    "step_daily_trend_csv",
                    "pedometer_daily_json",
                    "step_daily_trend_json",
                }
            ),
            sleep=any(k.startswith("sleep") for k in kinds),
            stress=bool(kinds & {"stress_csv", "stress_json", "stress_histogram_csv", "stress_histogram_json"}),
            activity=bool(
                kinds & {"activity_day_csv", "activity_extra_json", "activity_level_csv", "stand_day_summary_csv"}
            ),
            exercise=bool(kinds & {"exercise_csv", "exercise_live_json"}),
            body_profile=bool(kinds & {"height_csv", "weight_csv", "user_profile_csv", "user_profile_blob_json"}),
            device_profile=bool(kinds & {"device_profile_csv", "device_capability_json"}),
        )

    def _csv_rows(self, entry: ZipEntry, warnings: list[str]) -> list[dict[str, str]]:
        try:
            return parse_samsung_csv(entry.data, entry.name, warnings)
        except Exception as exc:
            warnings.append(f"Could not parse CSV {entry.name}: {exc}")
            return []

    def _preview_record_counts(self, entries: list[ZipEntry], warnings: list[str]) -> dict[str, int]:
        counts: Counter[str] = Counter()
        for entry in entries:
            if entry.name.lower().endswith(".csv"):
                counts[entry.kind] += len(self._csv_rows(entry, warnings))
            elif entry.name.lower().endswith(".json"):
                counts[entry.kind] += len(self._json_items(entry, warnings))
        return dict(counts)

    def _json_items(self, entry: ZipEntry, warnings: list[str]) -> list[dict[str, Any]]:
        try:
            return flatten_json_items(parse_json_bytes(entry.data))
        except Exception as exc:
            warnings.append(f"Malformed JSON file {entry.name}: {exc}")
            return []

    def _raw(self, row: dict[str, Any], include_raw_extra: bool, exclude: set[str] | None = None) -> dict[str, Any] | None:
        if not include_raw_extra:
            return None
        return non_empty_raw(row, exclude or set())

    def _parse_heart_rate(
        self, entries: list[ZipEntry], options: ImportOptions, warnings: list[str]
    ) -> HeartRateSection:
        periods: list[HeartRatePeriod] = []
        samples: list[HeartRateSample] = []
        malformed_json: list[str] = []
        for entry in entries:
            if entry.kind == "heart_rate_csv":
                for row in self._csv_rows(entry, warnings):
                    offset = to_int(row.get("time_offset"))
                    start = parse_samsung_datetime(row.get("start_time"), offset)
                    end = parse_samsung_datetime(row.get("end_time"), offset)
                    periods.append(
                        HeartRatePeriod(
                            datauuid=row.get("datauuid") or None,
                            deviceuuid=row.get("deviceuuid") or None,
                            package_name=row.get("pkg_name") or None,
                            start_time=start,
                            end_time=end,
                            avg_bpm=to_float(row.get("heart_rate")),
                            min_bpm=to_float(row.get("min")),
                            max_bpm=to_float(row.get("max")),
                            heart_beat_count=to_int(row.get("heart_beat_count")),
                            binning_data_ref=row.get("binning_data") or None,
                            time_offset_ms=offset,
                            create_time=parse_samsung_datetime(row.get("create_time"), offset),
                            update_time=parse_samsung_datetime(row.get("update_time"), offset),
                            create_sh_ver=row.get("create_sh_ver") or None,
                            modify_sh_ver=row.get("modify_sh_ver") or None,
                            client_data_id=row.get("client_data_id") or None,
                            client_data_ver=row.get("client_data_ver") or None,
                            comment=row.get("comment") or None,
                            source_file=entry.name,
                            raw_extra=self._raw(row, options.include_raw_extra),
                        )
                    )
            elif entry.kind == "heart_rate_json":
                parent = parent_id_from_json_file(entry.name, ".binning_data.json")
                items = self._json_items(entry, warnings)
                if not items:
                    malformed_json.append(entry.name)
                for item in items:
                    start = parse_samsung_datetime(item.get("start_time"))
                    end = parse_samsung_datetime(item.get("end_time"))
                    samples.append(
                        HeartRateSample(
                            parent_datauuid=parent,
                            parent_binning_data_ref=f"{parent}.binning_data" if parent else None,
                            source_json_file=entry.name,
                            start_time=start,
                            end_time=end,
                            duration_seconds=duration_seconds(start, end),
                            bpm=to_float(item.get("heart_rate") or item.get("bpm")),
                            min_bpm=to_float(item.get("heart_rate_min") or item.get("min")),
                            max_bpm=to_float(item.get("heart_rate_max") or item.get("max")),
                            raw_extra=self._raw(item, options.include_raw_extra),
                        )
                    )

        linked = 0
        period_refs = {period.binning_data_ref for period in periods if period.binning_data_ref}
        period_ids = {period.datauuid for period in periods if period.datauuid}
        for sample in samples:
            if sample.parent_binning_data_ref in period_refs or sample.parent_datauuid in period_ids:
                linked += 1
        hourly = self._heart_rate_aggregates(samples, "hour")
        daily = self._heart_rate_aggregates(samples, "day")
        hr_values = [sample.bpm for sample in samples] or [period.avg_bpm for period in periods]
        times = [time for sample in samples for time in (sample.start_time, sample.end_time) if time]
        period_without_json = [
            period.datauuid
            for period in periods
            if period.binning_data_ref and period.binning_data_ref not in {sample.parent_binning_data_ref for sample in samples}
        ]
        returned_periods, periods_truncated = limit_records(periods, options.include_raw_records, options.sample_limit)
        returned_samples, samples_truncated = limit_records(
            samples, options.include_raw_records and options.include_samples, options.sample_limit
        )
        analysis = self._heart_rate_analysis(samples)
        return HeartRateSection(
            detected=bool(periods or samples),
            summary={
                "period_count": len(periods),
                "sample_count": len(samples),
                "avg_bpm": average(hr_values),
                "min_bpm": min_value([sample.min_bpm or sample.bpm for sample in samples] or [period.min_bpm for period in periods]),
                "max_bpm": max_value([sample.max_bpm or sample.bpm for sample in samples] or [period.max_bpm for period in periods]),
                "first_record_time": min(times) if times else None,
                "last_record_time": max(times) if times else None,
                "devices": sorted({period.deviceuuid for period in periods if period.deviceuuid}),
            },
            periods=returned_periods,
            samples=returned_samples,
            hourly_aggregates=hourly,
            daily_aggregates=daily,
            analysis=analysis,
            data_quality={
                "has_period_csv": bool(periods),
                "has_binning_json": bool(samples),
                "linked_sample_count": linked,
                "unlinked_sample_count": len(samples) - linked,
                "periods_without_json": period_without_json,
                "malformed_json_files": malformed_json,
                "total_record_count": len(periods) + len(samples),
                "returned_record_count": len(returned_periods) + len(returned_samples),
                "samples_truncated": periods_truncated or samples_truncated,
            },
        )

    def _heart_rate_aggregates(self, samples: list[HeartRateSample], mode: str) -> list[TimeAggregate]:
        key_fn = hour_bucket if mode == "hour" else date_bucket
        result: list[TimeAggregate] = []
        for bucket, rows in sorted(group_by(samples, lambda sample: key_fn(sample.start_time)).items()):
            values = [row.bpm for row in rows]
            result.append(
                TimeAggregate(
                    hour=bucket if mode == "hour" else None,
                    date=bucket if mode == "day" else None,
                    avg_bpm=average(values),
                    min_bpm=min_value([row.min_bpm or row.bpm for row in rows]),
                    max_bpm=max_value([row.max_bpm or row.bpm for row in rows]),
                    sample_count=len(rows),
                    high_bpm_count=sum(1 for row in rows if row.bpm is not None and row.bpm >= 120),
                    low_bpm_count=sum(1 for row in rows if row.bpm is not None and row.bpm <= 50),
                )
            )
        return result

    def _heart_rate_analysis(self, samples: list[HeartRateSample]) -> dict[str, Any]:
        high = [sample for sample in samples if sample.bpm is not None and sample.bpm >= 120]
        very_high = [sample for sample in samples if sample.bpm is not None and sample.bpm >= 140]
        low = [sample for sample in samples if sample.bpm is not None and sample.bpm <= 50]
        resting = [sample for sample in samples if sample.bpm is not None and sample.bpm <= 90]
        spikes: list[dict[str, Any]] = []
        previous: HeartRateSample | None = None
        for sample in sorted(samples, key=lambda item: item.start_time or ""):
            if previous and sample.bpm is not None and previous.bpm is not None and abs(sample.bpm - previous.bpm) >= 25:
                spikes.append(
                    {
                        "label": "possible_activity_spike",
                        "start_time": sample.start_time,
                        "bpm": sample.bpm,
                        "previous_bpm": previous.bpm,
                        "delta_bpm": round(sample.bpm - previous.bpm, 2),
                    }
                )
            previous = sample
        timeline_density = [
            {"hour": aggregate.hour, "sample_count": aggregate.sample_count}
            for aggregate in self._heart_rate_aggregates(samples, "hour")
        ]
        return {
            "high_bpm_count": len(high),
            "very_high_bpm_count": len(very_high),
            "low_bpm_count": len(low),
            "high_bpm_intervals": [self._interval_dict(sample, "high_bpm_interval") for sample in high[:100]],
            "very_high_bpm_intervals": [self._interval_dict(sample, "very_high_bpm_interval") for sample in very_high[:100]],
            "low_bpm_intervals": [self._interval_dict(sample, "low_bpm_interval") for sample in low[:100]],
            "possible_resting_windows": [
                self._interval_dict(sample, "possible_resting_window") for sample in resting[:100]
            ],
            "possible_activity_spikes": spikes[:100],
            "bpm_variability": self._variability([sample.bpm for sample in samples if sample.bpm is not None]),
            "longest_high_bpm_window": self._longest_window(high),
            "timeline_density": timeline_density,
        }

    def _interval_dict(self, sample: HeartRateSample | StressSample, label: str) -> dict[str, Any]:
        value = getattr(sample, "bpm", None)
        if value is None:
            value = getattr(sample, "score", None)
        return {"label": label, "start_time": sample.start_time, "end_time": sample.end_time, "value": value}

    def _variability(self, values: list[float]) -> dict[str, Any]:
        if len(values) < 2:
            return {"sample_count": len(values)}
        deltas = [abs(values[index] - values[index - 1]) for index in range(1, len(values))]
        return {
            "sample_count": len(values),
            "average_absolute_delta": average(deltas),
            "max_absolute_delta": max_value(deltas),
        }

    def _longest_window(self, samples: list[HeartRateSample]) -> dict[str, Any]:
        if not samples:
            return {}
        ordered = sorted(samples, key=lambda item: item.start_time or "")
        longest = current = [ordered[0]]
        for sample in ordered[1:]:
            previous = current[-1]
            if previous.end_time and sample.start_time and previous.end_time >= sample.start_time:
                current.append(sample)
            else:
                if len(current) > len(longest):
                    longest = current
                current = [sample]
        if len(current) > len(longest):
            longest = current
        return {
            "label": "high_bpm_interval",
            "start_time": longest[0].start_time,
            "end_time": longest[-1].end_time,
            "sample_count": len(longest),
        }

    def _parse_steps(self, entries: list[ZipEntry], options: ImportOptions, warnings: list[str]) -> StepsSection:
        intervals: list[StepInterval] = []
        daily_summaries: list[StepDailySummary] = []
        trend_samples: list[StepTrendSample] = []
        recommendations: list[dict[str, Any]] = []
        for entry in entries:
            if entry.kind == "step_interval_csv":
                for row in self._csv_rows(entry, warnings):
                    offset = to_int(row.get("time_offset"))
                    start = parse_samsung_datetime(row.get("start_time"), offset)
                    end = parse_samsung_datetime(row.get("end_time"), offset)
                    intervals.append(
                        StepInterval(
                            datauuid=row.get("datauuid") or None,
                            deviceuuid=row.get("deviceuuid") or None,
                            package_name=row.get("pkg_name") or None,
                            start_time=start,
                            end_time=end,
                            duration_seconds=duration_seconds(start, end),
                            steps=to_int(row.get("count")),
                            distance_meters=to_float(row.get("distance")),
                            calories=to_float(row.get("calorie")),
                            speed=to_float(row.get("speed")),
                            sample_position_type=row.get("sample_position_type") or None,
                            time_offset_ms=offset,
                            create_time=parse_samsung_datetime(row.get("create_time"), offset),
                            update_time=parse_samsung_datetime(row.get("update_time"), offset),
                            source_file=entry.name,
                            raw_extra=self._raw(row, options.include_raw_extra),
                        )
                    )
            elif entry.kind in {"pedometer_daily_csv", "step_daily_trend_csv"}:
                for row in self._csv_rows(entry, warnings):
                    offset = to_int(row.get("time_offset"))
                    day_time = row.get("day_time")
                    daily_summaries.append(
                        StepDailySummary(
                            date=parse_samsung_date(day_time, offset),
                            day_time=parse_samsung_datetime(day_time, offset) or day_time,
                            step_count=to_int(row.get("step_count") or row.get("count")),
                            walk_step_count=to_int(row.get("walk_step_count")),
                            run_step_count=to_int(row.get("run_step_count")),
                            healthy_step=to_int(row.get("healthy_step")),
                            active_time=to_float(row.get("active_time")),
                            distance_meters=to_float(row.get("distance")),
                            calories=to_float(row.get("calorie")),
                            speed=to_float(row.get("speed")),
                            achievement=to_float(row.get("achievement")),
                            recommendation=row.get("recommendation") or None,
                            binning_data_ref=row.get("binning_data") or None,
                            source_package_name=row.get("source_package_name") or row.get("source_pkg_name") or None,
                            package_name=row.get("pkg_name") or None,
                            deviceuuid=row.get("deviceuuid") or None,
                            datauuid=row.get("datauuid") or None,
                            create_time=parse_samsung_datetime(row.get("create_time"), offset),
                            update_time=parse_samsung_datetime(row.get("update_time"), offset),
                            source_file=entry.name,
                            raw_extra=self._raw(row, options.include_raw_extra),
                        )
                    )
            elif entry.kind in {"pedometer_daily_json", "step_daily_trend_json"}:
                parent = parent_id_from_json_file(entry.name, ".binning_data.json")
                for item in self._json_items(entry, warnings):
                    start = parse_samsung_datetime(item.get("mStartTime") or item.get("start_time"))
                    trend_samples.append(
                        StepTrendSample(
                            parent_datauuid=parent,
                            source_json_file=entry.name,
                            start_time=start,
                            time_unit=item.get("mTimeUnit") or item.get("time_unit"),
                            steps=to_int(item.get("mStepCount") or item.get("count")),
                            walk_step_count=to_int(item.get("mWalkStepCount")),
                            run_step_count=to_int(item.get("mRunStepCount")),
                            distance_meters=to_float(item.get("mDistance") or item.get("distance")),
                            calories=to_float(item.get("mCalorie") or item.get("calorie")),
                            speed=to_float(item.get("mSpeed") or item.get("speed")),
                            raw_extra=self._raw(item, options.include_raw_extra),
                        )
                    )
            elif entry.kind == "pedometer_recommendation_csv":
                for row in self._csv_rows(entry, warnings):
                    recommendations.append(self._raw(row, True) or {})

        hourly = self._steps_hourly(intervals, trend_samples)
        daily = self._steps_daily(intervals, daily_summaries, trend_samples)
        returned_intervals, interval_truncated = limit_records(intervals, options.include_raw_records, options.sample_limit)
        returned_daily, daily_truncated = limit_records(daily_summaries, options.include_raw_records, options.sample_limit)
        returned_trends, trend_truncated = limit_records(
            trend_samples, options.include_raw_records and options.include_samples, options.sample_limit
        )
        total_steps = sum(value for value in [row.steps for row in intervals] if value is not None)
        if not total_steps:
            total_steps = sum(value for value in [row.step_count for row in daily_summaries] if value is not None)
        return StepsSection(
            detected=bool(intervals or daily_summaries or trend_samples),
            summary={
                "interval_count": len(intervals),
                "daily_record_count": len(daily_summaries),
                "trend_sample_count": len(trend_samples),
                "total_steps_detected": total_steps,
                "total_distance_meters_detected": sum(
                    value for value in [row.distance_meters for row in intervals] if value is not None
                ),
                "total_calories_detected": sum(value for value in [row.calories for row in intervals] if value is not None),
            },
            intervals=returned_intervals,
            daily_summaries=returned_daily,
            trend_samples=returned_trends,
            recommendations=recommendations if options.include_raw_records else [],
            hourly_aggregates=hourly,
            daily_aggregates=daily,
            data_quality={
                "total_record_count": len(intervals) + len(daily_summaries) + len(trend_samples),
                "returned_record_count": len(returned_intervals) + len(returned_daily) + len(returned_trends),
                "samples_truncated": interval_truncated or daily_truncated or trend_truncated,
                "has_interval_csv": bool(intervals),
                "has_daily_csv": bool(daily_summaries),
                "has_binning_json": bool(trend_samples),
            },
        )

    def _steps_hourly(self, intervals: list[StepInterval], trend_samples: list[StepTrendSample]) -> list[TimeAggregate]:
        rows: list[Any] = [row for row in intervals if row.start_time] + [row for row in trend_samples if row.start_time]
        result: list[TimeAggregate] = []
        for bucket, grouped in sorted(group_by(rows, lambda row: hour_bucket(row.start_time)).items()):
            result.append(
                TimeAggregate(
                    hour=bucket,
                    steps=sum((row.steps or 0) for row in grouped),
                    distance_meters=sum((row.distance_meters or 0) for row in grouped),
                    calories=sum((row.calories or 0) for row in grouped),
                    sample_count=len(grouped),
                )
            )
        return result

    def _steps_daily(
        self,
        intervals: list[StepInterval],
        daily_summaries: list[StepDailySummary],
        trend_samples: list[StepTrendSample],
    ) -> list[TimeAggregate]:
        by_date: dict[str, dict[str, Any]] = defaultdict(lambda: {"steps": 0, "distance": 0.0, "calories": 0.0, "count": 0})
        for row in intervals:
            key = date_bucket(row.start_time)
            if key:
                by_date[key]["steps"] += row.steps or 0
                by_date[key]["distance"] += row.distance_meters or 0
                by_date[key]["calories"] += row.calories or 0
                by_date[key]["count"] += 1
        for row in trend_samples:
            key = date_bucket(row.start_time)
            if key:
                by_date[key]["steps"] += row.steps or 0
                by_date[key]["distance"] += row.distance_meters or 0
                by_date[key]["calories"] += row.calories or 0
                by_date[key]["count"] += 1
        for row in daily_summaries:
            if row.date and row.date not in by_date:
                by_date[row.date] = {
                    "steps": row.step_count or 0,
                    "distance": row.distance_meters or 0.0,
                    "calories": row.calories or 0.0,
                    "count": 1,
                }
        return [
            TimeAggregate(
                date=date,
                steps=values["steps"],
                distance_meters=round(values["distance"], 3),
                calories=round(values["calories"], 3),
                sample_count=values["count"],
            )
            for date, values in sorted(by_date.items())
        ]

    def _parse_stress(self, entries: list[ZipEntry], options: ImportOptions, warnings: list[str]) -> StressSection:
        periods: list[StressPeriod] = []
        samples: list[StressSample] = []
        histogram_rows: dict[str, StressHistogram] = {}
        histogram_json: dict[str, dict[str, Any]] = {}
        for entry in entries:
            if entry.kind == "stress_csv":
                for row in self._csv_rows(entry, warnings):
                    offset = to_int(row.get("time_offset"))
                    periods.append(
                        StressPeriod(
                            datauuid=row.get("datauuid") or None,
                            deviceuuid=row.get("deviceuuid") or None,
                            package_name=row.get("pkg_name") or None,
                            start_time=parse_samsung_datetime(row.get("start_time"), offset),
                            end_time=parse_samsung_datetime(row.get("end_time"), offset),
                            score=to_float(row.get("score")),
                            min_score=to_float(row.get("min")),
                            max_score=to_float(row.get("max")),
                            algorithm=row.get("algorithm") or None,
                            tag_id=row.get("tag_id") or None,
                            binning_data_ref=row.get("binning_data") or None,
                            time_offset_ms=offset,
                            create_time=parse_samsung_datetime(row.get("create_time"), offset),
                            update_time=parse_samsung_datetime(row.get("update_time"), offset),
                            comment=row.get("comment") or None,
                            source_file=entry.name,
                            raw_extra=self._raw(row, options.include_raw_extra),
                        )
                    )
            elif entry.kind == "stress_json":
                parent = parent_id_from_json_file(entry.name, ".binning_data.json")
                for item in self._json_items(entry, warnings):
                    samples.append(
                        StressSample(
                            parent_datauuid=parent,
                            source_json_file=entry.name,
                            start_time=parse_samsung_datetime(item.get("start_time")),
                            end_time=parse_samsung_datetime(item.get("end_time")),
                            score=to_float(item.get("score")),
                            min_score=to_float(item.get("score_min") or item.get("min")),
                            max_score=to_float(item.get("score_max") or item.get("max")),
                            level=item.get("level"),
                            flag=item.get("flag"),
                            raw_extra=self._raw(item, options.include_raw_extra),
                        )
                    )
            elif entry.kind == "stress_histogram_csv":
                for row in self._csv_rows(entry, warnings):
                    datauuid = row.get("datauuid") or None
                    if datauuid:
                        histogram_rows[datauuid] = StressHistogram(
                            datauuid=datauuid,
                            deviceuuid=row.get("deviceuuid") or None,
                            base_hr=to_float(row.get("base_hr")),
                            histogram_ref=row.get("histogram") or None,
                            decay_time=parse_samsung_datetime(row.get("decay_time")),
                            source_file=entry.name,
                            raw_extra=self._raw(row, options.include_raw_extra),
                        )
            elif entry.kind == "stress_histogram_json":
                parent = parent_id_from_json_file(entry.name, ".histogram.json")
                items = self._json_items(entry, warnings)
                if items and parent:
                    histogram_json[parent] = items[0]
        histograms: list[StressHistogram] = []
        for datauuid, row in histogram_rows.items():
            payload = histogram_json.get(datauuid, {})
            row.version = to_int(payload.get("version"))
            values = payload.get("values")
            row.values = values if isinstance(values, list) else []
            row.source_json_file = f"jsons/com.samsung.shealth.stress.histogram/{datauuid}.histogram.json" if payload else None
            histograms.append(row)
        hourly = self._stress_aggregates(samples, "hour")
        daily = self._stress_aggregates(samples, "day")
        returned_periods, p_truncated = limit_records(periods, options.include_raw_records, options.sample_limit)
        returned_samples, s_truncated = limit_records(
            samples, options.include_raw_records and options.include_samples, options.sample_limit
        )
        returned_histograms, h_truncated = limit_records(histograms, options.include_raw_records, options.sample_limit)
        values = [row.score for row in samples] or [row.score for row in periods]
        return StressSection(
            detected=bool(periods or samples or histograms),
            summary={
                "period_count": len(periods),
                "sample_count": len(samples),
                "histogram_count": len(histograms),
                "avg_score": average(values),
                "min_score": min_value([row.min_score or row.score for row in samples] or [row.min_score for row in periods]),
                "max_score": max_value([row.max_score or row.score for row in samples] or [row.max_score for row in periods]),
            },
            periods=returned_periods,
            samples=returned_samples,
            histograms=returned_histograms,
            hourly_aggregates=hourly,
            daily_aggregates=daily,
            data_quality={
                "total_record_count": len(periods) + len(samples) + len(histograms),
                "returned_record_count": len(returned_periods) + len(returned_samples) + len(returned_histograms),
                "samples_truncated": p_truncated or s_truncated or h_truncated,
                "has_period_csv": bool(periods),
                "has_binning_json": bool(samples),
                "has_histogram": bool(histograms),
            },
        )

    def _stress_aggregates(self, samples: list[StressSample], mode: str) -> list[TimeAggregate]:
        key_fn = hour_bucket if mode == "hour" else date_bucket
        result: list[TimeAggregate] = []
        for bucket, rows in sorted(group_by(samples, lambda sample: key_fn(sample.start_time)).items()):
            result.append(
                TimeAggregate(
                    hour=bucket if mode == "hour" else None,
                    date=bucket if mode == "day" else None,
                    avg_score=average([row.score for row in rows]),
                    min_score=min_value([row.min_score or row.score for row in rows]),
                    max_score=max_value([row.max_score or row.score for row in rows]),
                    sample_count=len(rows),
                )
            )
        return result

    def _parse_activity(self, entries: list[ZipEntry], options: ImportOptions, warnings: list[str]) -> ActivitySection:
        day_summaries: list[ActivityDaySummary] = []
        extras: list[ActivityExtraData] = []
        levels: list[ActivityLevelRecord] = []
        stand_summaries: list[dict[str, Any]] = []
        goals: list[dict[str, Any]] = []
        for entry in entries:
            if entry.kind == "activity_day_csv":
                for row in self._csv_rows(entry, warnings):
                    day = row.get("day_time")
                    day_summaries.append(
                        ActivityDaySummary(
                            date=parse_samsung_date(day),
                            day_time=parse_samsung_datetime(day) or day,
                            step_count=to_int(row.get("step_count")),
                            distance_meters=to_float(row.get("distance")),
                            calories=to_float(row.get("calorie")),
                            active_time=to_float(row.get("active_time")),
                            walk_time=to_float(row.get("walk_time")),
                            run_time=to_float(row.get("run_time")),
                            exercise_time=to_float(row.get("exercise_time")),
                            dynamic_active_time=to_float(row.get("dynamic_active_time")),
                            longest_active_time=to_float(row.get("longest_active_time")),
                            longest_idle_time=to_float(row.get("longest_idle_time")),
                            move_hourly_count=to_int(row.get("move_hourly_count")),
                            floor_count=to_int(row.get("floor_count")),
                            score=to_float(row.get("score")),
                            goal=to_float(row.get("goal")),
                            target=to_float(row.get("target")),
                            movement_type=row.get("movement_type") or None,
                            energy_type=row.get("energy_type") or None,
                            extra_data_ref=row.get("extra_data") or None,
                            deviceuuid=row.get("deviceuuid") or None,
                            datauuid=row.get("datauuid") or None,
                            source_file=entry.name,
                            raw_extra=self._raw(row, options.include_raw_extra),
                        )
                    )
            elif entry.kind == "activity_extra_json":
                parent = parent_id_from_json_file(entry.name, ".extra_data.json")
                for item in self._json_items(entry, warnings):
                    extras.append(
                        ActivityExtraData(
                            parent_datauuid=parent,
                            mMostActiveMinutes=item.get("mMostActiveMinutes"),
                            mActivityList=item.get("mActivityList"),
                            mUnitDataList=item.get("mUnitDataList"),
                            mIsGoalAchieved=item.get("mIsGoalAchieved"),
                            mStreakDayCount=to_int(item.get("mStreakDayCount")),
                            mAdaptiveGoal=item.get("mAdaptiveGoal"),
                            raw_extra=self._raw(item, options.include_raw_extra),
                        )
                    )
            elif entry.kind == "activity_level_csv":
                for row in self._csv_rows(entry, warnings):
                    offset = to_int(row.get("time_offset"))
                    levels.append(
                        ActivityLevelRecord(
                            datauuid=row.get("datauuid") or None,
                            deviceuuid=row.get("deviceuuid") or None,
                            package_name=row.get("pkg_name") or None,
                            activity_level=row.get("activity_level") or None,
                            start_time=parse_samsung_datetime(row.get("start_time"), offset),
                            time_offset_ms=offset,
                            create_time=parse_samsung_datetime(row.get("create_time"), offset),
                            update_time=parse_samsung_datetime(row.get("update_time"), offset),
                            source_file=entry.name,
                            raw_extra=self._raw(row, options.include_raw_extra),
                        )
                    )
            elif entry.kind == "stand_day_summary_csv":
                for row in self._csv_rows(entry, warnings):
                    stand_summaries.append(self._raw(row, True) or {})
            elif entry.kind == "floor_goal_csv":
                for row in self._csv_rows(entry, warnings):
                    goals.append(self._raw(row, True) or {})
        returned_days, d_truncated = limit_records(day_summaries, options.include_raw_records, options.sample_limit)
        returned_extras, e_truncated = limit_records(extras, options.include_raw_records, options.sample_limit)
        returned_levels, l_truncated = limit_records(levels, options.include_raw_records, options.sample_limit)
        return ActivitySection(
            detected=bool(day_summaries or extras or levels or stand_summaries or goals),
            summary={
                "day_summary_count": len(day_summaries),
                "activity_extra_count": len(extras),
                "activity_level_count": len(levels),
                "stand_summary_count": len(stand_summaries),
                "goal_count": len(goals),
            },
            day_summaries=returned_days,
            extra_data=returned_extras,
            activity_levels=returned_levels,
            stand_summaries=stand_summaries if options.include_raw_records else [],
            goals=goals if options.include_raw_records else [],
            data_quality={
                "total_record_count": len(day_summaries) + len(extras) + len(levels) + len(stand_summaries) + len(goals),
                "returned_record_count": len(returned_days) + len(returned_extras) + len(returned_levels),
                "samples_truncated": d_truncated or e_truncated or l_truncated,
            },
        )

    def _parse_exercise(self, entries: list[ZipEntry], options: ImportOptions, warnings: list[str]) -> ExerciseSection:
        sessions: list[ExerciseSession] = []
        live_samples: list[ExerciseLiveSample] = []
        for entry in entries:
            if entry.kind == "exercise_csv":
                for row in self._csv_rows(entry, warnings):
                    offset = to_int(row.get("time_offset"))
                    start = parse_samsung_datetime(row.get("start_time"), offset)
                    end = parse_samsung_datetime(row.get("end_time"), offset)
                    sessions.append(
                        ExerciseSession(
                            datauuid=row.get("datauuid") or None,
                            deviceuuid=row.get("deviceuuid") or None,
                            package_name=row.get("pkg_name") or None,
                            start_time=start,
                            end_time=end,
                            duration_seconds=to_float(row.get("duration")) or duration_seconds(start, end),
                            exercise_type=row.get("exercise_type") or None,
                            exercise_custom_type=row.get("exercise_custom_type") or None,
                            calories=to_float(row.get("calorie")),
                            distance_meters=to_float(row.get("distance")),
                            count=to_float(row.get("count")),
                            count_type=row.get("count_type") or None,
                            mean_heart_rate=to_float(row.get("mean_heart_rate")),
                            min_heart_rate=to_float(row.get("min_heart_rate")),
                            max_heart_rate=to_float(row.get("max_heart_rate")),
                            mean_speed=to_float(row.get("mean_speed")),
                            max_speed=to_float(row.get("max_speed")),
                            mean_cadence=to_float(row.get("mean_cadence")),
                            max_cadence=to_float(row.get("max_cadence")),
                            mean_power=to_float(row.get("mean_power")),
                            max_power=to_float(row.get("max_power")),
                            vo2_max=to_float(row.get("vo2_max")),
                            altitude_gain=to_float(row.get("altitude_gain")),
                            altitude_loss=to_float(row.get("altitude_loss")),
                            max_altitude=to_float(row.get("max_altitude")),
                            min_altitude=to_float(row.get("min_altitude")),
                            incline_distance=to_float(row.get("incline_distance")),
                            decline_distance=to_float(row.get("decline_distance")),
                            sweat_loss=to_float(row.get("sweat_loss")),
                            live_data_ref=row.get("live_data") or None,
                            location_data_ref=row.get("location_data") or None,
                            additional_ref=row.get("additional") or None,
                            auxiliary_devices=row.get("auxiliary_devices") or None,
                            create_time=parse_samsung_datetime(row.get("create_time"), offset),
                            update_time=parse_samsung_datetime(row.get("update_time"), offset),
                            source_file=entry.name,
                            raw_extra=self._raw(row, options.include_raw_extra),
                        )
                    )
            elif entry.kind == "exercise_live_json":
                parent = parent_id_from_json_file(entry.name, ".live_data.json")
                for item in self._json_items(entry, warnings):
                    live_samples.append(
                        ExerciseLiveSample(
                            parent_datauuid=parent,
                            source_json_file=entry.name,
                            start_time=parse_samsung_datetime(item.get("start_time")),
                            heart_rate=to_float(item.get("heart_rate")),
                            speed=to_float(item.get("speed")),
                            distance=to_float(item.get("distance")),
                            cadence=to_float(item.get("cadence")),
                            raw_extra=self._raw(item, options.include_raw_extra),
                        )
                    )
        returned_sessions, s_truncated = limit_records(sessions, options.include_raw_records, options.sample_limit)
        returned_live, l_truncated = limit_records(
            live_samples, options.include_raw_records and options.include_samples, options.sample_limit
        )
        return ExerciseSection(
            detected=bool(sessions or live_samples),
            summary={
                "session_count": len(sessions),
                "live_sample_count": len(live_samples),
                "total_calories": sum(row.calories or 0 for row in sessions),
                "total_distance_meters": sum(row.distance_meters or 0 for row in sessions),
            },
            sessions=returned_sessions,
            live_samples=returned_live,
            data_quality={
                "total_record_count": len(sessions) + len(live_samples),
                "returned_record_count": len(returned_sessions) + len(returned_live),
                "samples_truncated": s_truncated or l_truncated,
            },
        )

    def _parse_sleep(self, entries: list[ZipEntry], options: ImportOptions, warnings: list[str]) -> SleepSection:
        sessions: list[SleepSession] = []
        stages: list[dict[str, Any]] = []
        for entry in entries:
            if entry.kind == "sleep_csv":
                for row in self._csv_rows(entry, warnings):
                    offset = to_int(row.get("time_offset"))
                    start = parse_samsung_datetime(row.get("start_time"), offset)
                    end = parse_samsung_datetime(row.get("end_time"), offset)
                    sessions.append(
                        SleepSession(
                            datauuid=row.get("datauuid") or None,
                            deviceuuid=row.get("deviceuuid") or None,
                            start_time=start,
                            end_time=end,
                            duration_seconds=to_float(row.get("duration")) or duration_seconds(start, end),
                            sleep_score=to_float(row.get("sleep_score")),
                            efficiency=to_float(row.get("efficiency")),
                            stage=row.get("stage") or row.get("sleep_stage") or None,
                            source_file=entry.name,
                            raw_extra=self._raw(row, options.include_raw_extra),
                        )
                    )
            elif entry.kind == "sleep_json":
                for item in self._json_items(entry, warnings):
                    stages.append(self._raw(item, True) or {})
        returned_sessions, s_truncated = limit_records(sessions, options.include_raw_records, options.sample_limit)
        if not sessions and not stages:
            return SleepSection(
                detected=False,
                summary={"session_count": 0},
                message="No sleep files found in this Samsung Health export.",
                data_quality={"total_record_count": 0, "returned_record_count": 0, "samples_truncated": False},
            )
        return SleepSection(
            detected=True,
            summary={"session_count": len(sessions), "stage_record_count": len(stages)},
            sessions=returned_sessions,
            stages=stages[: options.sample_limit] if options.include_raw_records and options.include_samples else [],
            data_quality={
                "total_record_count": len(sessions) + len(stages),
                "returned_record_count": len(returned_sessions),
                "samples_truncated": s_truncated or len(stages) > options.sample_limit,
            },
        )

    def _parse_body_profile(
        self, entries: list[ZipEntry], options: ImportOptions, warnings: list[str]
    ) -> BodyProfileSection:
        measurements: list[BodyMeasurement] = []
        profiles: list[UserProfileEntry] = []
        blob_values: dict[str, Any] = {}
        for entry in entries:
            if entry.kind == "user_profile_blob_json":
                parent = parent_id_from_json_file(entry.name, ".blob_value.json")
                items = self._json_items(entry, warnings)
                if parent and items:
                    blob_values[parent] = items[0]
        for entry in entries:
            if entry.kind == "height_csv":
                for row in self._csv_rows(entry, warnings):
                    offset = to_int(row.get("time_offset"))
                    measurements.append(
                        BodyMeasurement(
                            type="height",
                            start_time=parse_samsung_datetime(row.get("start_time"), offset),
                            height_cm=to_float(row.get("height")),
                            deviceuuid=row.get("deviceuuid") or None,
                            datauuid=row.get("datauuid") or None,
                            source_file=entry.name,
                            raw_extra=self._raw(row, options.include_raw_extra),
                        )
                    )
            elif entry.kind == "weight_csv":
                for row in self._csv_rows(entry, warnings):
                    offset = to_int(row.get("time_offset"))
                    has_composition = any(
                        row.get(key)
                        for key in (
                            "body_fat",
                            "body_fat_mass",
                            "skeletal_muscle",
                            "skeletal_muscle_mass",
                            "muscle_mass",
                            "total_body_water",
                        )
                    )
                    measurements.append(
                        BodyMeasurement(
                            type="body_composition" if has_composition else "weight",
                            start_time=parse_samsung_datetime(row.get("start_time"), offset),
                            height_cm=to_float(row.get("height")),
                            weight_kg=to_float(row.get("weight")),
                            body_fat_percent=to_float(row.get("body_fat")),
                            body_fat_mass=to_float(row.get("body_fat_mass")),
                            skeletal_muscle=to_float(row.get("skeletal_muscle")),
                            skeletal_muscle_mass=to_float(row.get("skeletal_muscle_mass")),
                            muscle_mass=to_float(row.get("muscle_mass")),
                            basal_metabolic_rate=to_float(row.get("basal_metabolic_rate")),
                            total_body_water=to_float(row.get("total_body_water")),
                            fat_free=to_float(row.get("fat_free")),
                            fat_free_mass=to_float(row.get("fat_free_mass")),
                            vfa_level=to_float(row.get("vfa_level")),
                            deviceuuid=row.get("deviceuuid") or None,
                            datauuid=row.get("datauuid") or None,
                            source_file=entry.name,
                            raw_extra=self._raw(row, options.include_raw_extra),
                        )
                    )
            elif entry.kind == "user_profile_csv":
                for row in self._csv_rows(entry, warnings):
                    datauuid = row.get("datauuid") or None
                    value, value_type = self._profile_value(row, blob_values.get(datauuid))
                    profiles.append(
                        UserProfileEntry(
                            key=row.get("key") or None,
                            value=value,
                            value_type=value_type,
                            deviceuuid=row.get("deviceuuid") or None,
                            datauuid=datauuid,
                            create_time=parse_samsung_datetime(row.get("create_time")),
                            update_time=parse_samsung_datetime(row.get("update_time")),
                            source_file=entry.name,
                            raw_extra=self._raw(row, options.include_raw_extra),
                        )
                    )
        returned_measurements, m_truncated = limit_records(measurements, options.include_raw_records, options.sample_limit)
        returned_profiles, p_truncated = limit_records(profiles, options.include_raw_records, options.sample_limit)
        return BodyProfileSection(
            detected=bool(measurements or profiles),
            summary={"measurement_count": len(measurements), "user_profile_entry_count": len(profiles)},
            measurements=returned_measurements,
            user_profile=returned_profiles,
            data_quality={
                "total_record_count": len(measurements) + len(profiles),
                "returned_record_count": len(returned_measurements) + len(returned_profiles),
                "samples_truncated": m_truncated or p_truncated,
            },
        )

    def _profile_value(self, row: dict[str, str], blob_value: Any) -> tuple[Any, str | None]:
        for key, value_type in (
            ("text_value", "text"),
            ("double_value", "double"),
            ("float_value", "float"),
            ("int_value", "int"),
            ("long_value", "long"),
        ):
            value = row.get(key)
            if value not in (None, ""):
                if value_type in {"double", "float"}:
                    return to_float(value), value_type
                if value_type in {"int", "long"}:
                    return to_int(value), value_type
                return value, value_type
        if blob_value is not None:
            return blob_value, "blob"
        return None, None

    def _parse_device_profile(
        self, entries: list[ZipEntry], options: ImportOptions, warnings: list[str]
    ) -> DeviceProfileSection:
        devices: list[DeviceProfile] = []
        capabilities: list[DeviceCapability] = []
        for entry in entries:
            if entry.kind == "device_profile_csv":
                for row in self._csv_rows(entry, warnings):
                    devices.append(
                        DeviceProfile(
                            datauuid=row.get("datauuid") or None,
                            deviceuuid=row.get("deviceuuid") or None,
                            name=row.get("name") or None,
                            manufacturer=row.get("manufacturer") or None,
                            model=row.get("model") or None,
                            fixed_name=row.get("fixed_name") or None,
                            device_group=row.get("device_group") or None,
                            device_type=row.get("device_type") or None,
                            connectivity_type=row.get("connectivity_type") or None,
                            accessory_type=row.get("accessory_type") or None,
                            step_source_group=row.get("step_source_group") or None,
                            providing_step_goal=row.get("providing_step_goal") or None,
                            backsync_step_goal=row.get("backsync_step_goal") or None,
                            capability_ref=row.get("capability") or None,
                            create_time=parse_samsung_datetime(row.get("create_time")),
                            update_time=parse_samsung_datetime(row.get("update_time")),
                            source_file=entry.name,
                            raw_extra=self._raw(row, options.include_raw_extra),
                        )
                    )
            elif entry.kind == "device_capability_json":
                parent = parent_id_from_json_file(entry.name, ".capability.json")
                for item in self._json_items(entry, warnings):
                    capabilities.append(
                        DeviceCapability(
                            parent_datauuid=parent,
                            protocol_feature=item.get("protocol_feature"),
                            model_name=item.get("model_name") or item.get("modelName"),
                            wearable_message=item.get("wearable_message"),
                            wearable_health_version=item.get("wearable_health_version"),
                            receiver=item.get("receiver"),
                            device_type=item.get("device_type"),
                            config=item.get("config"),
                            raw_extra=self._raw(item, options.include_raw_extra),
                        )
                    )
        returned_devices, d_truncated = limit_records(devices, options.include_raw_records, options.sample_limit)
        returned_capabilities, c_truncated = limit_records(capabilities, options.include_raw_records, options.sample_limit)
        return DeviceProfileSection(
            detected=bool(devices or capabilities),
            summary={"device_count": len(devices), "capability_count": len(capabilities)},
            devices=returned_devices,
            capabilities=returned_capabilities,
            data_quality={
                "total_record_count": len(devices) + len(capabilities),
                "returned_record_count": len(returned_devices) + len(returned_capabilities),
                "samples_truncated": d_truncated or c_truncated,
            },
        )

    def _build_daily_health(
        self,
        heart_rate: HeartRateSection,
        steps: StepsSection,
        stress: StressSection,
        activity: ActivitySection,
        exercise: ExerciseSection,
        sleep: SleepSection,
    ) -> list[DailyHealthSummary]:
        daily: dict[str, dict[str, Any]] = defaultdict(lambda: {"data_sources": set()})
        for aggregate in heart_rate.daily_aggregates:
            if aggregate.date:
                row = daily[aggregate.date]
                row.update(
                    avg_heart_rate=aggregate.avg_bpm,
                    min_heart_rate=aggregate.min_bpm,
                    max_heart_rate=aggregate.max_bpm,
                    heart_rate_sample_count=aggregate.sample_count,
                    high_bpm_count=aggregate.high_bpm_count,
                    low_bpm_count=aggregate.low_bpm_count,
                )
                row["data_sources"].add("heart_rate")
        for aggregate in steps.daily_aggregates:
            if aggregate.date:
                row = daily[aggregate.date]
                row["steps"] = aggregate.steps
                row["distance_meters"] = aggregate.distance_meters
                row["calories"] = aggregate.calories
                row["data_sources"].add("steps")
        for summary in steps.daily_summaries:
            if summary.date:
                row = daily[summary.date]
                row["steps"] = summary.step_count if summary.step_count is not None else row.get("steps")
                row["walking_steps"] = summary.walk_step_count
                row["running_steps"] = summary.run_step_count
                row["active_time_seconds"] = summary.active_time
                row["data_sources"].add("steps")
        for aggregate in stress.daily_aggregates:
            if aggregate.date:
                row = daily[aggregate.date]
                row.update(
                    stress_avg_score=aggregate.avg_score,
                    stress_min_score=aggregate.min_score,
                    stress_max_score=aggregate.max_score,
                    stress_sample_count=aggregate.sample_count,
                )
                row["data_sources"].add("stress")
        for summary in activity.day_summaries:
            if summary.date:
                row = daily[summary.date]
                row.update(
                    active_time_seconds=summary.active_time,
                    walk_time_seconds=summary.walk_time,
                    run_time_seconds=summary.run_time,
                    exercise_time_seconds=summary.exercise_time,
                    floor_count=summary.floor_count,
                )
                if row.get("steps") is None:
                    row["steps"] = summary.step_count
                if row.get("distance_meters") is None:
                    row["distance_meters"] = summary.distance_meters
                if row.get("calories") is None:
                    row["calories"] = summary.calories
                row["data_sources"].add("activity")
        exercise_by_day: dict[str, list[ExerciseSession]] = group_by(
            exercise.sessions, lambda session: date_bucket(session.start_time)
        )
        for date, sessions in exercise_by_day.items():
            row = daily[date]
            row["exercise_sessions_count"] = len(sessions)
            row["exercise_calories"] = sum(session.calories or 0 for session in sessions)
            row["data_sources"].add("exercise")
        for session in sleep.sessions:
            date = date_bucket(session.start_time)
            if date:
                row = daily[date]
                row["sleep_minutes"] = (session.duration_seconds / 60) if session.duration_seconds else None
                row["sleep_score"] = session.sleep_score
                row["data_sources"].add("sleep")
        return [
            DailyHealthSummary(date=date, data_sources=sorted(values.pop("data_sources")), **values)
            for date, values in sorted(daily.items())
        ]

    def _build_timeline_events(
        self,
        heart_rate: HeartRateSection,
        steps: StepsSection,
        stress: StressSection,
        activity: ActivitySection,
        exercise: ExerciseSection,
        sleep: SleepSection,
        limit: int,
    ) -> list[TimelineEvent]:
        events: list[TimelineEvent] = []
        for sample in heart_rate.samples:
            events.append(
                TimelineEvent(
                    type="heart_rate_sample",
                    start_time=sample.start_time,
                    end_time=sample.end_time,
                    date=date_bucket(sample.start_time),
                    value=sample.bpm,
                    label="Heart rate sample",
                    source="samsung_health_heart_rate",
                    datauuid=sample.parent_datauuid,
                    metadata={"min_bpm": sample.min_bpm, "max_bpm": sample.max_bpm},
                )
            )
        for interval in steps.intervals:
            events.append(
                TimelineEvent(
                    type="step_interval",
                    start_time=interval.start_time,
                    end_time=interval.end_time,
                    date=date_bucket(interval.start_time),
                    value=interval.steps,
                    label="Step interval",
                    source="samsung_health_steps",
                    datauuid=interval.datauuid,
                    deviceuuid=interval.deviceuuid,
                    metadata={"distance_meters": interval.distance_meters, "calories": interval.calories},
                )
            )
        for sample in stress.samples:
            events.append(
                TimelineEvent(
                    type="stress_sample",
                    start_time=sample.start_time,
                    end_time=sample.end_time,
                    date=date_bucket(sample.start_time),
                    value=sample.score,
                    label="Samsung Health stress score",
                    source="samsung_health_stress",
                    datauuid=sample.parent_datauuid,
                    metadata={"level": sample.level, "flag": sample.flag},
                )
            )
        for session in exercise.sessions:
            events.append(
                TimelineEvent(
                    type="exercise_session",
                    start_time=session.start_time,
                    end_time=session.end_time,
                    date=date_bucket(session.start_time),
                    value=session.exercise_type,
                    label="Exercise session",
                    source="samsung_health_exercise",
                    datauuid=session.datauuid,
                    deviceuuid=session.deviceuuid,
                    metadata={"calories": session.calories, "distance_meters": session.distance_meters},
                )
            )
        for summary in activity.day_summaries:
            events.append(
                TimelineEvent(
                    type="activity_summary",
                    start_time=summary.day_time,
                    date=summary.date,
                    value=summary.step_count,
                    label="Activity day summary",
                    source="samsung_health_activity",
                    datauuid=summary.datauuid,
                    deviceuuid=summary.deviceuuid,
                    metadata={"active_time_seconds": summary.active_time, "floor_count": summary.floor_count},
                )
            )
        for session in sleep.sessions:
            events.append(
                TimelineEvent(
                    type="sleep_session",
                    start_time=session.start_time,
                    end_time=session.end_time,
                    date=date_bucket(session.start_time),
                    value=session.sleep_score,
                    label="Sleep session",
                    source="samsung_health_sleep",
                    datauuid=session.datauuid,
                    deviceuuid=session.deviceuuid,
                    metadata={"duration_seconds": session.duration_seconds, "efficiency": session.efficiency},
                )
            )
        return sorted(events, key=lambda event: event.start_time or event.date or "")[: max(limit, 0)]

    def _compute_readiness(
        self,
        heart_rate: HeartRateSection,
        steps: StepsSection,
        stress: StressSection,
        activity: ActivitySection,
        exercise: ExerciseSection,
        sleep: SleepSection,
    ) -> AiTwinReadiness:
        score = 0
        if heart_rate.summary.get("sample_count", 0) > 0:
            score += 35
        if steps.detected:
            score += 25
        if stress.detected:
            score += 15
        if activity.detected:
            score += 10
        if exercise.detected:
            score += 10
        if sleep.detected:
            score += 20
        score = min(score, 100)
        level = "high" if score >= 75 else "medium" if score >= 45 else "low"
        reason_parts = []
        if heart_rate.detected:
            reason_parts.append("detailed heart rate")
        if steps.detected:
            reason_parts.append("steps")
        if stress.detected:
            reason_parts.append("stress")
        if activity.detected:
            reason_parts.append("activity")
        if exercise.detected:
            reason_parts.append("exercise")
        if sleep.detected:
            reason_parts.append("sleep")
        if not sleep.detected:
            reason = (
                "Sleep data was not found in this export. AI twin can still be generated using "
                f"{', '.join(reason_parts) or 'available'} data, but sleep insights will be limited."
            )
        else:
            reason = f"AI twin inputs include {', '.join(reason_parts)} data."
        return AiTwinReadiness(score=score, level=level, reason=reason)
