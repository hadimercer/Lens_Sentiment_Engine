"""Pipeline orchestration."""

from __future__ import annotations

import logging
import time
import uuid
from collections import Counter
from typing import Callable, Optional

from lens.config import get_settings

from .anomaly import run_anomaly_detection
from .api_client import APIClient, LLMProvider
from .models import (
    AnalysisResult,
    AnomalyFlag,
    BatchInput,
    IssueCluster,
    PositiveSignal,
    RecordResult,
    ThemeResult,
)
from .prompts import (
    build_sentiment_prompt,
    build_summary_prompt,
    build_system_prompt,
    build_theme_prompt,
)

logger = logging.getLogger(__name__)



def run_pipeline(
    batch: BatchInput,
    api_key: str,
    progress_callback: Optional[Callable[[str, int, int], None]] = None,
    provider: Optional[LLMProvider] = None,
    model: str | None = None,
) -> AnalysisResult:
    start_time = time.time()

    def progress(stage: str, processed: int, total: int) -> None:
        if progress_callback:
            progress_callback(stage, processed, total)

    progress("Building prompts", 0, len(batch.records))
    settings = get_settings()
    active_model = model or settings.openai_model
    system_prompt = build_system_prompt(
        context=batch.context,
        prior_cycle=batch.prior_cycle,
        has_timestamps=batch.timestamps is not None,
    )
    client = APIClient(
        api_key=api_key,
        system_prompt=system_prompt,
        retry_count=settings.retry_count,
        provider=provider,
        model=active_model,
    )

    progress("Running sentiment analysis", 0, len(batch.records))
    record_results: list[RecordResult] = []
    records_failed = 0

    for index, text in enumerate(batch.records):
        prompt = build_sentiment_prompt(text)
        api_result = client.score_record(prompt, record_index=index)
        timestamp = batch.timestamps[index] if batch.timestamps and index < len(batch.timestamps) else None
        record_id = str(uuid.uuid4())

        if api_result is None:
            records_failed += 1
            record_results.append(
                RecordResult(
                    record_id=record_id,
                    sequence_number=index + 1,
                    text_body=text,
                    sentiment_label="neutral",
                    confidence_score=0.0,
                    reasoning=None,
                    record_timestamp=timestamp,
                    scored=False,
                )
            )
        else:
            record_results.append(
                RecordResult(
                    record_id=record_id,
                    sequence_number=index + 1,
                    text_body=text,
                    sentiment_label=api_result["sentiment_label"],
                    confidence_score=api_result["confidence_score"],
                    reasoning=api_result.get("reasoning"),
                    record_timestamp=timestamp,
                    scored=True,
                )
            )

        if (index + 1) % 10 == 0 or (index + 1) == len(batch.records):
            progress("Running sentiment analysis", index + 1, len(batch.records))

    scored_only = [record for record in record_results if record.scored]
    sentiment_split = _compute_sentiment_split(scored_only)

    progress("Extracting themes", 0, 1)
    raw_themes = client.extract_themes(
        build_theme_prompt([record.text_body for record in scored_only], context=batch.context)
    )
    themes = [
        ThemeResult(
            label=theme["label"],
            frequency=theme["frequency"],
            dominant_sentiment=theme["dominant_sentiment"],
            representative_quotes=theme["representative_quotes"],
        )
        for theme in raw_themes
    ]
    progress("Extracting themes", 1, 1)

    _assign_themes_to_records(record_results, themes)

    progress("Running anomaly detection", 0, 1)
    anomaly_flags: list[AnomalyFlag] = run_anomaly_detection(record_results, timestamps=batch.timestamps)
    progress("Running anomaly detection", 1, 1)

    progress("Generating summary", 0, 1)
    summary_payload = client.generate_summary(
        build_summary_prompt(
            summary_evidence=_build_summary_evidence(
                batch=batch,
                sentiment_split=sentiment_split,
                records=record_results,
                themes=themes,
                anomaly_flags=anomaly_flags,
            ),
            context=batch.context,
            prior_cycle=batch.prior_cycle,
            batch_label=batch.batch_label,
        )
    )
    executive_summary = summary_payload["executive_summary"]
    key_takeaways = summary_payload["key_takeaways"]
    priority_actions = summary_payload["priority_actions"]
    issue_clusters = [IssueCluster(**cluster) for cluster in summary_payload["issue_clusters"]]
    positive_signals = [PositiveSignal(**signal) for signal in summary_payload["positive_signals"]]
    progress("Generating summary", 1, 1)

    duration = round(time.time() - start_time, 2)
    records_scored = len(batch.records) - records_failed

    result = AnalysisResult(
        analysis_id=batch.analysis_id,
        batch_label=batch.batch_label,
        domain_tag=batch.domain_tag,
        series_name=batch.series_name,
        run_sequence=None,
        records=record_results,
        themes=themes,
        executive_summary=executive_summary,
        key_takeaways=key_takeaways,
        priority_actions=priority_actions,
        issue_clusters=issue_clusters,
        positive_signals=positive_signals,
        anomaly_flags=anomaly_flags,
        sentiment_split=sentiment_split,
        anomaly_count=len(anomaly_flags),
        context_profile=batch.context,
        prior_cycle_ref=batch.prior_cycle.analysis_id if batch.prior_cycle else None,
        prior_cycle_context=batch.prior_cycle,
        record_count=len(batch.records),
        records_scored=records_scored,
        records_failed=records_failed,
        api_call_count=client.call_count,
        duration_seconds=duration,
    )

    progress("Complete", len(batch.records), len(batch.records))
    return result



