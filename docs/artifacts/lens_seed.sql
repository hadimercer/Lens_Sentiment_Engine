-- =============================================================================
-- Lens — Demo Seed Data
-- Document: seed.sql  |  Version: 0.1  |  Portfolio: S4 BA Portfolio 2026
-- Author: Hadi Mercer
--
-- Satisfies FR-04.05: 3 pre-loaded series (CX, HR, Ops) with 2-3 completed
-- runs each, demonstrating longitudinal output and all four dashboard panels.
--
-- Run AFTER schema.sql.
-- Safe to re-run: all INSERTs use ON CONFLICT DO NOTHING.
--
-- SERIES OVERVIEW
-- ─────────────────────────────────────────────────────────────────
--   CX  — Meridian SaaS    "NPS Q-Series"       3 runs (Q3→Q4 2025→Q1 2026)
--   HR  — Meridian SaaS    "Engagement Pulse"   3 runs (H1→H2 2025→Q1 2026)
--   OPS — Meridian SaaS    "Support Ticket Log" 2 runs (Jan→Feb 2026)
--
-- Each run has:
--   - sentiment_split + top_themes + executive_summary populated
--   - per_record_results with 12-15 records (mix of pos/neu/neg)
--   - run 2+ executive summaries contain explicit comparative language
--   - CX run 3 includes record_timestamp values → enables time-series panel
--   - anomaly_count > 0 in at least one run per series
-- =============================================================================


BEGIN;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- FIXED UUIDs (reference)
-- All UUIDs are used as inline literals throughout this file.
-- CX runs:  a1000001-0000-0000-0000-000000000001/2/3
-- HR runs:  b2000001-0000-0000-0000-000000000001/2/3
-- Ops runs: c3000001-0000-0000-0000-000000000001/2
-- =============================================================================


-- =============================================================================
-- SERIES INDEX
-- =============================================================================

INSERT INTO series_index (series_id, series_name, domain_tag, run_count, last_run_at, created_by, created_at)
VALUES
    (
        'a1000001-ffff-0000-0000-000000000000',
        'NPS Q-Series',
        'cx',
        3,
        '2026-02-01 09:00:00+00',
        'Demo — Meridian SaaS CX Team',
        '2025-07-01 09:00:00+00'
    ),
    (
        'b2000001-ffff-0000-0000-000000000000',
        'Engagement Pulse',
        'hr',
        3,
        '2026-01-15 10:00:00+00',
        'Demo — Meridian SaaS HR',
        '2025-01-10 09:00:00+00'
    ),
    (
        'c3000001-ffff-0000-0000-000000000000',
        'Support Ticket Log',
        'ops',
        2,
        '2026-02-28 14:00:00+00',
        'Demo — Meridian SaaS Ops',
        '2026-01-02 09:00:00+00'
    )
ON CONFLICT (series_name) DO NOTHING;


-- =============================================================================
-- ── CX SERIES: "NPS Q-Series" ────────────────────────────────────────────────
-- Context: B2B SaaS company, post-platform-migration feedback
-- Run 1 (Q3 2025): Baseline — mixed, billing pain dominant
-- Run 2 (Q4 2025): Modest improvement, billing improving, onboarding friction rises
-- Run 3 (Q1 2026): Further improvement, onboarding resolved, API docs gap emerges
--                  Includes record_timestamp → enables Sentiment Over Time panel
-- =============================================================================

-- ── CX RUN 1: NPS Q3 2025 ────────────────────────────────────────────────────

INSERT INTO analysis_results (
    analysis_id, series_name, run_sequence, batch_label, domain_tag,
    record_count, sentiment_split, top_themes, executive_summary,
    anomaly_count, context_profile, prior_cycle_ref, per_record_results, created_at
)
VALUES (
    'a1000001-0000-0000-0000-000000000001',
    'NPS Q-Series', 1, 'NPS Q3 2025', 'cx',
    14,
    '{"positive": 42.9, "neutral": 28.6, "negative": 28.6}'::JSONB,
    '[
        {"label": "billing errors and delays",      "frequency": 5, "dominant_sentiment": "negative", "representative_quotes": ["Billing error took 6 emails to fix.", "Charged twice and no one responded for two weeks."]},
        {"label": "onboarding experience",           "frequency": 4, "dominant_sentiment": "positive", "representative_quotes": ["The onboarding process was seamless.", "Setup was straightforward with good support."]},
        {"label": "support response time",           "frequency": 4, "dominant_sentiment": "negative", "representative_quotes": ["Waited 3 weeks for a response.", "Support ticket open for 10 days with no update."]},
        {"label": "product value and reliability",   "frequency": 3, "dominant_sentiment": "positive", "representative_quotes": ["Excellent value for money.", "No issues in three months of use."]},
        {"label": "documentation gaps",              "frequency": 2, "dominant_sentiment": "neutral",  "representative_quotes": ["Product works but docs could be clearer.", "Had to figure out integration myself."]}
    ]'::JSONB,
    'Q3 2025 NPS feedback for Meridian SaaS reflects a mixed landscape: just under half of respondents are positive, with billing errors and slow support response times driving the negative segment. Onboarding satisfaction is a relative strength, though documentation gaps signal a growing friction point as the customer base scales.',
    1,
    '{"org_name": "Meridian SaaS", "industry": "B2B Software", "department": "Customer Experience", "reporting_period": "Q3 2025", "situational_notes": "Post-platform migration. First NPS cycle following the July infrastructure upgrade."}'::JSONB,
    NULL,
    '[
        {"record_id": "a1r001", "sequence_number": 1,  "sentiment_label": "positive", "confidence_score": 0.91, "reasoning": "Clear satisfaction with onboarding process.", "is_anomaly": false, "theme_assignments": ["onboarding experience"]},
        {"record_id": "a1r002", "sequence_number": 2,  "sentiment_label": "negative", "confidence_score": 0.94, "reasoning": "Strong frustration expressed about billing error resolution time.", "is_anomaly": false, "theme_assignments": ["billing errors and delays"]},
        {"record_id": "a1r003", "sequence_number": 3,  "sentiment_label": "neutral",  "confidence_score": 0.72, "reasoning": "Acknowledges product works but identifies documentation shortfall.", "is_anomaly": false, "theme_assignments": ["documentation gaps"]},
        {"record_id": "a1r004", "sequence_number": 4,  "sentiment_label": "positive", "confidence_score": 0.88, "reasoning": "Positive outcome after initial issue, net positive sentiment.", "is_anomaly": false, "theme_assignments": ["support response time"]},
        {"record_id": "a1r005", "sequence_number": 5,  "sentiment_label": "negative", "confidence_score": 0.89, "reasoning": "Explicit cancellation intent following repeated billing failure.", "is_anomaly": true,  "theme_assignments": ["billing errors and delays", "support response time"]},
        {"record_id": "a1r006", "sequence_number": 6,  "sentiment_label": "positive", "confidence_score": 0.95, "reasoning": "Strong product endorsement with recommendation intent.", "is_anomaly": false, "theme_assignments": ["product value and reliability"]},
        {"record_id": "a1r007", "sequence_number": 7,  "sentiment_label": "negative", "confidence_score": 0.86, "reasoning": "No explanation provided for account lockout, high frustration.", "is_anomaly": false, "theme_assignments": ["support response time"]},
        {"record_id": "a1r008", "sequence_number": 8,  "sentiment_label": "positive", "confidence_score": 0.82, "reasoning": "Dashboard improvement noted positively.", "is_anomaly": false, "theme_assignments": ["product value and reliability"]},
        {"record_id": "a1r009", "sequence_number": 9,  "sentiment_label": "neutral",  "confidence_score": 0.68, "reasoning": "Integration friction acknowledged but not strongly negative.", "is_anomaly": false, "theme_assignments": ["documentation gaps"]},
        {"record_id": "a1r010", "sequence_number": 10, "sentiment_label": "positive", "confidence_score": 0.93, "reasoning": "Enthusiastic endorsement, no issues in three months.", "is_anomaly": false, "theme_assignments": ["product value and reliability"]},
        {"record_id": "a1r011", "sequence_number": 11, "sentiment_label": "negative", "confidence_score": 0.77, "reasoning": "Slow ticket response eroding trust.", "is_anomaly": false, "theme_assignments": ["support response time"]},
        {"record_id": "a1r012", "sequence_number": 12, "sentiment_label": "positive", "confidence_score": 0.90, "reasoning": "Feature request implemented quickly — strong positive.", "is_anomaly": false, "theme_assignments": ["product value and reliability"]},
        {"record_id": "a1r013", "sequence_number": 13, "sentiment_label": "negative", "confidence_score": 0.83, "reasoning": "Double billing with no response — high frustration.", "is_anomaly": false, "theme_assignments": ["billing errors and delays"]},
        {"record_id": "a1r014", "sequence_number": 14, "sentiment_label": "neutral",  "confidence_score": 0.65, "reasoning": "Neutral acknowledgement of product performance.", "is_anomaly": false, "theme_assignments": []}
    ]'::JSONB,
    '2025-08-02 09:00:00+00'
) ON CONFLICT (analysis_id) DO NOTHING;

