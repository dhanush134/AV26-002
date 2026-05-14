import csv
import io
import sys
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app
from app.services.samsung_health_import_service import (
    ImportOptions,
    InvalidSamsungZipError,
    SamsungHealthImportService,
    UnsafeSamsungZipPathError,
)
from app.services.samsung_health_parsers.base import parse_samsung_csv


service = SamsungHealthImportService()


def _zip(files: dict[str, str | bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return buffer.getvalue()


def _csv(dataset: str, headers: list[str], rows: list[list[object]]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([dataset, "1153005", "10"])
    writer.writerow(headers)
    writer.writerows(rows)
    return buffer.getvalue()


def _heart_rate_csv(rows: list[list[object]] | None = None) -> str:
    headers = [
        "modify_sh_ver",
        "pkg_name",
        "heart_beat_count",
        "time_offset",
        "binning_data",
        "client_data_ver",
        "heart_rate",
        "comment",
        "max",
        "start_time",
        "deviceuuid",
        "custom",
        "client_data_id",
        "end_time",
        "datauuid",
        "create_time",
        "create_sh_ver",
        "update_time",
        "min",
    ]
    return _csv(
        "com.samsung.health.heart_rate",
        headers,
        rows
        or [
            [
                "1",
                "com.samsung.health",
                "22",
                "19800000",
                "hr-parent.binning_data",
                "1",
                "82",
                "",
                "90",
                "14/05/2026, 6:36:55 PM",
                "device-1",
                "",
                "client-1",
                "14/05/2026, 6:37:55 PM",
                "hr-parent",
                "14/05/2026, 6:38:00 PM",
                "1",
                "14/05/2026, 6:39:00 PM",
                "79",
            ]
        ],
    )


def _step_interval_csv() -> str:
    headers = [
        "speed",
        "pkg_name",
        "count",
        "sample_position_type",
        "time_offset",
        "start_time",
        "calorie",
        "deviceuuid",
        "custom",
        "end_time",
        "datauuid",
        "distance",
        "create_time",
        "update_time",
    ]
    return _csv(
        "com.samsung.health.step_count",
        headers,
        [["1.2", "com.samsung.health", "42", "0", "0", "1778769000000", "2.4", "device-1", "", "1778769060000", "steps-1", "33.5", "", ""]],
    )


def _stress_csv() -> str:
    headers = [
        "score",
        "update_time",
        "modify_sh_ver",
        "pkg_name",
        "time_offset",
        "binning_data",
        "max",
        "start_time",
        "comment",
        "tag_id",
        "deviceuuid",
        "custom",
        "end_time",
        "datauuid",
        "create_time",
        "algorithm",
        "create_sh_ver",
        "min",
    ]
    return _csv(
        "com.samsung.shealth.stress",
        headers,
        [["45", "", "1", "com.samsung.health", "0", "stress-parent.binning_data", "60", "1778769000000", "", "tag", "device-1", "", "1778769060000", "stress-parent", "", "alg", "1", "30"]],
    )


def _basic_zip() -> bytes:
    return _zip(
        {
            "com.samsung.health.heart_rate.2026051422.csv": _heart_rate_csv(),
            "jsons/com.samsung.health.heart_rate/hr-parent.binning_data.json": """
                [
                  {"heart_rate": 82.0, "heart_rate_max": 90.0, "heart_rate_min": 79.0, "start_time": 1778769000000, "end_time": 1778769059000},
                  {"heart_rate": 121.0, "heart_rate_max": 130.0, "heart_rate_min": 110.0, "start_time": 1778769060000, "end_time": 1778769119000}
                ]
            """,
            "com.samsung.health.step_count.2026051422.csv": _step_interval_csv(),
            "jsons/com.samsung.shealth.step_daily_trend/steps-trend.binning_data.json": """
                [
                  {"start_time": 1778769000000, "count": 7, "distance": 5.5, "calorie": 0.4, "speed": 1.1}
                ]
            """,
            "com.samsung.shealth.stress.2026051422.csv": _stress_csv(),
            "jsons/com.samsung.shealth.stress/stress-parent.binning_data.json": """
                [{"score": 43, "score_min": 30, "score_max": 55, "level": 2, "flag": 0, "start_time": 1778769000000, "end_time": 1778769060000}]
            """,
            "com.samsung.shealth.activity.day_summary.2026051422.csv": _csv(
                "com.samsung.shealth.activity.day_summary",
                ["day_time", "step_count", "distance", "calorie", "active_time", "walk_time", "run_time", "exercise_time", "floor_count", "datauuid", "deviceuuid"],
                [["1778716800000", "1000", "800", "40", "1800", "1200", "0", "0", "3", "activity-1", "device-1"]],
            ),
            "com.samsung.health.exercise.2026051422.csv": _csv(
                "com.samsung.health.exercise",
                ["time_offset", "start_time", "end_time", "duration", "exercise_type", "calorie", "distance", "mean_heart_rate", "max_heart_rate", "live_data", "datauuid", "deviceuuid", "pkg_name"],
                [["0", "1778769000000", "1778770800000", "1800", "1001", "120", "1500", "112", "140", "exercise-1.live_data", "exercise-1", "device-1", "com.samsung.health"]],
            ),
        }
    )


def test_valid_samsung_zip_preview_is_accepted() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/health-imports/samsung/preview",
        files={"file": ("DownloadPersonalData_202605142248.zip", _basic_zip(), "application/zip")},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["detected"]["heart_rate"] is True
    assert payload["detected"]["steps"] is True
    assert payload["detected"]["stress"] is True
    assert payload["detected"]["activity"] is True
    assert payload["detected"]["exercise"] is True
    assert payload["detected"]["sleep"] is False
    assert payload["record_counts"]["heart_rate_json"] == 2


def test_invalid_zip_returns_clean_error() -> None:
    with pytest.raises(InvalidSamsungZipError) as exc:
        service.parse(b"not a zip", ImportOptions())
    assert exc.value.message == "Invalid Samsung Health export ZIP"


def test_zip_slip_unsafe_file_path_is_rejected() -> None:
    with pytest.raises(UnsafeSamsungZipPathError):
        service.parse(_zip({"../com.samsung.health.heart_rate.2026051422.csv": _heart_rate_csv()}), ImportOptions())


def test_csv_metadata_first_row_is_skipped_correctly() -> None:
    warnings: list[str] = []
    rows = parse_samsung_csv(_heart_rate_csv().encode(), "heart.csv", warnings)
    assert rows[0]["heart_rate"] == "82"
    assert "com.samsung.health.heart_rate" not in rows[0]
    assert warnings == []


def test_heart_rate_csv_periods_are_parsed() -> None:
    result = service.parse(_zip({"com.samsung.health.heart_rate.2026051422.csv": _heart_rate_csv()}), ImportOptions())
    assert result.heart_rate.summary["period_count"] == 1
    assert result.heart_rate.periods[0].avg_bpm == 82
    assert result.heart_rate.periods[0].binning_data_ref == "hr-parent.binning_data"


def test_heart_rate_json_binning_samples_are_parsed() -> None:
    result = service.parse(_basic_zip(), ImportOptions())
    assert result.heart_rate.summary["sample_count"] == 2
    assert result.heart_rate.samples[0].bpm == 82
    assert result.heart_rate.samples[0].min_bpm == 79
    assert result.heart_rate.samples[0].max_bpm == 90


def test_heart_rate_json_samples_are_linked_to_parent_csv_period() -> None:
    result = service.parse(_basic_zip(), ImportOptions())
    assert result.heart_rate.data_quality["linked_sample_count"] == 2
    assert result.heart_rate.data_quality["unlinked_sample_count"] == 0


def test_missing_heart_rate_json_file_does_not_crash() -> None:
    result = service.parse(_zip({"com.samsung.health.heart_rate.2026051422.csv": _heart_rate_csv()}), ImportOptions())
    assert result.heart_rate.detected is True
    assert result.heart_rate.summary["sample_count"] == 0
    assert result.heart_rate.data_quality["periods_without_json"] == ["hr-parent"]


def test_step_interval_csv_is_parsed() -> None:
    result = service.parse(_zip({"com.samsung.health.step_count.2026051422.csv": _step_interval_csv()}), ImportOptions())
    assert result.steps.intervals[0].steps == 42
    assert result.steps.intervals[0].distance_meters == 33.5


def test_step_trend_json_is_parsed() -> None:
    result = service.parse(
        _zip(
            {
                "jsons/com.samsung.shealth.step_daily_trend/steps-trend.binning_data.json": """
                    [{"start_time": 1778769000000, "count": 7, "distance": 5.5, "calorie": 0.4, "speed": 1.1}]
                """
            }
        ),
        ImportOptions(),
    )
    assert result.steps.trend_samples[0].parent_datauuid == "steps-trend"
    assert result.steps.trend_samples[0].steps == 7


def test_stress_csv_and_stress_json_are_parsed() -> None:
    result = service.parse(
        _zip(
            {
                "com.samsung.shealth.stress.2026051422.csv": _stress_csv(),
                "jsons/com.samsung.shealth.stress/stress-parent.binning_data.json": """
                    [{"score": 43, "score_min": 30, "score_max": 55, "level": 2, "flag": 0, "start_time": 1778769000000, "end_time": 1778769060000}]
                """,
            }
        ),
        ImportOptions(),
    )
    assert result.stress.periods[0].score == 45
    assert result.stress.samples[0].score == 43


def test_missing_sleep_files_return_detected_false_not_error() -> None:
    result = service.parse(_basic_zip(), ImportOptions())
    assert result.sleep.detected is False
    assert result.sleep.summary["session_count"] == 0
    assert "No sleep files found" in result.sleep.message


def test_include_samples_false_excludes_detailed_sample_arrays_but_keeps_aggregates() -> None:
    result = service.parse(_basic_zip(), ImportOptions(include_samples=False))
    assert result.heart_rate.samples == []
    assert result.stress.samples == []
    assert result.heart_rate.hourly_aggregates
    assert result.stress.daily_aggregates


def test_sample_limit_truncates_samples_and_sets_flag() -> None:
    result = service.parse(_basic_zip(), ImportOptions(sample_limit=1))
    assert len(result.heart_rate.samples) == 1
    assert result.heart_rate.data_quality["samples_truncated"] is True


def test_malformed_row_creates_warning_not_full_failure() -> None:
    malformed = _heart_rate_csv(rows=[["1", "com.samsung.health", "22"]])
    result = service.parse(_zip({"com.samsung.health.heart_rate.2026051422.csv": malformed}), ImportOptions())
    assert result.heart_rate.detected is True
    assert any("Malformed row" in warning for warning in result.files.warnings)
