"""Validation and parsing for uploaded and pasted batches."""

from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import Optional

from lens.config import get_settings

from .models import ValidatedBatch

TEXT_COLUMN_HINTS = [
    "text",
    "comment",
    "comments",
    "response",
    "responses",
    "body",
    "message",
    "feedback",
    "note",
    "notes",
    "content",
]
TIMESTAMP_COLUMN_HINTS = ["date", "timestamp", "created", "created_at", "time"]


class ValidationError(ValueError):
    pass


def validate_batch(*, csv_bytes: bytes | None = None, raw_text: str | None = None) -> ValidatedBatch:
    if csv_bytes is not None:
        return _validate_csv(csv_bytes)
    if raw_text is not None:
        return _validate_text(raw_text)
    raise ValidationError("Provide either csv_bytes or raw_text.")


def _validate_csv(csv_bytes: bytes) -> ValidatedBatch:
    settings = get_settings()
    try:
        decoded = csv_bytes.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValidationError("CSV files must be UTF-8 encoded.") from error

    reader = csv.DictReader(io.StringIO(decoded))
    if not reader.fieldnames:
        raise ValidationError("CSV must include a header row.")

    detected_columns = [column.strip() for column in reader.fieldnames if column]
    text_column = _detect_column(detected_columns, TEXT_COLUMN_HINTS)
    if not text_column:
        raise ValidationError("CSV must include a text column such as text, comment, response, or feedback.")

    timestamp_column = _detect_column(detected_columns, TIMESTAMP_COLUMN_HINTS)

    records: list[str] = []
    timestamps: list[Optional[str]] = []
    rejected_row_count = 0
    preview_rows: list[dict[str, Optional[str]]] = []

    for row in reader:
        text_value = _clean_text(row.get(text_column))
        timestamp_value = _parse_timestamp(row.get(timestamp_column)) if timestamp_column else None

        if not text_value:
            rejected_row_count += 1
            continue

        records.append(text_value)
        timestamps.append(timestamp_value)
        if len(preview_rows) < 5:
            preview_rows.append(
                {
                    "text": text_value,
                    "timestamp": timestamp_value,
                }
            )

    _validate_record_count(len(records), settings.max_batch_size)

    return ValidatedBatch(
        source_type="csv",
        records=records,
        timestamps=timestamps if timestamp_column else None,
        rejected_row_count=rejected_row_count,
        detected_columns=detected_columns,
        text_column=text_column,
        timestamp_column=timestamp_column,
        preview_rows=preview_rows,
    )


def _validate_text(raw_text: str) -> ValidatedBatch:
    settings = get_settings()
    records = [_clean_text(line) for line in raw_text.splitlines()]
    records = [record for record in records if record]
    _validate_record_count(len(records), settings.max_batch_size)

    if not records:
        raise ValidationError("Paste at least one non-empty line of text.")

    preview_rows = [{"text": record, "timestamp": None} for record in records[:5]]
    return ValidatedBatch(
        source_type="text",
        records=records,
        timestamps=None,
        rejected_row_count=0,
        detected_columns=["text"],
        text_column="text",
        timestamp_column=None,
        preview_rows=preview_rows,
    )


def _validate_record_count(record_count: int, max_batch_size: int) -> None:
    if record_count == 0:
        raise ValidationError("No valid text records were found in the batch.")
    if record_count > max_batch_size:
        raise ValidationError(f"Batch exceeds the {max_batch_size:,} record limit.")


def _detect_column(columns: list[str], hints: list[str]) -> str | None:
    lowered = {column.lower(): column for column in columns}
    for hint in hints:
        if hint in lowered:
            return lowered[hint]
    for column in columns:
        if any(hint in column.lower() for hint in hints):
            return column
    return None


def _clean_text(value: Optional[str]) -> str:
    if value is None:
        return ""
    return " ".join(str(value).strip().split())


def _parse_timestamp(value: Optional[str]) -> Optional[str]:
    if not value or not str(value).strip():
        return None
    candidate = str(value).strip()
    for parser in (datetime.fromisoformat, _parse_date_only):
        try:
            parsed = parser(candidate)
            return parsed.date().isoformat() if isinstance(parsed, datetime) else parsed
        except ValueError:
            continue
    return candidate


def _parse_date_only(value: str) -> str:
    return datetime.strptime(value, "%Y-%m-%d").date().isoformat()
