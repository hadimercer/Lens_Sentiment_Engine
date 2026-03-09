"""Persistence and history queries for Lens."""

from __future__ import annotations

import csv
import io
import re
from datetime import datetime, time
from pathlib import Path
from typing import Optional

from psycopg2 import sql
from psycopg2.extras import Json, execute_values

from lens.config import get_settings
from lens.db import get_connection
from lens.pipeline.anomaly import run_anomaly_detection
from lens.pipeline.models import (
    AnalysisResult,
    ContextProfile,
    IssueCluster,
    PositiveSignal,
    PriorCycleContext,
    ThemeResult,
)

from .models import HistoryFilters, HistoryListItem, StoredAnalysis, StoredRecord


SUMMARY_DETAILS_MIGRATION = """
ALTER TABLE analysis_results
ADD COLUMN IF NOT EXISTS summary_details JSONB NOT NULL DEFAULT '{}'::JSONB;
"""



def _apply_runtime_migrations(cursor) -> None:
    cursor.execute(SUMMARY_DETAILS_MIGRATION)



def _read_sql_file(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8-sig")



def bootstrap_database() -> tuple[bool, str]:
    settings = get_settings()
    if not settings.database_url:
        return False, "DATABASE_URL is not configured. Demo history is unavailable until the database is configured."

    schema_sql = _read_sql_file(settings.schema_path)
    seed_sql = _read_sql_file(settings.seed_path)

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(schema_sql)
            _apply_runtime_migrations(cursor)
            connection.commit()

            cursor.execute("SELECT COUNT(*) AS total FROM series_index")
            total = int(cursor.fetchone()["total"])
            if total == 0:
                cursor.execute(seed_sql)
                connection.commit()
                return True, "Database bootstrapped and demo seed data loaded."

    return True, "Database already initialized."



def get_series_names() -> list[str]:
    if not _database_ready():
        return []
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT series_name FROM series_index ORDER BY series_name ASC")
            return [row["series_name"] for row in cursor.fetchall()]



def get_prior_cycle(series_name: str | None) -> Optional[PriorCycleContext]:
    if not series_name or not _database_ready():
        return None

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT analysis_id, batch_label, run_sequence, sentiment_split, top_themes, executive_summary FROM get_prior_cycle(%s)",
                (series_name,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            top_themes = [theme.get("label", "") for theme in row["top_themes"]][:5]
            return PriorCycleContext(
                analysis_id=str(row["analysis_id"]),
                batch_label=row["batch_label"],
                run_sequence=row["run_sequence"],
                sentiment_split=row["sentiment_split"],
                top_themes=top_themes,
                executive_summary=row["executive_summary"],
            )



def save_analysis(result: AnalysisResult) -> StoredAnalysis:
    with get_connection() as connection:
        try:
            with connection.cursor() as cursor:
                _apply_runtime_migrations(cursor)

                if result.series_name:
                    cursor.execute(
                        "SELECT upsert_series(%s, %s, %s)",
                        (result.series_name, result.domain_tag, get_settings().created_by),
                    )
                    cursor.execute(
                        "SELECT get_next_run_sequence(%s) AS next_run_sequence",
                        (result.series_name,),
                    )
                    result.run_sequence = int(cursor.fetchone()["next_run_sequence"])

                db_payload = result.to_db_dict()
                cursor.execute(
                    """
                    INSERT INTO analysis_results (
                        analysis_id, series_name, run_sequence, batch_label, domain_tag,
                        record_count, sentiment_split, top_themes, executive_summary,
                        summary_details, anomaly_count, context_profile, per_record_results, prior_cycle_ref
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        result.analysis_id,
                        result.series_name,
                        result.run_sequence,
                        result.batch_label,
                        result.domain_tag,
                        result.record_count,
                        Json(db_payload["sentiment_split"]),
                        Json(db_payload["top_themes"]),
                        result.executive_summary,
                        Json(db_payload["summary_details"]),
                        result.anomaly_count,
                        Json(db_payload["context_profile"]) if db_payload["context_profile"] else None,
                        Json(db_payload["per_record_results"]),
                        result.prior_cycle_ref,
                    ),
                )

                if result.context_profile and not result.context_profile.is_empty():
                    cursor.execute(
                        """
                        INSERT INTO context_profiles (
                            analysis_id, org_name, industry, department, reporting_period, situational_notes
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (analysis_id) DO NOTHING
                        """,
                        (
                            result.analysis_id,
                            result.context_profile.org_name,
                            result.context_profile.industry,
                            result.context_profile.department,
                            result.context_profile.reporting_period,
                            result.context_profile.situational_notes,
                        ),
                    )

                batch_rows = [
                    (
                        record.record_id,
                        result.analysis_id,
                        record.sequence_number,
                        record.text_body,
                        record.sentiment_label,
                        record.confidence_score,
                        record.deviation_from_mean,
                        record.is_anomaly,
                        Json(record.theme_assignments or []),
                        record.record_timestamp,
                        record.scored,
                    )
                    for record in result.records
                ]
                execute_values(
                    cursor,
                    """
                    INSERT INTO batch_records (
                        record_id, analysis_id, sequence_number, text_body, sentiment_label,
                        confidence_score, deviation_from_mean, is_anomaly, theme_assignments,
                        record_timestamp, scored
                    ) VALUES %s
                    """,
                    batch_rows,
                )

                status = "PARTIAL" if result.records_failed else "SUCCESS"
                cursor.execute(
                    """
                    INSERT INTO pipeline_run_log (
                        analysis_id, status, records_submitted, records_scored,
                        records_failed, api_call_count, duration_seconds, error_detail
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        result.analysis_id,
                        status,
                        result.record_count,
                        result.records_scored,
                        result.records_failed,
                        result.api_call_count,
                        result.duration_seconds,
                        None if status == "SUCCESS" else "One or more records failed scoring.",
                    ),
                )

            connection.commit()
        except Exception:
            connection.rollback()
            raise

    return load_analysis(result.analysis_id)



def retry_save_pending_analysis(result: AnalysisResult) -> StoredAnalysis:
    return save_analysis(result)



def delete_analysis(analysis_id: str) -> None:
    with get_connection() as connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT analysis_id FROM analysis_results WHERE analysis_id = %s",
                    (analysis_id,),
                )
                if not cursor.fetchone():
                    raise ValueError(f"Analysis {analysis_id} not found.")

                cursor.execute(
                    "DELETE FROM analysis_results WHERE analysis_id = %s",
                    (analysis_id,),
                )
            connection.commit()
        except Exception:
            connection.rollback()
            raise



def list_analyses(filters: Optional[HistoryFilters] = None) -> list[HistoryListItem]:
    if not _database_ready():
        return []

    filters = filters or HistoryFilters()
    clauses = []
    params: list[object] = []

    if filters.series_name:
        clauses.append(sql.SQL("series_name = %s"))
        params.append(filters.series_name)
    if filters.domain_tag:
        clauses.append(sql.SQL("domain_tag = %s"))
        params.append(filters.domain_tag)
    if filters.date_from:
        clauses.append(sql.SQL("created_at >= %s"))
        params.append(datetime.combine(filters.date_from, time.min))
    if filters.date_to:
        clauses.append(sql.SQL("created_at <= %s"))
        params.append(datetime.combine(filters.date_to, time.max))

    query = sql.SQL(
        "SELECT analysis_id, batch_label, series_name, run_sequence, domain_tag, created_at, record_count, anomaly_count "
        "FROM analysis_results"
    )
    if clauses:
        query += sql.SQL(" WHERE ") + sql.SQL(" AND ").join(clauses)
    query += sql.SQL(" ORDER BY created_at DESC")

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()

    return [
        HistoryListItem(
            analysis_id=str(row["analysis_id"]),
            batch_label=row["batch_label"],
            series_name=row["series_name"],
            run_sequence=row["run_sequence"],
            domain_tag=row["domain_tag"],
            created_at=row["created_at"],
            record_count=row["record_count"],
            anomaly_count=row["anomaly_count"],
        )
        for row in rows
    ]



def load_analysis(analysis_id: str) -> StoredAnalysis:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            _apply_runtime_migrations(cursor)
            cursor.execute(
                """
                SELECT analysis_id, batch_label, domain_tag, series_name, run_sequence,
                       created_at, record_count, sentiment_split, top_themes,
                       executive_summary, summary_details, anomaly_count, context_profile,
                       per_record_results, prior_cycle_ref
                FROM analysis_results
                WHERE analysis_id = %s
                """,
                (analysis_id,),
            )
            analysis_row = cursor.fetchone()
            if not analysis_row:
                raise ValueError(f"Analysis {analysis_id} not found.")

            cursor.execute(
                """
                SELECT record_id, sequence_number, text_body, sentiment_label, confidence_score,
                       deviation_from_mean, is_anomaly, theme_assignments, record_timestamp, scored
                FROM batch_records
                WHERE analysis_id = %s
                ORDER BY sequence_number ASC
                """,
                (analysis_id,),
            )
            record_rows = cursor.fetchall()

            prior_cycle = None
            if analysis_row["prior_cycle_ref"]:
                cursor.execute(
                    """
                    SELECT analysis_id, batch_label, run_sequence, sentiment_split, top_themes, executive_summary
                    FROM analysis_results
                    WHERE analysis_id = %s
                    """,
                    (analysis_row["prior_cycle_ref"],),
                )
                prior_row = cursor.fetchone()
                if prior_row:
                    prior_cycle = PriorCycleContext(
                        analysis_id=str(prior_row["analysis_id"]),
                        batch_label=prior_row["batch_label"],
                        run_sequence=prior_row["run_sequence"],
                        sentiment_split=prior_row["sentiment_split"],
                        top_themes=[theme.get("label", "") for theme in prior_row["top_themes"]][:5],
                        executive_summary=prior_row["executive_summary"],
                    )

    context_profile = None
    if analysis_row["context_profile"]:
        context_profile = ContextProfile(**analysis_row["context_profile"])

    themes = [
        ThemeResult(
            label=theme["label"],
            frequency=theme["frequency"],
            dominant_sentiment=theme["dominant_sentiment"],
            representative_quotes=theme["representative_quotes"],
        )
        for theme in analysis_row["top_themes"]
    ]

    summary_details = analysis_row.get("summary_details") or {}
    key_takeaways = _normalize_summary_list(summary_details.get("key_takeaways"))
    priority_actions = _normalize_summary_list(summary_details.get("priority_actions"))
    issue_clusters = [
        IssueCluster(
            label=str(cluster.get("label") or "Operational issue"),
            severity=str(cluster.get("severity") or "medium"),
            frequency=int(cluster.get("frequency") or 0),
            sentiment_direction=str(cluster.get("sentiment_direction") or "neutral"),
            problem_patterns=_normalize_summary_list(cluster.get("problem_patterns")),
            evidence_quotes=_normalize_summary_list(cluster.get("evidence_quotes")),
            recommended_actions=_normalize_summary_list(cluster.get("recommended_actions")),
            trend_note=str(cluster.get("trend_note") or "").strip() or None,
        )
        for cluster in list(summary_details.get("issue_clusters") or [])
        if isinstance(cluster, dict)
    ]
    positive_signals = [
        PositiveSignal(
            label=str(signal.get("label") or "Positive signal"),
            frequency=int(signal.get("frequency") or 0),
            why_it_matters=str(signal.get("why_it_matters") or ""),
            evidence_quotes=_normalize_summary_list(signal.get("evidence_quotes")),
            recommended_preservation_actions=_normalize_summary_list(signal.get("recommended_preservation_actions")),
        )
        for signal in list(summary_details.get("positive_signals") or [])
        if isinstance(signal, dict)
    ]

    reasoning_by_id = {
        record.get("record_id"): record.get("reasoning")
        for record in analysis_row["per_record_results"]
        if isinstance(record, dict)
    }

    records = [
        StoredRecord(
            record_id=str(row["record_id"]),
            sequence_number=row["sequence_number"],
            text_body=row["text_body"],
            sentiment_label=row["sentiment_label"],
            confidence_score=float(row["confidence_score"]),
            reasoning=reasoning_by_id.get(str(row["record_id"])),
            deviation_from_mean=float(row["deviation_from_mean"]) if row["deviation_from_mean"] is not None else None,
            is_anomaly=bool(row["is_anomaly"]),
            theme_assignments=list(row["theme_assignments"] or []),
            record_timestamp=row["record_timestamp"].date().isoformat() if row["record_timestamp"] else None,
            scored=bool(row["scored"]),
        )
        for row in record_rows
    ]

    stored = StoredAnalysis(
        analysis_id=str(analysis_row["analysis_id"]),
        batch_label=analysis_row["batch_label"],
        domain_tag=analysis_row["domain_tag"],
        series_name=analysis_row["series_name"],
        run_sequence=analysis_row["run_sequence"],
        created_at=analysis_row["created_at"],
        record_count=analysis_row["record_count"],
        sentiment_split=analysis_row["sentiment_split"],
        themes=themes,
        executive_summary=analysis_row["executive_summary"],
        key_takeaways=key_takeaways,
        priority_actions=priority_actions,
        issue_clusters=issue_clusters,
        positive_signals=positive_signals,
        anomaly_flags=[],
        anomaly_count=analysis_row["anomaly_count"],
        context_profile=context_profile,
        records=records,
        prior_cycle_context=prior_cycle,
    )
    stored.anomaly_flags = run_anomaly_detection(
        stored.to_record_results(),
        timestamps=[record.record_timestamp for record in stored.records],
    )
    return stored



def export_analysis_csv(analysis_id: str) -> str:
    stored = load_analysis(analysis_id)
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=["record_id", "text_body", "sentiment_label", "confidence_score", "theme_assignments"],
    )
    writer.writeheader()
    for record in stored.records:
        writer.writerow(
            {
                "record_id": record.record_id,
                "text_body": record.text_body,
                "sentiment_label": record.sentiment_label,
                "confidence_score": record.confidence_score,
                "theme_assignments": "; ".join(record.theme_assignments),
            }
        )
    return buffer.getvalue()



def _database_ready() -> bool:
    return bool(get_settings().database_url)