-- ── CX RUN 2: NPS Q4 2025 ────────────────────────────────────────────────────

INSERT INTO analysis_results (
    analysis_id, series_name, run_sequence, batch_label, domain_tag,
    record_count, sentiment_split, top_themes, executive_summary,
    anomaly_count, context_profile, prior_cycle_ref, per_record_results, created_at
)
VALUES (
    'a1000001-0000-0000-0000-000000000002',
    'NPS Q-Series', 2, 'NPS Q4 2025', 'cx',
    14,
    '{"positive": 50.0, "neutral": 28.6, "negative": 21.4}'::JSONB,
    '[
        {"label": "billing errors and delays",      "frequency": 3, "dominant_sentiment": "negative", "representative_quotes": ["Still seeing occasional billing discrepancies.", "Invoice was wrong but fixed within 48 hours this time."]},
        {"label": "onboarding friction",             "frequency": 4, "dominant_sentiment": "negative", "representative_quotes": ["New user setup is taking longer than it should.", "Three of my team members struggled with the initial configuration."]},
        {"label": "support response time",           "frequency": 3, "dominant_sentiment": "neutral",  "representative_quotes": ["Response times have improved but still inconsistent.", "Got a response within 24 hours — much better than before."]},
        {"label": "product value and reliability",   "frequency": 4, "dominant_sentiment": "positive", "representative_quotes": ["The platform has been rock solid this quarter.", "ROI is clearly there — renewing without hesitation."]},
        {"label": "documentation gaps",              "frequency": 2, "dominant_sentiment": "neutral",  "representative_quotes": ["Docs still sparse for advanced API use.", "Knowledge base helps but video tutorials would be better."]}
    ]'::JSONB,
    'Q4 2025 NPS feedback shows meaningful improvement from Q3: positive sentiment has risen from 43% to 50% and the billing error theme, which dominated Q3, has declined in both frequency and severity — likely reflecting the billing system fixes deployed in October. However, onboarding friction has emerged as the new primary negative theme, replacing billing as the dominant concern, suggesting the platform upgrade has introduced new complexity for first-time users.',
    2,
    '{"org_name": "Meridian SaaS", "industry": "B2B Software", "department": "Customer Experience", "reporting_period": "Q4 2025", "situational_notes": "Second NPS cycle. October billing system patch deployed mid-quarter."}'::JSONB,
    'a1000001-0000-0000-0000-000000000001',
    '[
        {"record_id": "a2r001", "sequence_number": 1,  "sentiment_label": "positive", "confidence_score": 0.92, "reasoning": "Strong quarterly satisfaction with no major issues.", "is_anomaly": false, "theme_assignments": ["product value and reliability"]},
        {"record_id": "a2r002", "sequence_number": 2,  "sentiment_label": "negative", "confidence_score": 0.81, "reasoning": "Onboarding setup issues for new team members.", "is_anomaly": false, "theme_assignments": ["onboarding friction"]},
        {"record_id": "a2r003", "sequence_number": 3,  "sentiment_label": "neutral",  "confidence_score": 0.70, "reasoning": "Support improved but inconsistency noted.", "is_anomaly": false, "theme_assignments": ["support response time"]},
        {"record_id": "a2r004", "sequence_number": 4,  "sentiment_label": "positive", "confidence_score": 0.89, "reasoning": "Platform stability praised — renewal confirmed.", "is_anomaly": false, "theme_assignments": ["product value and reliability"]},
        {"record_id": "a2r005", "sequence_number": 5,  "sentiment_label": "negative", "confidence_score": 0.85, "reasoning": "Configuration complexity for new users flagged.", "is_anomaly": false, "theme_assignments": ["onboarding friction"]},
        {"record_id": "a2r006", "sequence_number": 6,  "sentiment_label": "positive", "confidence_score": 0.94, "reasoning": "Billing issue resolved quickly — positive outcome.", "is_anomaly": false, "theme_assignments": ["billing errors and delays"]},
        {"record_id": "a2r007", "sequence_number": 7,  "sentiment_label": "neutral",  "confidence_score": 0.66, "reasoning": "Documentation gaps acknowledged without strong sentiment.", "is_anomaly": false, "theme_assignments": ["documentation gaps"]},
        {"record_id": "a2r008", "sequence_number": 8,  "sentiment_label": "positive", "confidence_score": 0.91, "reasoning": "Overall positive experience, minor friction noted.", "is_anomaly": false, "theme_assignments": ["product value and reliability"]},
        {"record_id": "a2r009", "sequence_number": 9,  "sentiment_label": "negative", "confidence_score": 0.78, "reasoning": "Onboarding duration too long for enterprise rollout.", "is_anomaly": false, "theme_assignments": ["onboarding friction"]},
        {"record_id": "a2r010", "sequence_number": 10, "sentiment_label": "positive", "confidence_score": 0.87, "reasoning": "Positive sentiment about support improvement trajectory.", "is_anomaly": false, "theme_assignments": ["support response time"]},
        {"record_id": "a2r011", "sequence_number": 11, "sentiment_label": "negative", "confidence_score": 0.97, "reasoning": "Strongest negative in batch — multiple onboarding failures described.", "is_anomaly": true, "theme_assignments": ["onboarding friction"]},
        {"record_id": "a2r012", "sequence_number": 12, "sentiment_label": "positive", "confidence_score": 0.90, "reasoning": "Renewed contract, cites platform ROI explicitly.", "is_anomaly": false, "theme_assignments": ["product value and reliability"]},
        {"record_id": "a2r013", "sequence_number": 13, "sentiment_label": "neutral",  "confidence_score": 0.69, "reasoning": "Residual billing concern but tone not strongly negative.", "is_anomaly": false, "theme_assignments": ["billing errors and delays"]},
        {"record_id": "a2r014", "sequence_number": 14, "sentiment_label": "positive", "confidence_score": 0.88, "reasoning": "Advanced API docs lacking but core product praised.", "is_anomaly": false, "theme_assignments": ["documentation gaps"]}
    ]'::JSONB,
    '2026-01-06 09:00:00+00'
) ON CONFLICT (analysis_id) DO NOTHING;

-- ── CX RUN 3: NPS Q1 2026 ────────────────────────────────────────────────────
-- This run has record_timestamp values — enables the Sentiment Over Time panel
-- and the time-series anomaly spike detection.