def _compute_sentiment_split(scored_records: list[RecordResult]) -> dict:
    if not scored_records:
        return {"positive": 0.0, "neutral": 0.0, "negative": 0.0}

    counts = {"positive": 0, "neutral": 0, "negative": 0}
    for record in scored_records:
        counts[record.sentiment_label if record.sentiment_label in counts else "neutral"] += 1

    total = len(scored_records)
    return {
        "positive": round(counts["positive"] / total * 100, 1),
        "neutral": round(counts["neutral"] / total * 100, 1),
        "negative": round(counts["negative"] / total * 100, 1),
    }



def _assign_themes_to_records(records: list[RecordResult], themes: list[ThemeResult]) -> None:
    for record in records:
        assigned: list[str] = []
        lower_text = record.text_body.lower()
        for theme in themes:
            label_tokens = [token for token in theme.label.lower().split() if len(token) > 3]
            quote_match = any(quote and quote[:40].lower() in lower_text for quote in theme.representative_quotes)
            label_match = any(token in lower_text for token in label_tokens)
            if quote_match or label_match:
                assigned.append(theme.label)
        record.theme_assignments = assigned or None



def _build_summary_evidence(
    *,
    batch: BatchInput,
    sentiment_split: dict,
    records: list[RecordResult],
    themes: list[ThemeResult],
    anomaly_flags: list[AnomalyFlag],
) -> dict:
    theme_sections = []
    for theme in themes:
        related_records = [record for record in records if record.theme_assignments and theme.label in record.theme_assignments]
        negative_records = [record for record in related_records if record.sentiment_label == "negative"]
        positive_records = [record for record in related_records if record.sentiment_label == "positive"]
        neutral_records = [record for record in related_records if record.sentiment_label == "neutral"]

        theme_sections.append(
            {
                "label": theme.label,
                "frequency": theme.frequency,
                "dominant_sentiment": theme.dominant_sentiment,
                "representative_quotes": theme.representative_quotes,
                "negative_issue_patterns": _top_reasoning_patterns(negative_records),
                "positive_win_patterns": _top_reasoning_patterns(positive_records),
                "neutral_notes": _top_reasoning_patterns(neutral_records),
                "sample_negative_text": [record.text_body[:220] for record in negative_records[:3]],
                "sample_positive_text": [record.text_body[:220] for record in positive_records[:3]],
            }
        )

    anomaly_sections = [
        {
            "type": flag.anomaly_type,
            "description": flag.description,
            "record_id": flag.record_id,
            "time_period": flag.time_period,
            "deviation_value": flag.deviation_value,
        }
        for flag in anomaly_flags[:6]
    ]

    overall_patterns = {
        "negative": _top_reasoning_patterns([record for record in records if record.sentiment_label == "negative"]),
        "positive": _top_reasoning_patterns([record for record in records if record.sentiment_label == "positive"]),
        "neutral": _top_reasoning_patterns([record for record in records if record.sentiment_label == "neutral"]),
    }

    return {
        "record_count": len(batch.records),
        "records_scored": len([record for record in records if record.scored]),
        "records_failed": len([record for record in records if not record.scored]),
        "sentiment_split": sentiment_split,
        "top_level_patterns": overall_patterns,
        "themes": theme_sections,
        "anomalies": anomaly_sections,
        "series_name": batch.series_name,
        "has_timestamps": batch.timestamps is not None,
    }



def _top_reasoning_patterns(records: list[RecordResult], limit: int = 5) -> list[str]:
    reasoning_counter: Counter[str] = Counter()
    text_counter: Counter[str] = Counter()
    for record in records:
        if record.reasoning:
            reasoning_counter[record.reasoning.strip()] += 1
        else:
            text_counter[_compact_text(record.text_body)] += 1

    ranked = [text for text, _count in reasoning_counter.most_common(limit)]
    if len(ranked) < limit:
        ranked.extend([text for text, _count in text_counter.most_common(limit - len(ranked))])
    return ranked[:limit]



def _compact_text(text: str, limit: int = 140) -> str:
    clean = " ".join(text.split())
    return clean[:limit] + ("..." if len(clean) > limit else "")
