from __future__ import annotations

import csv
import io
import json
import re
import unicodedata
from collections.abc import Iterable
from datetime import UTC, datetime, timedelta, timezone
from pathlib import PurePosixPath
from typing import Any, TypeVar


SAMSUNG_DATETIME_FORMATS = (
    "%d/%m/%Y, %I:%M:%S %p",
    "%d/%m/%Y, %I:%M %p",
    "%d/%m/%Y %I:%M:%S %p",
    "%Y-%m-%dT%H:%M:%S.%f%z",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%d %H:%M:%S",
)


def normalize_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return unicodedata.normalize("NFKC", text).replace("\u202f", " ").replace("\xa0", " ").strip()


def parse_samsung_datetime(value: Any, time_offset_ms: int | float | str | None = None) -> str | None:
    text = normalize_text(value)
    if text is None:
        return None
    dt: datetime | None = None
    if re.fullmatch(r"-?\d+(\.0+)?", text):
        numeric_value = int(float(text))
        if abs(numeric_value) > 10_000_000_000:
            dt = datetime.fromtimestamp(numeric_value / 1000, UTC)
        else:
            dt = datetime.fromtimestamp(numeric_value, UTC)
    else:
        for fmt in SAMSUNG_DATETIME_FORMATS:
            try:
                dt = datetime.strptime(text, fmt)
                break
            except ValueError:
                continue
    if dt is None:
        return None
    if dt.tzinfo is None:
        offset = to_int(time_offset_ms)
        if offset is not None:
            dt = dt.replace(tzinfo=timezone(timedelta(milliseconds=offset)))
        else:
            dt = dt.replace(tzinfo=UTC)
    return dt.isoformat()


def parse_samsung_date(value: Any, time_offset_ms: int | float | str | None = None) -> str | None:
    parsed = parse_samsung_datetime(value, time_offset_ms)
    if parsed:
        return parsed[:10]
    text = normalize_text(value)
    if text is None:
        return None
    if re.fullmatch(r"\d{8}", text):
        return f"{text[:4]}-{text[4:6]}-{text[6:]}"
    return text[:10] if len(text) >= 10 else text


def decode_text(data: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp949", "cp1252"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def parse_samsung_csv(data: bytes, source_file: str, warnings: list[str]) -> list[dict[str, str]]:
    text = decode_text(data)
    rows = list(csv.reader(io.StringIO(text)))
    if len(rows) < 2:
        warnings.append(f"Samsung Health CSV format not recognized: {source_file}")
        return []
    headers = [normalize_text(header) or "" for header in rows[1]]
    if not any(headers):
        warnings.append(f"Samsung Health CSV format not recognized: {source_file}")
        return []
    records: list[dict[str, str]] = []
    for index, row in enumerate(rows[2:], start=3):
        if not row or not any((cell or "").strip() for cell in row):
            continue
        if len(row) > len(headers) and not any((cell or "").strip() for cell in row[len(headers) :]):
            row = row[: len(headers)]
        if len(row) != len(headers):
            warnings.append(
                f"Malformed row in {source_file} at CSV row {index}: expected {len(headers)} columns, got {len(row)}"
            )
        normalized_row = list(row[: len(headers)])
        if len(normalized_row) < len(headers):
            normalized_row.extend([""] * (len(headers) - len(normalized_row)))
        records.append(dict(zip(headers, normalized_row, strict=False)))
    return records


def parse_json_bytes(data: bytes) -> Any:
    return json.loads(decode_text(data))


def flatten_json_items(payload: Any) -> list[dict[str, Any]]:
    if payload is None:
        return []
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("items", "data", "records", "samples"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        return [payload]
    return []


def parent_id_from_json_file(filename: str, suffix: str) -> str | None:
    stem = PurePosixPath(filename).name
    if stem.endswith(suffix):
        return stem[: -len(suffix)]
    parts = stem.split(".")
    return parts[0] if parts else None


def to_float(value: Any) -> float | None:
    text = normalize_text(value)
    if text is None:
        return None
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def to_int(value: Any) -> int | None:
    number = to_float(value)
    if number is None:
        return None
    return int(number)


def duration_seconds(start_time: str | None, end_time: str | None) -> float | None:
    if not start_time or not end_time:
        return None
    try:
        start = datetime.fromisoformat(start_time)
        end = datetime.fromisoformat(end_time)
    except ValueError:
        return None
    return max((end - start).total_seconds(), 0)


def non_empty_raw(row: dict[str, Any], exclude: Iterable[str] = ()) -> dict[str, Any]:
    excluded = set(exclude)
    return {
        key: value
        for key, value in row.items()
        if key not in excluded and value is not None and normalize_text(value) is not None
    }


T = TypeVar("T")


def limit_records(records: list[T], include: bool, limit: int) -> tuple[list[T], bool]:
    if not include:
        return [], bool(records)
    safe_limit = max(limit, 0)
    return records[:safe_limit], len(records) > safe_limit


def average(values: Iterable[float | int | None]) -> float | None:
    clean = [float(value) for value in values if value is not None]
    if not clean:
        return None
    return round(sum(clean) / len(clean), 2)


def min_value(values: Iterable[float | int | None]) -> float | None:
    clean = [float(value) for value in values if value is not None]
    return min(clean) if clean else None


def max_value(values: Iterable[float | int | None]) -> float | None:
    clean = [float(value) for value in values if value is not None]
    return max(clean) if clean else None


def hour_bucket(iso_value: str | None) -> str | None:
    if not iso_value:
        return None
    try:
        dt = datetime.fromisoformat(iso_value)
    except ValueError:
        return None
    return dt.replace(minute=0, second=0, microsecond=0).isoformat()


def date_bucket(iso_value: str | None) -> str | None:
    if not iso_value:
        return None
    return iso_value[:10]


def group_by(records: Iterable[T], key_fn: Any) -> dict[str, list[T]]:
    grouped: dict[str, list[T]] = {}
    for record in records:
        key = key_fn(record)
        if key:
            grouped.setdefault(key, []).append(record)
    return grouped