INSERT INTO analysis_results (
    analysis_id, series_name, run_sequence, batch_label, domain_tag,
    record_count, sentiment_split, top_themes, executive_summary,
    anomaly_count, context_profile, prior_cycle_ref, per_record_results, created_at
)
VALUES (
    'a1000001-0000-0000-0000-000000000003',
    'NPS Q-Series', 3, 'NPS Q1 2026', 'cx',
    15,
    '{"positive": 60.0, "neutral": 26.7, "negative": 13.3}'::JSONB,
    '[
        {"label": "onboarding resolution",           "frequency": 4, "dominant_sentiment": "positive", "representative_quotes": ["The new setup wizard fixed our onboarding issues completely.", "Onboarding is now the smoothest part of the whole process."]},
        {"label": "API documentation gaps",          "frequency": 4, "dominant_sentiment": "negative", "representative_quotes": ["Still no working examples for the webhooks endpoint.", "API docs are years behind the actual product."]},
        {"label": "product value and reliability",   "frequency": 5, "dominant_sentiment": "positive", "representative_quotes": ["Three quarters in and the uptime has been flawless.", "Best ROI of any tool in our stack."]},
        {"label": "support quality",                 "frequency": 3, "dominant_sentiment": "positive", "representative_quotes": ["Support team has been exceptional this quarter.", "Response time and quality both excellent."]},
        {"label": "billing accuracy",                "frequency": 2, "dominant_sentiment": "positive", "representative_quotes": ["Billing has been accurate every month for two quarters.", "No billing surprises — completely resolved."]}
    ]'::JSONB,
    'Q1 2026 NPS feedback marks a continued positive trajectory for Meridian SaaS: positive sentiment has risen to 60%, up from 50% in Q4 2025 and 43% in Q3 2025, confirming the upward trend over three consecutive cycles. The onboarding friction theme that dominated Q4 has been largely resolved — replaced by positive references to the new setup wizard — while billing accuracy, previously the primary pain point in Q3, is now cited positively. However, API documentation gaps have emerged as the new unresolved theme, growing in both frequency and specificity, and represent the clearest action item heading into Q2.',
    1,
    '{"org_name": "Meridian SaaS", "industry": "B2B Software", "department": "Customer Experience", "reporting_period": "Q1 2026", "situational_notes": "Third NPS cycle. New customer setup wizard released in December. API v2 documentation still pending."}'::JSONB,
    'a1000001-0000-0000-0000-000000000002',
    '[
        {"record_id": "a3r001", "sequence_number": 1,  "sentiment_label": "positive", "confidence_score": 0.95, "reasoning": "Onboarding wizard praised explicitly.", "is_anomaly": false, "theme_assignments": ["onboarding resolution"], "record_timestamp": "2026-01-05"},
        {"record_id": "a3r002", "sequence_number": 2,  "sentiment_label": "negative", "confidence_score": 0.88, "reasoning": "Webhook API docs flagged as severely out of date.", "is_anomaly": false, "theme_assignments": ["API documentation gaps"], "record_timestamp": "2026-01-07"},
        {"record_id": "a3r003", "sequence_number": 3,  "sentiment_label": "positive", "confidence_score": 0.93, "reasoning": "Three quarters of flawless uptime praised.", "is_anomaly": false, "theme_assignments": ["product value and reliability"], "record_timestamp": "2026-01-10"},
        {"record_id": "a3r004", "sequence_number": 4,  "sentiment_label": "positive", "confidence_score": 0.90, "reasoning": "Support team response quality explicitly praised.", "is_anomaly": false, "theme_assignments": ["support quality"], "record_timestamp": "2026-01-12"},
        {"record_id": "a3r005", "sequence_number": 5,  "sentiment_label": "neutral",  "confidence_score": 0.71, "reasoning": "API limitation noted without strong emotional response.", "is_anomaly": false, "theme_assignments": ["API documentation gaps"], "record_timestamp": "2026-01-14"},
        {"record_id": "a3r006", "sequence_number": 6,  "sentiment_label": "positive", "confidence_score": 0.96, "reasoning": "Best ROI endorsement — strongest positive in batch.", "is_anomaly": false, "theme_assignments": ["product value and reliability"], "record_timestamp": "2026-01-15"},
        {"record_id": "a3r007", "sequence_number": 7,  "sentiment_label": "negative", "confidence_score": 0.91, "reasoning": "API docs materially blocking integration work.", "is_anomaly": false, "theme_assignments": ["API documentation gaps"], "record_timestamp": "2026-01-18"},
        {"record_id": "a3r008", "sequence_number": 8,  "sentiment_label": "positive", "confidence_score": 0.89, "reasoning": "Onboarding now cited as a strength — complete reversal.", "is_anomaly": false, "theme_assignments": ["onboarding resolution"], "record_timestamp": "2026-01-19"},
        {"record_id": "a3r009", "sequence_number": 9,  "sentiment_label": "positive", "confidence_score": 0.92, "reasoning": "Billing accuracy praised — contrast to Q3 complaints.", "is_anomaly": false, "theme_assignments": ["billing accuracy"], "record_timestamp": "2026-01-22"},
        {"record_id": "a3r010", "sequence_number": 10, "sentiment_label": "neutral",  "confidence_score": 0.67, "reasoning": "Neutral reference to documentation needing updates.", "is_anomaly": false, "theme_assignments": ["API documentation gaps"], "record_timestamp": "2026-01-25"},
        {"record_id": "a3r011", "sequence_number": 11, "sentiment_label": "positive", "confidence_score": 0.94, "reasoning": "Support quality improvement noted across team.", "is_anomaly": false, "theme_assignments": ["support quality"], "record_timestamp": "2026-01-26"},
        {"record_id": "a3r012", "sequence_number": 12, "sentiment_label": "neutral",  "confidence_score": 0.73, "reasoning": "Setup wizard helped but edge cases remain.", "is_anomaly": false, "theme_assignments": ["onboarding resolution"], "record_timestamp": "2026-01-28"},
        {"record_id": "a3r013", "sequence_number": 13, "sentiment_label": "positive", "confidence_score": 0.91, "reasoning": "Reliable billing and support make renewal straightforward.", "is_anomaly": false, "theme_assignments": ["billing accuracy", "support quality"], "record_timestamp": "2026-01-29"},
        {"record_id": "a3r014", "sequence_number": 14, "sentiment_label": "negative", "confidence_score": 0.96, "reasoning": "Developer productivity severely impacted by missing API docs.", "is_anomaly": true, "theme_assignments": ["API documentation gaps"], "record_timestamp": "2026-01-30"},
        {"record_id": "a3r015", "sequence_number": 15, "sentiment_label": "positive", "confidence_score": 0.88, "reasoning": "Overall satisfaction high despite API gap.", "is_anomaly": false, "theme_assignments": ["product value and reliability"], "record_timestamp": "2026-01-31"}
    ]'::JSONB,
    '2026-02-01 09:00:00+00'
) ON CONFLICT (analysis_id) DO NOTHING;


-- =============================================================================
-- ── HR SERIES: "Engagement Pulse" ────────────────────────────────────────────
-- Context: Annual and pulse engagement surveys, People & Culture team
-- Run 1 (H1 2025): Post-reorg baseline — low engagement, change fatigue dominant
-- Run 2 (H2 2025): Stabilisation — sentiment recovering, career growth theme rises
-- Run 3 (Q1 2026): Ongoing recovery, manager quality now the swing factor
-- =============================================================================

-- ── HR RUN 1: Engagement H1 2025 ─────────────────────────────────────────────

