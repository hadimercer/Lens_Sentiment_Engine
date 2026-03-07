"""Typed data structures used throughout the Lens pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
import uuid


@dataclass
class ContextProfile:
    org_name: Optional[str] = None
    industry: Optional[str] = None
    department: Optional[str] = None
    reporting_period: Optional[str] = None
    situational_notes: Optional[str] = None

    def is_empty(self) -> bool:
        return not any(
            [
                self.org_name,
                self.industry,
                self.department,
                self.reporting_period,
                self.situational_notes,
            ]
        )

    def to_prompt_block(self) -> str:
        if self.is_empty():
            return "No organisational context supplied. Use domain-agnostic framing."

        parts: list[str] = []
        if self.org_name:
            parts.append(f"Organisation: {self.org_name}.")
        if self.industry:
            parts.append(f"Industry: {self.industry}.")
        if self.department:
            parts.append(f"Department: {self.department}.")
        if self.reporting_period:
            parts.append(f"Period: {self.reporting_period}.")
        if self.situational_notes:
            parts.append(f"Context: {self.situational_notes}")
        return " ".join(parts)


@dataclass
class PriorCycleContext:
    batch_label: str
    run_sequence: int
    sentiment_split: dict
    top_themes: list[str]
    executive_summary: str
    analysis_id: Optional[str] = None

    def to_prompt_block(self) -> str:
        themes_str = ", ".join(self.top_themes[:5])
        pos = self.sentiment_split.get("positive", 0)
        neu = self.sentiment_split.get("neutral", 0)
        neg = self.sentiment_split.get("negative", 0)
        return (
            f"Previous cycle ({self.batch_label}, run {self.run_sequence}): "
            f"Sentiment split: {pos:.0f}% positive, {neu:.0f}% neutral, {neg:.0f}% negative. "
            f"Top themes: {themes_str}. "
            f"Summary: {self.executive_summary}"
        )


@dataclass
class BatchInput:
    batch_label: str
    domain_tag: Optional[str]
    records: list[str]
    timestamps: Optional[list[str]]
    context: ContextProfile = field(default_factory=ContextProfile)
    series_name: Optional[str] = None
    prior_cycle: Optional[PriorCycleContext] = None
    analysis_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class RecordResult:
    record_id: str
    sequence_number: int
    text_body: str
    sentiment_label: str
    confidence_score: float
    reasoning: Optional[str]
    deviation_from_mean: Optional[float] = None
    is_anomaly: bool = False
    theme_assignments: Optional[list[str]] = None
    record_timestamp: Optional[str] = None
    scored: bool = True


@dataclass
class ThemeResult:
    label: str
    frequency: int
    dominant_sentiment: str
    representative_quotes: list[str]


@dataclass
class AnomalyFlag:
    anomaly_type: str
    record_id: Optional[str]
    time_period: Optional[str]
    deviation_value: float
    description: str


@dataclass
class AnalysisResult:
    analysis_id: str
    batch_label: str
    domain_tag: Optional[str]
    series_name: Optional[str]
    run_sequence: Optional[int]
    records: list[RecordResult]
    themes: list[ThemeResult]
    executive_summary: str
    anomaly_flags: list[AnomalyFlag]
    sentiment_split: dict
    anomaly_count: int
    context_profile: Optional[ContextProfile]
    prior_cycle_ref: Optional[str]
    prior_cycle_context: Optional[PriorCycleContext]
    record_count: int
    records_scored: int
    records_failed: int
    api_call_count: int
    duration_seconds: Optional[float]

    def to_db_dict(self) -> dict:
        return {
            "analysis_id": self.analysis_id,
            "series_name": self.series_name,
            "run_sequence": self.run_sequence,
            "batch_label": self.batch_label,
            "domain_tag": self.domain_tag,
            "record_count": self.record_count,
            "sentiment_split": self.sentiment_split,
            "top_themes": [
                {
                    "label": theme.label,
                    "frequency": theme.frequency,
                    "dominant_sentiment": theme.dominant_sentiment,
                    "representative_quotes": theme.representative_quotes,
                }
                for theme in self.themes
            ],
            "executive_summary": self.executive_summary,
            "anomaly_count": self.anomaly_count,
            "context_profile": {
                "org_name": self.context_profile.org_name,
                "industry": self.context_profile.industry,
                "department": self.context_profile.department,
                "reporting_period": self.context_profile.reporting_period,
                "situational_notes": self.context_profile.situational_notes,
            }
            if self.context_profile and not self.context_profile.is_empty()
            else None,
            "prior_cycle_ref": self.prior_cycle_ref,
            "per_record_results": [
                {
                    "record_id": record.record_id,
                    "sequence_number": record.sequence_number,
                    "sentiment_label": record.sentiment_label,
                    "confidence_score": record.confidence_score,
                    "reasoning": record.reasoning,
                    "is_anomaly": record.is_anomaly,
                    "theme_assignments": record.theme_assignments,
                    "record_timestamp": record.record_timestamp,
                    "deviation_from_mean": record.deviation_from_mean,
                    "scored": record.scored,
                }
                for record in self.records
            ],
        }
