-- =============================================================================
-- Lens — PostgreSQL Schema
-- Document: schema.sql  |  Version: 0.1  |  Portfolio: S4 BA Portfolio 2026
-- Author: Hadi Mercer
--
-- 5 tables matching the ERD (Lens_ERD_001):
--   1. series_index          — named series registry
--   2. analysis_results      — core result store (central fact table)
--   3. batch_records         — normalised per-record rows
--   4. context_profiles      — separated context data (1:1 with analysis_results)
--   5. pipeline_run_log      — audit trail, permanent retention
--
-- Deployment target: Supabase (PostgreSQL 15) — free tier
-- Run order: this file top-to-bottom, then seed.sql for demo data
-- =============================================================================


-- =============================================================================
-- EXTENSION
-- gen_random_uuid() requires pgcrypto on older Postgres versions.
-- Supabase ships with uuid-ossp enabled by default — both work.
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";


-- =============================================================================
-- 1. SERIES_INDEX
--
-- Lightweight registry of named analysis series.
-- Created or updated each time a run is assigned to a series.
-- Enables autocomplete (FR-03.01) and series browser (FR-03.06).
-- series_name is UNIQUE — the natural key analysts type and reuse.
-- =============================================================================

CREATE TABLE IF NOT EXISTS series_index (
    series_id     UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    series_name   TEXT          NOT NULL,
    domain_tag    TEXT,                              -- cx | hr | ops | null (analyst-assigned)
    run_count     INTEGER       NOT NULL DEFAULT 0,
    last_run_at   TIMESTAMPTZ,
    created_by    TEXT,                              -- free-text analyst label (v1: no auth)
    created_at    TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    CONSTRAINT series_name_unique UNIQUE (series_name),
    CONSTRAINT run_count_non_negative CHECK (run_count >= 0)
);

COMMENT ON TABLE  series_index              IS 'Registry of named analysis series. One row per unique series_name.';
COMMENT ON COLUMN series_index.series_name  IS 'Human-readable name assigned by analyst at batch label step (max 100 chars).';
COMMENT ON COLUMN series_index.domain_tag   IS 'Domain context for the series: cx, hr, ops, or null if untagged.';
COMMENT ON COLUMN series_index.run_count    IS 'Incremented on each successful pipeline write. Used for autocomplete ordering.';
COMMENT ON COLUMN series_index.last_run_at  IS 'Timestamp of the most recent completed run in this series.';


-- =============================================================================
-- 2. ANALYSIS_RESULTS
--
-- Central fact table. One row per completed pipeline run.
-- All other tables reference this via analysis_id (FK).
-- JSONB fields carry structured output — see design notes in FRD Section 6.
--
-- prior_cycle_ref is a self-referential FK — points to the previous run
-- in the same series. NULL for series run 1 and all standalone runs.
-- =============================================================================

CREATE TABLE IF NOT EXISTS analysis_results (
    -- Identity
    analysis_id         UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    series_name         TEXT          REFERENCES series_index (series_name)
                                        ON UPDATE CASCADE ON DELETE SET NULL,
    run_sequence        INTEGER,                    -- position within series (1, 2, 3...)
    batch_label         TEXT          NOT NULL,     -- human-readable label, e.g. "NPS Q1 2026"
    domain_tag          TEXT,                       -- cx | hr | ops

    -- Batch metadata
    record_count        INTEGER       NOT NULL,
    created_at          TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    -- NLP outputs (JSONB — structure varies per run)
    sentiment_split     JSONB         NOT NULL,
    -- {"positive": 42.1, "neutral": 38.0, "negative": 19.9}

    top_themes          JSONB         NOT NULL DEFAULT '[]'::JSONB,
    -- [{"label": "...", "frequency": 12, "dominant_sentiment": "negative",
    --   "representative_quotes": ["...", "..."]}]

    executive_summary   TEXT,
    anomaly_count       INTEGER       NOT NULL DEFAULT 0,

    context_profile     JSONB,
    -- Snapshot at run time. Nullable — not all runs have context.
    -- {"org_name": "...", "industry": "...", "department": "...",
    --  "reporting_period": "...", "situational_notes": "..."}

    per_record_results  JSONB         NOT NULL DEFAULT '[]'::JSONB,
    -- Full scored array. Also normalised into batch_records for query flexibility.
    -- [{"record_id": "...", "sequence_number": 1, "sentiment_label": "positive",
    --   "confidence_score": 0.92, "reasoning": "...", "is_anomaly": false,
    --   "theme_assignments": ["..."]}]

    -- Longitudinal reference
    prior_cycle_ref     UUID          REFERENCES analysis_results (analysis_id)
                                        ON DELETE SET NULL,
    -- Self-referential. Points to the most recent prior run in the same series.

    CONSTRAINT run_sequence_positive CHECK (run_sequence IS NULL OR run_sequence > 0),
    CONSTRAINT record_count_positive  CHECK (record_count > 0),
    CONSTRAINT anomaly_count_non_neg  CHECK (anomaly_count >= 0),
    CONSTRAINT domain_tag_values      CHECK (domain_tag IN ('cx', 'hr', 'ops') OR domain_tag IS NULL),
    CONSTRAINT sentiment_split_keys   CHECK (
        sentiment_split ? 'positive' AND
        sentiment_split ? 'neutral'  AND
        sentiment_split ? 'negative'
    )
);