INSERT INTO analysis_results (
    analysis_id, series_name, run_sequence, batch_label, domain_tag,
    record_count, sentiment_split, top_themes, executive_summary,
    anomaly_count, context_profile, prior_cycle_ref, per_record_results, created_at
)
VALUES (
    'b2000001-0000-0000-0000-000000000001',
    'Engagement Pulse', 1, 'Engagement H1 2025', 'hr',
    13,
    '{"positive": 30.8, "neutral": 30.8, "negative": 38.5}'::JSONB,
    '[
        {"label": "change fatigue and reorg uncertainty", "frequency": 5, "dominant_sentiment": "negative", "representative_quotes": ["Three restructures in two years — nobody knows what their role is anymore.", "Constant change without explanation is exhausting."]},
        {"label": "manager support quality",              "frequency": 4, "dominant_sentiment": "negative", "representative_quotes": ["My manager is stretched too thin to support the team.", "One-on-ones cancelled more often than they happen."]},
        {"label": "career growth visibility",             "frequency": 3, "dominant_sentiment": "neutral",  "representative_quotes": ["Not clear what I need to do to get promoted.", "Career paths exist on paper but not in practice."]},
        {"label": "team cohesion and culture",            "frequency": 3, "dominant_sentiment": "positive", "representative_quotes": ["My immediate team is great even if the wider org is uncertain.", "The people I work with are what keeps me here."]},
        {"label": "workload and burnout risk",            "frequency": 3, "dominant_sentiment": "negative", "representative_quotes": ["Headcount reduced but workload did not change.", "I have not taken a full week off in 18 months."]}
    ]'::JSONB,
    'H1 2025 engagement feedback reflects the aftermath of two organisational restructures: negative sentiment leads at 38%, driven by change fatigue, unclear role definitions, and under-resourced managers. Workload and burnout signals are present in roughly a quarter of responses and represent the highest-urgency risk. Team cohesion at the immediate team level is a genuine strength and appears to be the primary retention factor in this environment.',
    2,
    '{"org_name": "Meridian SaaS", "industry": "B2B Software", "department": "People & Culture", "reporting_period": "H1 2025", "situational_notes": "Post-reorg pulse. Two restructures completed in 18 months. Third under consideration."}'::JSONB,
    NULL,
    '[
        {"record_id": "b1r001", "sequence_number": 1,  "sentiment_label": "negative", "confidence_score": 0.92, "reasoning": "Explicit fatigue from repeated structural changes.", "is_anomaly": false, "theme_assignments": ["change fatigue and reorg uncertainty"]},
        {"record_id": "b1r002", "sequence_number": 2,  "sentiment_label": "positive", "confidence_score": 0.85, "reasoning": "Team culture cited as retention anchor.", "is_anomaly": false, "theme_assignments": ["team cohesion and culture"]},
        {"record_id": "b1r003", "sequence_number": 3,  "sentiment_label": "negative", "confidence_score": 0.88, "reasoning": "Manager overwhelmed — direct support lacking.", "is_anomaly": false, "theme_assignments": ["manager support quality"]},
        {"record_id": "b1r004", "sequence_number": 4,  "sentiment_label": "neutral",  "confidence_score": 0.70, "reasoning": "Career pathway exists but lacks practical clarity.", "is_anomaly": false, "theme_assignments": ["career growth visibility"]},
        {"record_id": "b1r005", "sequence_number": 5,  "sentiment_label": "negative", "confidence_score": 0.96, "reasoning": "Burnout indicators: no leave, unsustainable workload.", "is_anomaly": true, "theme_assignments": ["workload and burnout risk"]},
        {"record_id": "b1r006", "sequence_number": 6,  "sentiment_label": "positive", "confidence_score": 0.82, "reasoning": "Peer relationships strong despite org uncertainty.", "is_anomaly": false, "theme_assignments": ["team cohesion and culture"]},
        {"record_id": "b1r007", "sequence_number": 7,  "sentiment_label": "negative", "confidence_score": 0.90, "reasoning": "Role clarity lost after last restructure.", "is_anomaly": false, "theme_assignments": ["change fatigue and reorg uncertainty"]},
        {"record_id": "b1r008", "sequence_number": 8,  "sentiment_label": "neutral",  "confidence_score": 0.68, "reasoning": "Acknowledges change as necessary but impact on morale noted.", "is_anomaly": false, "theme_assignments": ["change fatigue and reorg uncertainty"]},
        {"record_id": "b1r009", "sequence_number": 9,  "sentiment_label": "negative", "confidence_score": 0.87, "reasoning": "1:1 frequency insufficient for current workload.", "is_anomaly": false, "theme_assignments": ["manager support quality"]},
        {"record_id": "b1r010", "sequence_number": 10, "sentiment_label": "positive", "confidence_score": 0.80, "reasoning": "Work output quality cited despite difficult conditions.", "is_anomaly": false, "theme_assignments": ["team cohesion and culture"]},
        {"record_id": "b1r011", "sequence_number": 11, "sentiment_label": "negative", "confidence_score": 0.95, "reasoning": "Workload increase post-headcount reduction explicitly cited.", "is_anomaly": true, "theme_assignments": ["workload and burnout risk"]},
        {"record_id": "b1r012", "sequence_number": 12, "sentiment_label": "neutral",  "confidence_score": 0.65, "reasoning": "Promotion criteria unclear but respondent not disengaged.", "is_anomaly": false, "theme_assignments": ["career growth visibility"]},
        {"record_id": "b1r013", "sequence_number": 13, "sentiment_label": "negative", "confidence_score": 0.83, "reasoning": "Manager stretched, 1:1s not happening consistently.", "is_anomaly": false, "theme_assignments": ["manager support quality"]}
    ]'::JSONB,
    '2025-07-15 10:00:00+00'
) ON CONFLICT (analysis_id) DO NOTHING;

-- ── HR RUN 2: Engagement H2 2025 ─────────────────────────────────────────────

INSERT INTO analysis_results (
    analysis_id, series_name, run_sequence, batch_label, domain_tag,
    record_count, sentiment_split, top_themes, executive_summary,
    anomaly_count, context_profile, prior_cycle_ref, per_record_results, created_at
)
VALUES (
    'b2000001-0000-0000-0000-000000000002',
    'Engagement Pulse', 2, 'Engagement H2 2025', 'hr',
    13,
    '{"positive": 46.2, "neutral": 30.8, "negative": 23.1}'::JSONB,
    '[
        {"label": "manager support quality",              "frequency": 4, "dominant_sentiment": "positive", "representative_quotes": ["My manager has really stepped up — more present and supportive.", "1:1s are happening and they are actually useful now."]},
        {"label": "career growth visibility",             "frequency": 4, "dominant_sentiment": "negative", "representative_quotes": ["Still no promotion framework published.", "I have been told I am performing well but nothing has moved."]},
        {"label": "change fatigue and reorg uncertainty", "frequency": 3, "dominant_sentiment": "neutral",  "representative_quotes": ["The restructure dust is settling but uncertainty lingers.", "Things feel more stable but I am not fully confident yet."]},
        {"label": "team cohesion and culture",            "frequency": 3, "dominant_sentiment": "positive", "representative_quotes": ["Team dynamics have genuinely improved since H1.", "We have a clearer sense of direction as a unit."]},
        {"label": "workload distribution",                "frequency": 2, "dominant_sentiment": "neutral",  "representative_quotes": ["Workload is more balanced but still heavy.", "Better than H1 but not sustainable long term."]}
    ]'::JSONB,
    'H2 2025 engagement feedback shows a meaningful recovery from the H1 2025 low point: positive sentiment has risen from 31% to 46%, driven primarily by improved manager visibility and a stabilisation of the reorg uncertainty that dominated the first half. The burnout and workload signals that were flagged as high-urgency in H1 have moderated, suggesting the headcount pressure may have eased. Career growth visibility has moved from neutral to negative and is now the clearest unresolved theme — employees are performing and being told so, but the absence of a published promotion framework is creating credibility risk.',
    1,
    '{"org_name": "Meridian SaaS", "industry": "B2B Software", "department": "People & Culture", "reporting_period": "H2 2025", "situational_notes": "Stabilisation check-in. No further restructures. Manager coaching programme launched in September."}'::JSONB,
    'b2000001-0000-0000-0000-000000000001',
    '[
        {"record_id": "b2r001", "sequence_number": 1,  "sentiment_label": "positive", "confidence_score": 0.90, "reasoning": "Manager improvement explicitly noted.", "is_anomaly": false, "theme_assignments": ["manager support quality"]},
        {"record_id": "b2r002", "sequence_number": 2,  "sentiment_label": "negative", "confidence_score": 0.85, "reasoning": "Performing well but no progression movement.", "is_anomaly": false, "theme_assignments": ["career growth visibility"]},
        {"record_id": "b2r003", "sequence_number": 3,  "sentiment_label": "positive", "confidence_score": 0.88, "reasoning": "1:1 quality improved, actionable feedback now received.", "is_anomaly": false, "theme_assignments": ["manager support quality"]},
        {"record_id": "b2r004", "sequence_number": 4,  "sentiment_label": "neutral",  "confidence_score": 0.72, "reasoning": "Reorg settling but full confidence not yet restored.", "is_anomaly": false, "theme_assignments": ["change fatigue and reorg uncertainty"]},
        {"record_id": "b2r005", "sequence_number": 5,  "sentiment_label": "negative", "confidence_score": 0.91, "reasoning": "No promotion framework two years running.", "is_anomaly": false, "theme_assignments": ["career growth visibility"]},
        {"record_id": "b2r006", "sequence_number": 6,  "sentiment_label": "positive", "confidence_score": 0.87, "reasoning": "Team direction clearer, cohesion strong.", "is_anomaly": false, "theme_assignments": ["team cohesion and culture"]},
        {"record_id": "b2r007", "sequence_number": 7,  "sentiment_label": "neutral",  "confidence_score": 0.67, "reasoning": "Workload improved but still heavy.", "is_anomaly": false, "theme_assignments": ["workload distribution"]},
        {"record_id": "b2r008", "sequence_number": 8,  "sentiment_label": "positive", "confidence_score": 0.89, "reasoning": "Manager coaching results visible in daily support.", "is_anomaly": false, "theme_assignments": ["manager support quality"]},
        {"record_id": "b2r009", "sequence_number": 9,  "sentiment_label": "neutral",  "confidence_score": 0.69, "reasoning": "Stabilising but lingering uncertainty acknowledged.", "is_anomaly": false, "theme_assignments": ["change fatigue and reorg uncertainty"]},
        {"record_id": "b2r010", "sequence_number": 10, "sentiment_label": "positive", "confidence_score": 0.86, "reasoning": "Team dynamics explicitly improved since H1.", "is_anomaly": false, "theme_assignments": ["team cohesion and culture"]},
        {"record_id": "b2r011", "sequence_number": 11, "sentiment_label": "negative", "confidence_score": 0.97, "reasoning": "Career stagnation — performing strongly, no recognition pathway.", "is_anomaly": true, "theme_assignments": ["career growth visibility"]},
        {"record_id": "b2r012", "sequence_number": 12, "sentiment_label": "neutral",  "confidence_score": 0.65, "reasoning": "Workload improved, still above sustainable threshold.", "is_anomaly": false, "theme_assignments": ["workload distribution"]},
        {"record_id": "b2r013", "sequence_number": 13, "sentiment_label": "positive", "confidence_score": 0.84, "reasoning": "Overall positive trajectory acknowledged.", "is_anomaly": false, "theme_assignments": ["team cohesion and culture"]}
    ]'::JSONB,
    '2026-01-15 10:00:00+00'
) ON CONFLICT (analysis_id) DO NOTHING;

