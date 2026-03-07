"""Ingestion models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from lens.pipeline.models import BatchInput, ContextProfile, PriorCycleContext


@dataclass
class BatchPreview:
    sample_records: list[dict[str, Optional[str]]]
    valid_record_count: int
    rejected_row_count: int
    detected_columns: list[str]
    text_column: Optional[str]
    timestamp_column: Optional[str]


@dataclass
class ValidatedBatch:
    source_type: str
    records: list[str]
    timestamps: Optional[list[Optional[str]]]
    rejected_row_count: int
    detected_columns: list[str]
    text_column: Optional[str]
    timestamp_column: Optional[str]
    preview_rows: list[dict[str, Optional[str]]]

    @property
    def valid_record_count(self) -> int:
        return len(self.records)

    def to_preview(self) -> BatchPreview:
        return BatchPreview(
            sample_records=self.preview_rows,
            valid_record_count=self.valid_record_count,
            rejected_row_count=self.rejected_row_count,
            detected_columns=self.detected_columns,
            text_column=self.text_column,
            timestamp_column=self.timestamp_column,
        )


def build_batch_input(
    validated_batch: ValidatedBatch,
    *,
    batch_label: str,
    domain_tag: str | None,
    context: ContextProfile,
    series_name: str | None,
    prior_cycle: PriorCycleContext | None,
) -> BatchInput:
    timestamps = None
    if validated_batch.timestamps and any(value is not None for value in validated_batch.timestamps):
        timestamps = [value.isoformat() if hasattr(value, "isoformat") else value for value in validated_batch.timestamps]
    return BatchInput(
        batch_label=batch_label,
        domain_tag=domain_tag or None,
        records=validated_batch.records,
        timestamps=timestamps,
        context=context,
        series_name=series_name or None,
        prior_cycle=prior_cycle,
    )