COMMENT ON TABLE  analysis_results                IS 'Core result store. One row per completed pipeline run. Central fact table.';
COMMENT ON COLUMN analysis_results.series_name    IS 'FK to series_index. NULL for standalone (non-series) runs.';
COMMENT ON COLUMN analysis_results.run_sequence   IS 'Run number within its series (1-indexed). NULL for standalone runs.';
COMMENT ON COLUMN analysis_results.sentiment_split IS 'JSONB: {"positive": %, "neutral": %, "negative": %}. Always populated.';
COMMENT ON COLUMN analysis_results.top_themes     IS 'JSONB array of theme objects from P2.4. 5-8 items per run.';
COMMENT ON COLUMN analysis_results.context_profile IS 'JSONB snapshot of context at run time. Nullable.';
COMMENT ON COLUMN analysis_results.per_record_results IS 'JSONB full scored array. Denormalised copy — batch_records holds the queryable rows.';
COMMENT ON COLUMN analysis_results.prior_cycle_ref IS 'Self-referential FK. Points to prior run in same series for longitudinal injection.';


-- =============================================================================
-- 3. BATCH_RECORDS
--
-- Normalised per-record detail table.
-- Populated from per_record_results JSONB at write time.
-- Exists to support: CSV export (FR-04.03), history query, theme assignment query.
-- text_body is retained only to support export — not a permanent archive intent.
-- =============================================================================

CREATE TABLE IF NOT EXISTS batch_records (
    record_id             UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id           UUID          NOT NULL REFERENCES analysis_results (analysis_id)
                                          ON DELETE CASCADE,
    sequence_number       INTEGER       NOT NULL,   -- position within the batch (1-indexed)
    text_body             TEXT          NOT NULL,
    sentiment_label       TEXT          NOT NULL,   -- positive | neutral | negative
    confidence_score      NUMERIC(4,3)  NOT NULL,   -- 0.000–1.000
    deviation_from_mean   NUMERIC,                  -- signed σ value; NULL if not scored
    is_anomaly            BOOLEAN       NOT NULL DEFAULT FALSE,
    theme_assignments     JSONB,                    -- ["theme label 1", "theme label 2"]
    record_timestamp      TIMESTAMPTZ,              -- from source if present (enables time panel)
    scored                BOOLEAN       NOT NULL DEFAULT TRUE,
    -- FALSE if all API retries exhausted (FR-02.03 constraint)

    CONSTRAINT sentiment_label_values   CHECK (sentiment_label IN ('positive', 'neutral', 'negative')),
    CONSTRAINT confidence_score_range   CHECK (confidence_score >= 0 AND confidence_score <= 1),
    CONSTRAINT sequence_number_positive CHECK (sequence_number > 0)
);

COMMENT ON TABLE  batch_records                    IS 'Normalised per-record rows. One row per text record per analysis run.';
COMMENT ON COLUMN batch_records.analysis_id        IS 'FK to analysis_results. CASCADE delete — records deleted with their parent run.';
COMMENT ON COLUMN batch_records.sequence_number    IS 'Original position in uploaded batch (1-indexed).';
COMMENT ON COLUMN batch_records.confidence_score   IS 'OpenAI confidence score 0.000–1.000.';
COMMENT ON COLUMN batch_records.deviation_from_mean IS 'Signed σ deviation from batch mean score. NULL for unscored records.';
COMMENT ON COLUMN batch_records.is_anomaly         IS 'TRUE when |deviation_from_mean| >= 2σ or flagged as time-series spike.';
COMMENT ON COLUMN batch_records.theme_assignments  IS 'JSONB array of theme labels assigned to this record.';
COMMENT ON COLUMN batch_records.record_timestamp   IS 'Parsed from optional timestamp column in source CSV.';
COMMENT ON COLUMN batch_records.scored             IS 'FALSE if all API retries failed. Record retained with placeholder values.';


-- =============================================================================
-- 4. CONTEXT_PROFILES
--
-- Separated context data — 1:1 with analysis_results.
-- Kept separate to keep the main table clean and because not all runs have context.
-- Nullable fields: all context input is optional (FR-02.01).
-- =============================================================================