-- ── HR RUN 3: Engagement Q1 2026 ─────────────────────────────────────────────

INSERT INTO analysis_results (
    analysis_id, series_name, run_sequence, batch_label, domain_tag,
    record_count, sentiment_split, top_themes, executive_summary,
    anomaly_count, context_profile, prior_cycle_ref, per_record_results, created_at
)
VALUES (
    'b2000001-0000-0000-0000-000000000003',
    'Engagement Pulse', 3, 'Engagement Q1 2026', 'hr',
    12,
    '{"positive": 58.3, "neutral": 25.0, "negative": 16.7}'::JSONB,
    '[
        {"label": "career growth and promotion clarity",  "frequency": 4, "dominant_sentiment": "positive", "representative_quotes": ["The new career framework was exactly what we needed.", "First time in two years I can see a clear path forward."]},
        {"label": "manager quality and consistency",      "frequency": 4, "dominant_sentiment": "positive", "representative_quotes": ["My manager is the best support I have had in this company.", "Consistent 1:1s with real development focus — big change from H1."]},
        {"label": "team cohesion and culture",            "frequency": 3, "dominant_sentiment": "positive", "representative_quotes": ["Team is firing on all cylinders.", "Culture feels like it is actually improving, not just in comms."]},
        {"label": "workload sustainability",              "frequency": 2, "dominant_sentiment": "negative", "representative_quotes": ["Headcount still not back to pre-reorg levels.", "Workload is manageable but fragile — one departure would break it."]},
        {"label": "pay and total compensation",           "frequency": 2, "dominant_sentiment": "negative", "representative_quotes": ["Pay has not kept pace with inflation or responsibility growth.", "Compensation review is overdue."]}
    ]'::JSONB,
    'Q1 2026 engagement feedback continues the three-cycle improvement trend: positive sentiment has reached 58%, up from 46% in H2 2025 and 31% in H1 2025 — the highest point in the series. The career growth theme, which was the primary unresolved concern in H2 2025, has turned strongly positive following the January promotion framework launch, confirming that the H2 action item has landed effectively. Manager quality is now a consistent strength. Workload fragility and compensation lag are the emerging concerns in this cycle and represent the most actionable items heading into Q2.',
    0,
    '{"org_name": "Meridian SaaS", "industry": "B2B Software", "department": "People & Culture", "reporting_period": "Q1 2026", "situational_notes": "Post-framework launch. Career development framework published January 2026. Compensation review scheduled Q2."}'::JSONB,
    'b2000001-0000-0000-0000-000000000002',
    '[
        {"record_id": "b3r001", "sequence_number": 1,  "sentiment_label": "positive", "confidence_score": 0.94, "reasoning": "Career framework praised directly.", "is_anomaly": false, "theme_assignments": ["career growth and promotion clarity"]},
        {"record_id": "b3r002", "sequence_number": 2,  "sentiment_label": "positive", "confidence_score": 0.92, "reasoning": "Manager consistency and development focus praised.", "is_anomaly": false, "theme_assignments": ["manager quality and consistency"]},
        {"record_id": "b3r003", "sequence_number": 3,  "sentiment_label": "negative", "confidence_score": 0.86, "reasoning": "Compensation lag relative to market and responsibility.", "is_anomaly": false, "theme_assignments": ["pay and total compensation"]},
        {"record_id": "b3r004", "sequence_number": 4,  "sentiment_label": "positive", "confidence_score": 0.91, "reasoning": "Clear promotion path visible for first time.", "is_anomaly": false, "theme_assignments": ["career growth and promotion clarity"]},
        {"record_id": "b3r005", "sequence_number": 5,  "sentiment_label": "positive", "confidence_score": 0.89, "reasoning": "Team culture cited as genuinely improving.", "is_anomaly": false, "theme_assignments": ["team cohesion and culture"]},
        {"record_id": "b3r006", "sequence_number": 6,  "sentiment_label": "neutral",  "confidence_score": 0.70, "reasoning": "Workload manageable but dependency on individuals noted.", "is_anomaly": false, "theme_assignments": ["workload sustainability"]},
        {"record_id": "b3r007", "sequence_number": 7,  "sentiment_label": "positive", "confidence_score": 0.93, "reasoning": "1:1 quality and development conversations strong.", "is_anomaly": false, "theme_assignments": ["manager quality and consistency"]},
        {"record_id": "b3r008", "sequence_number": 8,  "sentiment_label": "positive", "confidence_score": 0.88, "reasoning": "Team output and collaboration at high point.", "is_anomaly": false, "theme_assignments": ["team cohesion and culture"]},
        {"record_id": "b3r009", "sequence_number": 9,  "sentiment_label": "negative", "confidence_score": 0.84, "reasoning": "Workload fragility risk if headcount does not recover.", "is_anomaly": false, "theme_assignments": ["workload sustainability"]},
        {"record_id": "b3r010", "sequence_number": 10, "sentiment_label": "positive", "confidence_score": 0.90, "reasoning": "Manager described as best in company career.", "is_anomaly": false, "theme_assignments": ["manager quality and consistency"]},
        {"record_id": "b3r011", "sequence_number": 11, "sentiment_label": "neutral",  "confidence_score": 0.68, "reasoning": "Career framework positive but implementation pace could be faster.", "is_anomaly": false, "theme_assignments": ["career growth and promotion clarity"]},
        {"record_id": "b3r012", "sequence_number": 12, "sentiment_label": "negative", "confidence_score": 0.87, "reasoning": "Pay not keeping pace with inflation explicitly noted.", "is_anomaly": false, "theme_assignments": ["pay and total compensation"]}
    ]'::JSONB,
    '2026-02-12 10:00:00+00'
) ON CONFLICT (analysis_id) DO NOTHING;


-- =============================================================================
-- ── OPS SERIES: "Support Ticket Log" ─────────────────────────────────────────
-- Context: Internal ops team analysing support ticket free-text comments
-- Run 1 (Jan 2026): Post-holiday spike, SLA pressure dominant
-- Run 2 (Feb 2026): SLA improving, integration complexity emerging as new theme
-- =============================================================================

-- ── OPS RUN 1: Support Tickets Jan 2026 ──────────────────────────────────────

