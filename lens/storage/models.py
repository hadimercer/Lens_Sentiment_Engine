"""Storage models for historical analysis views."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

from lens.pipeline.anomaly import run_anomaly_detection
from lens.pipeline.models import AnalysisResult, AnomalyFlag, ContextProfile, PriorCycleContext, RecordResult, ThemeResult


@dataclass
class HistoryFilters:
    series_name: Optional[str] = None
    domain_tag: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None


@dataclass
class HistoryListItem:
    analysis_id: str
    batch_label: str
    series_name: Optional[str]
    run_sequence: Optional[int]
    domain_tag: Optional[str]
    created_at: datetime
    record_count: int
    anomaly_count: int

    @property
    def label(self) -> str:
        series_part = f"{self.series_name} / run {self.run_sequence}" if self.series_name and self.run_sequence else "Standalone"
        return f"{self.batch_label} - {series_part} - {self.created_at:%Y-%m-%d %H:%M}"


@dataclass
class StoredRecord:
    record_id: str
    sequence_number: int
    text_body: str
    sentiment_label: str
    confidence_score: float
    reasoning: Optional[str]
    deviation_from_mean: Optional[float]
    is_anomaly: bool
    theme_assignments: list[str] = field(default_factory=list)
    record_timestamp: Optional[str] = None
    scored: bool = True


@dataclass
class StoredAnalysis:
    analysis_id: str
    batch_label: str
    domain_tag: Optional[str]
    series_name: Optional[str]
    run_sequence: Optional[int]
    created_at: Optional[datetime]
    record_count: int
    sentiment_split: dict
    themes: list[ThemeResult]
    executive_summary: str
    anomaly_flags: list[AnomalyFlag]
    anomaly_count: int
    context_profile: Optional[ContextProfile]
    records: list[StoredRecord]
    prior_cycle_context: Optional[PriorCycleContext] = None

    @classmethod
    def from_analysis_result(cls, result: AnalysisResult, created_at: Optional[datetime] = None) -> "StoredAnalysis":
        records = [
            StoredRecord(
                record_id=record.record_id,
                sequence_number=record.sequence_number,
                text_body=record.text_body,
                sentiment_label=record.sentiment_label,
                confidence_score=record.confidence_score,
                reasoning=record.reasoning,
                deviation_from_mean=record.deviation_from_mean,
                is_anomaly=record.is_anomaly,
                theme_assignments=record.theme_assignments or [],
                record_timestamp=record.record_timestamp,
                scored=record.scored,
            )
            for record in result.records
        ]
        return cls(
            analysis_id=result.analysis_id,
            batch_label=result.batch_label,
            domain_tag=result.domain_tag,
            series_name=result.series_name,
            run_sequence=result.run_sequence,
            created_at=created_at,
            record_count=result.record_count,
            sentiment_split=result.sentiment_split,
            themes=result.themes,
            executive_summary=result.executive_summary,
            anomaly_flags=result.anomaly_flags,
            anomaly_count=result.anomaly_count,
            context_profile=result.context_profile,
            records=records,
            prior_cycle_context=result.prior_cycle_context,
        )

    def to_record_results(self) -> list[RecordResult]:
        return [
            RecordResult(
                record_id=record.record_id,
                sequence_number=record.sequence_number,
                text_body=record.text_body,
                sentiment_label=record.sentiment_label,
                confidence_score=record.confidence_score,
                reasoning=record.reasoning,
                deviation_from_mean=record.deviation_from_mean,
                is_anomaly=record.is_anomaly,
                theme_assignments=record.theme_assignments,
                record_timestamp=record.record_timestamp,
                scored=record.scored,
            )
            for record in self.records
        ]

    def rebuild_anomaly_flags(self) -> list[AnomalyFlag]:
        return run_anomaly_detection(self.to_record_results(), timestamps=[record.record_timestamp for record in self.records])