CREATE TABLE IF NOT EXISTS context_profiles (
    profile_id          UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id         UUID    NOT NULL UNIQUE
                                  REFERENCES analysis_results (analysis_id)
                                  ON DELETE CASCADE,
    org_name            TEXT,                       -- max 100 chars in app layer
    industry            TEXT,                       -- max 80 chars
    department          TEXT,                       -- max 100 chars
    reporting_period    TEXT,                       -- max 60 chars, e.g. "Q1 2026"
    situational_notes   TEXT,                       -- max 500 chars (FR-02.01 constraint)
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT situational_notes_length CHECK (
        situational_notes IS NULL OR char_length(situational_notes) <= 500
    )
);

COMMENT ON TABLE  context_profiles                  IS 'Optional analyst context per run. 1:1 with analysis_results. All fields nullable.';
COMMENT ON COLUMN context_profiles.analysis_id      IS 'UNIQUE FK — enforces 1:1 relationship with analysis_results.';
COMMENT ON COLUMN context_profiles.situational_notes IS 'Free text, max 500 chars (enforced at DB and app layer).';


-- =============================================================================
-- 5. PIPELINE_RUN_LOG
--
-- Audit trail for every pipeline execution attempt.
-- Retained permanently — supports debugging and portfolio demo of run history.
-- Includes PARTIAL and FAILED runs, not only SUCCESS.
-- =============================================================================

CREATE TABLE IF NOT EXISTS pipeline_run_log (
    log_id              UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id         UUID    REFERENCES analysis_results (analysis_id)
                                  ON DELETE SET NULL,
    -- SET NULL (not CASCADE) — retain log even if result is deleted
    triggered_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status              TEXT    NOT NULL,           -- SUCCESS | PARTIAL | FAILED
    records_submitted   INTEGER NOT NULL DEFAULT 0,
    records_scored      INTEGER NOT NULL DEFAULT 0,
    records_failed      INTEGER NOT NULL DEFAULT 0,
    api_call_count      INTEGER NOT NULL DEFAULT 0,
    duration_seconds    NUMERIC,
    error_detail        TEXT,                       -- populated on PARTIAL or FAILED

    CONSTRAINT status_values CHECK (status IN ('SUCCESS', 'PARTIAL', 'FAILED')),
    CONSTRAINT records_submitted_non_neg CHECK (records_submitted >= 0),
    CONSTRAINT records_scored_non_neg    CHECK (records_scored >= 0),
    CONSTRAINT records_failed_non_neg    CHECK (records_failed >= 0)
);

COMMENT ON TABLE  pipeline_run_log              IS 'Permanent audit log for every pipeline execution. Retained even if analysis_results row is deleted.';
COMMENT ON COLUMN pipeline_run_log.analysis_id  IS 'FK SET NULL on delete — log survives if result is deleted.';
COMMENT ON COLUMN pipeline_run_log.status       IS 'SUCCESS = all records scored. PARTIAL = some failed. FAILED = pipeline aborted.';
COMMENT ON COLUMN pipeline_run_log.error_detail IS 'Exception message or stage name on PARTIAL/FAILED runs.';


-- =============================================================================
-- INDEXES
--
-- Designed for the three query patterns that matter for this app:
--   1. Longitudinal injection query (FR-03.02):
--      SELECT ... FROM analysis_results WHERE series_name = ? ORDER BY run_sequence DESC LIMIT 1
--   2. History browser query (FR-04.02):
--      SELECT ... FROM analysis_results WHERE domain_tag = ? ORDER BY created_at DESC
--   3. CSV export + dashboard render (FR-04.03):
--      SELECT ... FROM batch_records WHERE analysis_id = ? ORDER BY sequence_number
-- =============================================================================

-- Analysis results: primary query patterns
CREATE INDEX IF NOT EXISTS idx_analysis_series_seq
    ON analysis_results (series_name, run_sequence DESC)
    WHERE series_name IS NOT NULL;
-- Used by: FR-03.02 prior cycle retrieval, FR-03.06 series trend display

CREATE INDEX IF NOT EXISTS idx_analysis_created
    ON analysis_results (created_at DESC);
-- Used by: FR-04.02 history browser default sort

CREATE INDEX IF NOT EXISTS idx_analysis_domain_created
    ON analysis_results (domain_tag, created_at DESC)
    WHERE domain_tag IS NOT NULL;
-- Used by: FR-04.02 history browser domain_tag filter

-- Batch records: export and dashboard queries
CREATE INDEX IF NOT EXISTS idx_batch_records_analysis
    ON batch_records (analysis_id, sequence_number);
-- Used by: FR-04.03 CSV export, dashboard per-record histogram

CREATE INDEX IF NOT EXISTS idx_batch_records_anomaly
    ON batch_records (analysis_id, is_anomaly)
    WHERE is_anomaly = TRUE;