INSERT INTO analysis_results (
    analysis_id, series_name, run_sequence, batch_label, domain_tag,
    record_count, sentiment_split, top_themes, executive_summary,
    anomaly_count, context_profile, prior_cycle_ref, per_record_results, created_at
)
VALUES (
    'c3000001-0000-0000-0000-000000000001',
    'Support Ticket Log', 1, 'Support Tickets Jan 2026', 'ops',
    12,
    '{"positive": 25.0, "neutral": 33.3, "negative": 41.7}'::JSONB,
    '[
        {"label": "SLA breach and response delays",      "frequency": 5, "dominant_sentiment": "negative", "representative_quotes": ["P1 ticket open for 36 hours with no engineer assigned.", "SLA was 4 hours — it took 3 days."]},
        {"label": "integration and configuration issues", "frequency": 3, "dominant_sentiment": "negative", "representative_quotes": ["Webhook integration broke after the January patch.", "Configuration docs do not match actual system behaviour."]},
        {"label": "escalation handling",                  "frequency": 3, "dominant_sentiment": "negative", "representative_quotes": ["Escalated twice but no ownership assigned.", "Escalation process unclear — different agent each contact."]},
        {"label": "resolution quality",                   "frequency": 2, "dominant_sentiment": "positive", "representative_quotes": ["Issue resolved correctly first time.", "Engineer found root cause quickly and explained the fix."]},
        {"label": "holiday backlog impact",               "frequency": 2, "dominant_sentiment": "neutral",  "representative_quotes": ["Understand the holiday period caused delays.", "Volume spike expected but communication was lacking."]}
    ]'::JSONB,
    'January 2026 support ticket analysis reflects a post-holiday volume spike with significant SLA pressure: negative sentiment leads at 42%, driven by P1 and P2 response delays and unclear escalation ownership. Integration and configuration issues — concentrated around the January patch — represent a secondary but growing concern. Resolution quality when engineers do engage is rated positively, suggesting the issue is capacity and routing, not technical competence.',
    2,
    '{"org_name": "Meridian SaaS", "industry": "B2B Software", "department": "Service Operations", "reporting_period": "January 2026", "situational_notes": "Post-holiday volume spike. January platform patch released 6th. Reduced ops staffing 1st-10th Jan."}'::JSONB,
    NULL,
    '[
        {"record_id": "c1r001", "sequence_number": 1,  "sentiment_label": "negative", "confidence_score": 0.93, "reasoning": "P1 SLA severely breached with no assignment.", "is_anomaly": false, "theme_assignments": ["SLA breach and response delays"]},
        {"record_id": "c1r002", "sequence_number": 2,  "sentiment_label": "positive", "confidence_score": 0.88, "reasoning": "Resolution was fast and technically accurate.", "is_anomaly": false, "theme_assignments": ["resolution quality"]},
        {"record_id": "c1r003", "sequence_number": 3,  "sentiment_label": "negative", "confidence_score": 0.91, "reasoning": "Escalation with no ownership — systemic process issue.", "is_anomaly": false, "theme_assignments": ["escalation handling"]},
        {"record_id": "c1r004", "sequence_number": 4,  "sentiment_label": "neutral",  "confidence_score": 0.69, "reasoning": "Holiday delays understood but communication poor.", "is_anomaly": false, "theme_assignments": ["holiday backlog impact"]},
        {"record_id": "c1r005", "sequence_number": 5,  "sentiment_label": "negative", "confidence_score": 0.97, "reasoning": "3-day SLA breach on P1 — extreme case.", "is_anomaly": true, "theme_assignments": ["SLA breach and response delays"]},
        {"record_id": "c1r006", "sequence_number": 6,  "sentiment_label": "negative", "confidence_score": 0.89, "reasoning": "Integration broke post-patch, docs do not reflect change.", "is_anomaly": false, "theme_assignments": ["integration and configuration issues"]},
        {"record_id": "c1r007", "sequence_number": 7,  "sentiment_label": "neutral",  "confidence_score": 0.71, "reasoning": "Config issue resolved but process was unclear.", "is_anomaly": false, "theme_assignments": ["integration and configuration issues"]},
        {"record_id": "c1r008", "sequence_number": 8,  "sentiment_label": "negative", "confidence_score": 0.86, "reasoning": "Multiple agents, no continuity in escalation.", "is_anomaly": false, "theme_assignments": ["escalation handling"]},
        {"record_id": "c1r009", "sequence_number": 9,  "sentiment_label": "positive", "confidence_score": 0.84, "reasoning": "Root cause identified and explained clearly.", "is_anomaly": false, "theme_assignments": ["resolution quality"]},
        {"record_id": "c1r010", "sequence_number": 10, "sentiment_label": "neutral",  "confidence_score": 0.67, "reasoning": "Volume spike acknowledged as context for delay.", "is_anomaly": false, "theme_assignments": ["holiday backlog impact"]},
        {"record_id": "c1r011", "sequence_number": 11, "sentiment_label": "negative", "confidence_score": 0.94, "reasoning": "SLA breach with no proactive communication.", "is_anomaly": true, "theme_assignments": ["SLA breach and response delays"]},
        {"record_id": "c1r012", "sequence_number": 12, "sentiment_label": "negative", "confidence_score": 0.83, "reasoning": "Webhook config issue linked to January patch.", "is_anomaly": false, "theme_assignments": ["integration and configuration issues"]}
    ]'::JSONB,
    '2026-02-03 14:00:00+00'
) ON CONFLICT (analysis_id) DO NOTHING;

-- ── OPS RUN 2: Support Tickets Feb 2026 ──────────────────────────────────────

INSERT INTO analysis_results (
    analysis_id, series_name, run_sequence, batch_label, domain_tag,
    record_count, sentiment_split, top_themes, executive_summary,
    anomaly_count, context_profile, prior_cycle_ref, per_record_results, created_at
)
VALUES (
    'c3000001-0000-0000-0000-000000000002',
    'Support Ticket Log', 2, 'Support Tickets Feb 2026', 'ops',
    12,
    '{"positive": 41.7, "neutral": 33.3, "negative": 25.0}'::JSONB,
    '[
        {"label": "SLA performance recovery",            "frequency": 4, "dominant_sentiment": "positive", "representative_quotes": ["Response within SLA for the first time in months.", "P1 handled in under 2 hours — exactly what we needed."]},
        {"label": "integration complexity",              "frequency": 4, "dominant_sentiment": "negative", "representative_quotes": ["Third-party integration requirements are underdocumented.", "Every integration engagement needs senior engineer involvement."]},
        {"label": "escalation process clarity",          "frequency": 3, "dominant_sentiment": "neutral",  "representative_quotes": ["Escalation path is clearer than January but still inconsistent.", "Knew who owned the ticket this time — improvement."]},
        {"label": "resolution quality",                  "frequency": 3, "dominant_sentiment": "positive", "representative_quotes": ["Engineer went beyond the fix and explained the underlying issue.", "Fast, accurate, and proactive about follow-up."]},
        {"label": "patch communication",                 "frequency": 2, "dominant_sentiment": "negative", "representative_quotes": ["February patch change log missed the API behaviour changes.", "Would have avoided the ticket entirely with better release notes."]}
    ]'::JSONB,
    'February 2026 support ticket analysis shows a clear improvement from the January post-holiday low: negative sentiment has declined from 42% to 25% and positive has risen to 42%, driven primarily by SLA recovery — the dominant pain point in January. Escalation process clarity has improved but remains inconsistent. Integration complexity has emerged as the new primary negative theme, replacing SLA as the critical concern; unlike SLA pressure which was situational, integration issues appear structural and are likely to persist without documentation and tooling investment.',
    1,
    '{"org_name": "Meridian SaaS", "industry": "B2B Software", "department": "Service Operations", "reporting_period": "February 2026", "situational_notes": "SLA recovery focus implemented. Extra engineer cover added. February patch released 3rd."}'::JSONB,
    'c3000001-0000-0000-0000-000000000001',
    '[
        {"record_id": "c2r001", "sequence_number": 1,  "sentiment_label": "positive", "confidence_score": 0.92, "reasoning": "SLA met on P1 — notable improvement.", "is_anomaly": false, "theme_assignments": ["SLA performance recovery"]},
        {"record_id": "c2r002", "sequence_number": 2,  "sentiment_label": "negative", "confidence_score": 0.89, "reasoning": "Integration docs still lacking for third-party setup.", "is_anomaly": false, "theme_assignments": ["integration complexity"]},
        {"record_id": "c2r003", "sequence_number": 3,  "sentiment_label": "neutral",  "confidence_score": 0.71, "reasoning": "Escalation ownership clearer, still inconsistent.", "is_anomaly": false, "theme_assignments": ["escalation process clarity"]},
        {"record_id": "c2r004", "sequence_number": 4,  "sentiment_label": "positive", "confidence_score": 0.90, "reasoning": "Response under 2 hours — SLA met with time to spare.", "is_anomaly": false, "theme_assignments": ["SLA performance recovery"]},
        {"record_id": "c2r005", "sequence_number": 5,  "sentiment_label": "negative", "confidence_score": 0.95, "reasoning": "Every integration ticket requires senior engineer — not scalable.", "is_anomaly": true, "theme_assignments": ["integration complexity"]},
        {"record_id": "c2r006", "sequence_number": 6,  "sentiment_label": "positive", "confidence_score": 0.88, "reasoning": "Engineer proactive about follow-up and root cause explanation.", "is_anomaly": false, "theme_assignments": ["resolution quality"]},
        {"record_id": "c2r007", "sequence_number": 7,  "sentiment_label": "neutral",  "confidence_score": 0.69, "reasoning": "Ownership assigned this time — improvement noted.", "is_anomaly": false, "theme_assignments": ["escalation process clarity"]},
        {"record_id": "c2r008", "sequence_number": 8,  "sentiment_label": "negative", "confidence_score": 0.86, "reasoning": "Patch change log incomplete — caused avoidable ticket.", "is_anomaly": false, "theme_assignments": ["patch communication"]},
        {"record_id": "c2r009", "sequence_number": 9,  "sentiment_label": "positive", "confidence_score": 0.91, "reasoning": "Quick, accurate resolution with post-fix summary.", "is_anomaly": false, "theme_assignments": ["resolution quality"]},
        {"record_id": "c2r010", "sequence_number": 10, "sentiment_label": "neutral",  "confidence_score": 0.67, "reasoning": "Escalation improved but process not yet fully consistent.", "is_anomaly": false, "theme_assignments": ["escalation process clarity"]},
        {"record_id": "c2r011", "sequence_number": 11, "sentiment_label": "positive", "confidence_score": 0.87, "reasoning": "SLA compliance restored — confidence returning.", "is_anomaly": false, "theme_assignments": ["SLA performance recovery"]},
        {"record_id": "c2r012", "sequence_number": 12, "sentiment_label": "negative", "confidence_score": 0.83, "reasoning": "API behaviour changes undocumented in release notes.", "is_anomaly": false, "theme_assignments": ["patch communication"]}
    ]'::JSONB,
    '2026-02-28 14:00:00+00'
) ON CONFLICT (analysis_id) DO NOTHING;


