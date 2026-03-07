"""Anomaly detection helpers."""

from __future__ import annotations

import logging
import statistics
from collections import defaultdict
from typing import Optional

from .models import AnomalyFlag, RecordResult

logger = logging.getLogger(__name__)

RECORD_OUTLIER_SIGMA = 2.0
TIME_SPIKE_THRESHOLD_PP = 15.0
TIME_SPIKE_MIN_RECORDS = 14
TIME_SPIKE_MIN_PERIODS = 2


def _score_to_numeric(record: RecordResult) -> float:
    if record.sentiment_label == "positive":
        return record.confidence_score
    if record.sentiment_label == "negative":
        return -record.confidence_score
    return 0.0


def detect_record_outliers(records: list[RecordResult]) -> list[AnomalyFlag]:
    scored_records = [record for record in records if record.scored]
    if len(scored_records) < 3:
        return []

    scores = [_score_to_numeric(record) for record in scored_records]
    mean = statistics.mean(scores)
    try:
        stdev = statistics.stdev(scores)
    except statistics.StatisticsError:
        return []

    if stdev == 0:
        return []

    flags: list[AnomalyFlag] = []
    for record, score in zip(scored_records, scores):
        deviation = (score - mean) / stdev
        record.deviation_from_mean = round(deviation, 3)
        if abs(deviation) >= RECORD_OUTLIER_SIGMA:
            record.is_anomaly = True
            direction = "above" if deviation > 0 else "below"
            flags.append(
                AnomalyFlag(
                    anomaly_type="record_outlier",
                    record_id=record.record_id,
                    time_period=None,
                    deviation_value=round(abs(deviation), 3),
                    description=(
                        f"Record sentiment score is {abs(deviation):.1f} standard deviations {direction} "
                        f"the batch mean ({record.sentiment_label}, confidence {record.confidence_score:.2f})."
                    ),
                )
            )

    logger.info("Record outlier detection: %s flags from %s records", len(flags), len(scored_records))
    return flags


def detect_time_spikes(records: list[RecordResult], timestamps: Optional[list[str]]) -> list[AnomalyFlag]:
    if not timestamps:
        return []

    scored_records = [record for record in records if record.scored and record.record_timestamp]
    if len(scored_records) < TIME_SPIKE_MIN_RECORDS:
        return []

    daily_scores: dict[str, list[float]] = defaultdict(list)
    for record in scored_records:
        day = str(record.record_timestamp)[:10]
        if day:
            daily_scores[day].append(_score_to_numeric(record))

    if len(daily_scores) < TIME_SPIKE_MIN_PERIODS:
        return []

    sorted_days = sorted(daily_scores.keys())
    daily_avg = {day: statistics.mean(values) for day, values in daily_scores.items()}

    def to_pct(signed_score: float) -> float:
        return (signed_score + 1) / 2 * 100

    rolling_avgs: list[tuple[str, float]] = []
    for index, day in enumerate(sorted_days):
        window_start = max(0, index - 6)
        window_days = sorted_days[window_start : index + 1]
        window_scores = [daily_avg[current_day] for current_day in window_days]
        rolling_avgs.append((day, to_pct(statistics.mean(window_scores))))

    flags: list[AnomalyFlag] = []
    for index in range(1, len(rolling_avgs)):
        prev_day, prev_avg = rolling_avgs[index - 1]
        curr_day, curr_avg = rolling_avgs[index]
        shift = curr_avg - prev_avg
        if abs(shift) >= TIME_SPIKE_THRESHOLD_PP:
            direction = "increase" if shift > 0 else "decline"
            flags.append(
                AnomalyFlag(
                    anomaly_type="time_spike",
                    record_id=None,
                    time_period=curr_day,
                    deviation_value=round(abs(shift), 1),
                    description=(
                        f"7-day rolling sentiment average shifted {abs(shift):.1f}pp "
                        f"({direction}) between {prev_day} and {curr_day}."
                    ),
                )
            )

    logger.info("Time spike detection: %s flags across %s days", len(flags), len(sorted_days))
    return flags


def run_anomaly_detection(records: list[RecordResult], timestamps: Optional[list[str]] = None) -> list[AnomalyFlag]:
    return detect_record_outliers(records) + detect_time_spikes(records, timestamps)