-- Used by: anomaly flags panel (filtered view)

CREATE INDEX IF NOT EXISTS idx_batch_records_timestamp
    ON batch_records (analysis_id, record_timestamp)
    WHERE record_timestamp IS NOT NULL;
-- Used by: sentiment over time panel (FR-01.04, FR-02.07)

-- Series index: autocomplete query
CREATE INDEX IF NOT EXISTS idx_series_name_trgm
    ON series_index (series_name);
-- Used by: FR-03.01 series name autocomplete

-- Pipeline log: debugging queries
CREATE INDEX IF NOT EXISTS idx_pipeline_log_analysis
    ON pipeline_run_log (analysis_id, triggered_at DESC)
    WHERE analysis_id IS NOT NULL;


-- =============================================================================
-- HELPER FUNCTION: upsert_series
--
-- Called by the storage layer after a successful pipeline run.
-- Creates the series if it doesn't exist, or increments run_count.
-- Using INSERT ... ON CONFLICT to avoid race conditions.
-- =============================================================================

CREATE OR REPLACE FUNCTION upsert_series(
    p_series_name  TEXT,
    p_domain_tag   TEXT,
    p_created_by   TEXT DEFAULT NULL
)
RETURNS UUID
LANGUAGE plpgsql
AS $$
DECLARE
    v_series_id UUID;
BEGIN
    INSERT INTO series_index (series_name, domain_tag, run_count, last_run_at, created_by)
    VALUES (p_series_name, p_domain_tag, 1, NOW(), p_created_by)
    ON CONFLICT (series_name) DO UPDATE
        SET run_count   = series_index.run_count + 1,
            last_run_at = NOW(),
            domain_tag  = COALESCE(EXCLUDED.domain_tag, series_index.domain_tag)
    RETURNING series_id INTO v_series_id;

    RETURN v_series_id;
END;
$$;

COMMENT ON FUNCTION upsert_series IS
    'Creates a new series or increments run_count on conflict. Returns series_id. '
    'Called by the Python storage layer after each successful pipeline run.';


-- =============================================================================
-- HELPER FUNCTION: get_prior_cycle
--
-- Called by the pipeline runner BEFORE execution to retrieve prior cycle data.
-- Returns the most recent completed run for a given series_name.
-- Corresponds to: FR-03.02
-- =============================================================================

CREATE OR REPLACE FUNCTION get_prior_cycle(p_series_name TEXT)
RETURNS TABLE (
    analysis_id       UUID,
    batch_label       TEXT,
    run_sequence      INTEGER,
    sentiment_split   JSONB,
    top_themes        JSONB,
    executive_summary TEXT
)
LANGUAGE sql
STABLE
AS $$
    SELECT
        analysis_id,
        batch_label,
        run_sequence,
        sentiment_split,
        top_themes,
        executive_summary
    FROM  analysis_results
    WHERE series_name = p_series_name
      AND run_sequence IS NOT NULL
    ORDER BY run_sequence DESC
    LIMIT 1;
$$;

COMMENT ON FUNCTION get_prior_cycle IS
    'Returns the most recent completed run for a series. '
    'Used by the pipeline runner for longitudinal context injection (FR-03.02).';


-- =============================================================================
-- HELPER FUNCTION: get_next_run_sequence
--
-- Returns the next run_sequence integer for a given series.
-- Called when writing a new analysis result to assign the correct sequence number.
-- =============================================================================

CREATE OR REPLACE FUNCTION get_next_run_sequence(p_series_name TEXT)
RETURNS INTEGER
LANGUAGE sql
STABLE
AS $$
    SELECT COALESCE(MAX(run_sequence), 0) + 1
    FROM  analysis_results
    WHERE series_name = p_series_name;
$$;

COMMENT ON FUNCTION get_next_run_sequence IS
    'Returns the next run_sequence for a series (MAX + 1). Returns 1 for a new series.';


-- =============================================================================
-- ROW LEVEL SECURITY (RLS) — PLACEHOLDER
--
-- RLS is NOT enabled in v1 (single-session Streamlit deployment, no auth).
-- These stubs document the Phase 2 intent: per-analyst row isolation.
-- Uncomment and configure when adding user authentication.
-- =============================================================================

-- ALTER TABLE analysis_results  ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE batch_records      ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE context_profiles   ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE pipeline_run_log   ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE series_index       ENABLE ROW LEVEL SECURITY;

-- CREATE POLICY analyst_isolation ON analysis_results
--     USING (auth.uid()::text = created_by);


-- =============================================================================
-- SCHEMA COMPLETE
-- Next step: seed.sql — 3 pre-loaded series (CX / HR / Ops) with 2-3 runs each.
-- This satisfies FR-04.05: demo dataset visible on first Streamlit Cloud deploy.
-- =============================================================================