-- =============================================================================
-- BATCH_RECORDS
-- Populate the normalised per-record table from per_record_results JSONB.
-- In production this is done by the Python storage layer on pipeline write.
-- For seed data we expand inline so the history browser and export work
-- immediately without running the Python pipeline.
-- =============================================================================

INSERT INTO batch_records (
    record_id, analysis_id, sequence_number, text_body,
    sentiment_label, confidence_score, deviation_from_mean,
    is_anomaly, theme_assignments, record_timestamp, scored
)
SELECT
    uuid_generate_v5(ar.analysis_id, (rec->>'sequence_number')) AS record_id,
    ar.analysis_id,
    (rec->>'sequence_number')::INT   AS sequence_number,

    -- Representative text body matched to record_id (abbreviated for seed)
    CASE rec->>'record_id'
        -- CX Run 1
        WHEN 'a1r001' THEN 'The onboarding process was seamless and the team was incredibly helpful.'
        WHEN 'a1r002' THEN 'Billing error took 6 emails to fix. Very frustrated with support.'
        WHEN 'a1r003' THEN 'Product works as advertised but documentation could be clearer.'
        WHEN 'a1r004' THEN 'Had an issue last month but it was resolved quickly. Happy with the outcome.'
        WHEN 'a1r005' THEN 'My account was locked for no reason and no one could explain why. I am considering cancelling.'
        WHEN 'a1r006' THEN 'Excellent value for money. Would recommend to colleagues without hesitation.'
        WHEN 'a1r007' THEN 'Support ticket open for 10 days with no update. Not acceptable.'
        WHEN 'a1r008' THEN 'The new dashboard is a massive improvement. Much easier to navigate.'
        WHEN 'a1r009' THEN 'Had to figure out the API integration myself. Missing examples in the docs.'
        WHEN 'a1r010' THEN 'Signed up 3 months ago and have not had a single issue. Very impressed.'
        WHEN 'a1r011' THEN 'Slow ticket response is eroding my trust in the platform.'
        WHEN 'a1r012' THEN 'Feature request submitted and implemented within two weeks. Incredible.'
        WHEN 'a1r013' THEN 'Charged twice and no one responded for two weeks. Escalating to my card provider.'
        WHEN 'a1r014' THEN 'Overall the product meets our needs.'
        -- CX Run 2
        WHEN 'a2r001' THEN 'No major issues this quarter. The platform has been reliable.'
        WHEN 'a2r002' THEN 'New user setup is taking longer than it should for our team.'
        WHEN 'a2r003' THEN 'Response times have improved but are still inconsistent day to day.'
        WHEN 'a2r004' THEN 'Platform stability has been excellent — renewing without hesitation.'
        WHEN 'a2r005' THEN 'Three of my team members struggled with the initial configuration.'
        WHEN 'a2r006' THEN 'Invoice was wrong but fixed within 48 hours this time. Progress.'
        WHEN 'a2r007' THEN 'Docs still sparse for advanced API use cases.'
        WHEN 'a2r008' THEN 'Overall positive experience this quarter despite some minor friction.'
        WHEN 'a2r009' THEN 'Onboarding duration is too long for an enterprise rollout at our scale.'
        WHEN 'a2r010' THEN 'Support response improvements are clear — still room to go.'
        WHEN 'a2r011' THEN 'Three separate onboarding failures for new starters this month. Unacceptable for enterprise.'
        WHEN 'a2r012' THEN 'Renewed contract. Cites platform ROI explicitly.'
        WHEN 'a2r013' THEN 'Still seeing occasional billing discrepancies but not as severe.'
        WHEN 'a2r014' THEN 'API docs lacking for power users but the core product is excellent.'
        -- CX Run 3
        WHEN 'a3r001' THEN 'The new setup wizard fixed our onboarding issues completely.'
        WHEN 'a3r002' THEN 'Still no working examples for the webhooks endpoint. API docs are years behind.'
        WHEN 'a3r003' THEN 'Three quarters in and the uptime has been flawless.'
        WHEN 'a3r004' THEN 'Support team has been exceptional this quarter — response time and quality both excellent.'
        WHEN 'a3r005' THEN 'API has some limitations that are not well documented.'
        WHEN 'a3r006' THEN 'Best ROI of any tool in our stack. Will renew and expand seats.'
        WHEN 'a3r007' THEN 'API docs are materially blocking our integration work. This needs urgent attention.'
        WHEN 'a3r008' THEN 'Onboarding is now the smoothest part of the whole process. Complete turnaround.'
        WHEN 'a3r009' THEN 'Billing has been accurate every month for two quarters. No billing surprises at all.'
        WHEN 'a3r010' THEN 'Documentation needs to keep pace with the product.'
        WHEN 'a3r011' THEN 'Support quality improvement has been noticeable across the whole team.'
        WHEN 'a3r012' THEN 'Setup wizard helped enormously but some edge cases still need manual support.'
        WHEN 'a3r013' THEN 'Reliable billing and support make the renewal decision straightforward.'
        WHEN 'a3r014' THEN 'Developer productivity is severely impacted by missing webhook and API documentation.'
        WHEN 'a3r015' THEN 'Overall satisfaction is high. The API gap is the one thing holding back a full recommendation.'
        -- HR Run 1
        WHEN 'b1r001' THEN 'Three restructures in two years — nobody knows what their role is anymore.'
        WHEN 'b1r002' THEN 'The people I work with are what keeps me here. My team is great.'
        WHEN 'b1r003' THEN 'My manager is stretched too thin to support the team effectively.'
        WHEN 'b1r004' THEN 'Career paths exist on paper but not in practice.'
        WHEN 'b1r005' THEN 'I have not taken a full week off in 18 months. The workload is unsustainable.'
        WHEN 'b1r006' THEN 'Peer relationships are strong even though the wider org is uncertain.'
        WHEN 'b1r007' THEN 'My role changed in the last restructure and I still do not have clarity on scope.'
        WHEN 'b1r008' THEN 'The change is probably necessary but the impact on morale is real.'
        WHEN 'b1r009' THEN '1:1s get cancelled more often than they happen. I do not feel supported.'
        WHEN 'b1r010' THEN 'The work output quality from our team has been strong despite the conditions.'
        WHEN 'b1r011' THEN 'Headcount was reduced but workload did not change. This is not sustainable.'
        WHEN 'b1r012' THEN 'Not sure what I need to do to get promoted but I am not disengaged.'
        WHEN 'b1r013' THEN 'Manager is trying but they have too many direct reports.'
        -- HR Run 2
        WHEN 'b2r001' THEN 'My manager has really stepped up this half — more present and supportive.'
        WHEN 'b2r002' THEN 'I am performing well and being told so but nothing has moved on promotion.'
        WHEN 'b2r003' THEN '1:1s are happening and they are actually useful now. Real change from H1.'
        WHEN 'b2r004' THEN 'The reorg dust is settling but I am not fully confident in the direction yet.'
        WHEN 'b2r005' THEN 'Still no promotion framework published. Two years of this.'
        WHEN 'b2r006' THEN 'Team dynamics have genuinely improved since H1. We have clearer direction.'
        WHEN 'b2r007' THEN 'Workload is more balanced but still heavier than it should be long term.'
        WHEN 'b2r008' THEN 'The manager coaching programme results are showing in daily interactions.'
        WHEN 'b2r009' THEN 'Things feel more stable but I am not ready to call it resolved.'
        WHEN 'b2r010' THEN 'Team cohesion is the strongest it has been since I joined.'
        WHEN 'b2r011' THEN 'I am a top performer with no recognition pathway. I am starting to look externally.'
        WHEN 'b2r012' THEN 'Better than H1 but still above what I would call sustainable workload.'
        WHEN 'b2r013' THEN 'On a positive trajectory overall even with the career visibility issue.'
        -- HR Run 3
        WHEN 'b3r001' THEN 'The new career framework was exactly what we needed. First time I can see a clear path.'
        WHEN 'b3r002' THEN 'My manager is the best support I have had in this company. Consistent and development-focused.'
        WHEN 'b3r003' THEN 'Pay has not kept pace with inflation or the growth in my responsibilities.'
        WHEN 'b3r004' THEN 'For the first time in two years I can see exactly what I need to do to progress.'
        WHEN 'b3r005' THEN 'Culture feels like it is actually improving, not just in the comms.'
        WHEN 'b3r006' THEN 'Workload is manageable but fragile. One departure and we would be in trouble.'
        WHEN 'b3r007' THEN 'Consistent 1:1s with real development focus. Big change from H1 2025.'
        WHEN 'b3r008' THEN 'The team is firing on all cylinders right now.'
        WHEN 'b3r009' THEN 'Headcount is still not back to pre-reorg levels. One departure breaks us.'
        WHEN 'b3r010' THEN 'Best manager I have had in my time at this company.'
        WHEN 'b3r011' THEN 'Career framework is positive but the implementation pace could be faster.'
        WHEN 'b3r012' THEN 'Compensation review is overdue. Pay has not kept up.'
        -- Ops Run 1
        WHEN 'c1r001' THEN 'P1 ticket open for 36 hours with no engineer assigned. SLA was 4 hours.'
        WHEN 'c1r002' THEN 'Issue resolved correctly first time. Engineer found root cause quickly.'
        WHEN 'c1r003' THEN 'Escalated twice but no ownership was ever assigned. Different agent each time.'
        WHEN 'c1r004' THEN 'Understand the holiday period caused delays but communication was lacking.'
        WHEN 'c1r005' THEN 'SLA was 4 hours. It took 3 days. No explanation, no escalation path.'
        WHEN 'c1r006' THEN 'Webhook integration broke after the January patch. Docs do not match system behaviour.'
        WHEN 'c1r007' THEN 'Configuration issue was resolved but the process for getting there was unclear.'
        WHEN 'c1r008' THEN 'Escalation process unclear — different agent every time I contact.'
        WHEN 'c1r009' THEN 'Root cause was identified and explained clearly. Appreciated the thoroughness.'
        WHEN 'c1r010' THEN 'Volume spike expected over the holiday period but some communication would have helped.'
        WHEN 'c1r011' THEN 'SLA breached with no proactive communication. Had to chase every update.'
        WHEN 'c1r012' THEN 'Webhook config issue directly linked to the January patch. No changelog entry.'
        -- Ops Run 2
        WHEN 'c2r001' THEN 'Response within SLA for the first time in months. This is what we needed.'
        WHEN 'c2r002' THEN 'Third-party integration requirements are completely underdocumented.'
        WHEN 'c2r003' THEN 'Escalation path is clearer than January but still not fully consistent.'
        WHEN 'c2r004' THEN 'P1 handled in under 2 hours. Exactly the kind of response we pay for.'
        WHEN 'c2r005' THEN 'Every integration ticket requires senior engineer involvement. This will not scale.'
        WHEN 'c2r006' THEN 'Engineer went beyond the fix and explained the underlying issue. Proactive follow-up.'
        WHEN 'c2r007' THEN 'Knew who owned the ticket this time. Real improvement from January.'
        WHEN 'c2r008' THEN 'February patch change log missed the API behaviour changes. Caused an avoidable ticket.'
        WHEN 'c2r009' THEN 'Fast, accurate resolution with a post-fix summary. Exactly right.'
        WHEN 'c2r010' THEN 'Escalation process improved but not yet fully consistent across the team.'
        WHEN 'c2r011' THEN 'SLA compliance restored. Confidence in the ops team is returning.'
        WHEN 'c2r012' THEN 'API behaviour changes were not in the release notes. Would have avoided the ticket entirely.'
        ELSE '[Demo record — text body not expanded for this record_id]'
    END                              AS text_body,

    (rec->>'sentiment_label')::TEXT  AS sentiment_label,
    (rec->>'confidence_score')::NUMERIC(4,3) AS confidence_score,
    NULL                             AS deviation_from_mean,  -- populated by anomaly detection in app
    COALESCE((rec->>'is_anomaly')::BOOLEAN, FALSE) AS is_anomaly,
    (rec->'theme_assignments')::JSONB AS theme_assignments,
    -- record_timestamp: only CX run 3 has timestamps in seed data
    CASE WHEN rec->>'record_timestamp' IS NOT NULL
         THEN (rec->>'record_timestamp')::TIMESTAMPTZ
         ELSE NULL
    END                              AS record_timestamp,
    TRUE                             AS scored

FROM analysis_results ar,
     JSONB_ARRAY_ELEMENTS(ar.per_record_results) AS rec

ON CONFLICT (record_id) DO NOTHING;


-- =============================================================================
-- CONTEXT PROFILES
-- One row per run that has a context profile (all 8 seed runs do).
-- =============================================================================

INSERT INTO context_profiles (analysis_id, org_name, industry, department, reporting_period, situational_notes)
SELECT
    ar.analysis_id,
    ar.context_profile->>'org_name',
    ar.context_profile->>'industry',
    ar.context_profile->>'department',
    ar.context_profile->>'reporting_period',
    ar.context_profile->>'situational_notes'
FROM analysis_results ar
WHERE ar.context_profile IS NOT NULL
ON CONFLICT (analysis_id) DO NOTHING;


-- =============================================================================
-- PIPELINE RUN LOG
-- One SUCCESS entry per seed run.
-- Approximate api_call_count: record_count + 2 (theme + summary calls)
-- =============================================================================

INSERT INTO pipeline_run_log (
    analysis_id, triggered_at, status,
    records_submitted, records_scored, records_failed,
    api_call_count, duration_seconds, error_detail
)
SELECT
    ar.analysis_id,
    ar.created_at - INTERVAL '4 minutes',
    'SUCCESS',
    ar.record_count,
    ar.record_count,       -- all records scored in demo runs
    0,
    ar.record_count + 2,   -- per-record calls + theme call + summary call
    ROUND((RANDOM() * 60 + ar.record_count * 1.8)::NUMERIC, 1),
    NULL
FROM analysis_results ar
ON CONFLICT DO NOTHING;


COMMIT;

-- =============================================================================
-- VERIFICATION QUERIES
-- Run these after seeding to confirm the data loaded correctly.
-- =============================================================================

-- Series run counts
-- SELECT series_name, domain_tag, run_count FROM series_index ORDER BY domain_tag;

-- Sentiment trajectory per series
-- SELECT series_name, run_sequence, batch_label,
--        sentiment_split->>'positive' AS pos_pct,
--        sentiment_split->>'negative' AS neg_pct
-- FROM analysis_results ORDER BY series_name, run_sequence;

-- Total records per run
-- SELECT ar.batch_label, COUNT(br.record_id) AS record_count, SUM(br.is_anomaly::INT) AS anomalies
-- FROM analysis_results ar
-- JOIN batch_records br ON br.analysis_id = ar.analysis_id
-- GROUP BY ar.batch_label ORDER BY ar.created_at;

-- Prior cycle chain (longitudinal links)
-- SELECT a.batch_label AS current_run, p.batch_label AS prior_run
-- FROM analysis_results a LEFT JOIN analysis_results p ON p.analysis_id = a.prior_cycle_ref
-- ORDER BY a.series_name, a.run_sequence;
