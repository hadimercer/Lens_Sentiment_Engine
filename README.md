# Lens - Sentiment & Text Analytics Tool

**Portfolio Project S4 | Hadi Mercer | BA Portfolio 2026**

A Streamlit-based qualitative analytics application that accepts uploaded text batches, validates them, enriches them with business context, runs an OpenAI-backed sentiment and theme analysis pipeline, stores results in PostgreSQL, and reopens historical runs through a reviewer-friendly analysis library.

> Lens is built as a realistic fictional portfolio product. The seeded organisations, batch labels, and text records are synthetic and exist to demonstrate business analysis, data design, LLM workflow orchestration, and analytical UX patterns.

---

## Live Demo

> **Deployment in progress** - the Streamlit Community Cloud deployment is configured and ready for the public URL to be linked here.

**Runtime modes:**
- **Demo Mode** - seeded historical analyses load from PostgreSQL and live OpenAI execution is disabled.
- **Live Mode** - upload, validation, and full pipeline execution are enabled when `OPENAI_API_KEY` is configured.

**Runtime governance:**
- public users can browse `Overview` and `Analysis Library`
- live runs are gated behind an admin password on `New Analysis`
- model selection is available only to an unlocked admin session

---

## Screenshots

Screenshots will be added after the final smoke test and public deployment publish.

| Screen | Purpose |
|---|---|
| Overview | Reviewer landing page, workflow explanation, runtime status |
| New Analysis | Batch upload, validation preview, admin unlock, run controls |
| Analysis Library | Historical analysis reload, CSV export, admin cleanup |
| Executive Summary Surface | Narrative summary, takeaways, priority actions |
| Dashboard Panels | Sentiment split, sentiment distribution, theme heatmap, theme table |
| Longitudinal Comparison | Prior-cycle context and series run progression |

---

## What This Project Demonstrates

| Capability | Evidence |
|---|---|
| End-to-end business analysis to working product | FRD, DFD, ERD, UCD, schema, seed data, working Streamlit app |
| LLM workflow design | Prompted sentiment scoring, theme extraction, structured summary generation, retry handling |
| Data validation and ingestion | UTF-8 CSV parsing, text-column detection, timestamp detection, preview gating, batch thresholds |
| PostgreSQL data design | Five-table schema, helper functions, FK chains, indexes, idempotent bootstrap, runtime migration handling |
| Longitudinal analysis design | Named series, prior-cycle retrieval, run sequencing, historical comparison context |
| Governance for public AI demos | Demo/live mode split, admin password gate, model allowlist, safe public browsing |
| Analyst-facing UX | IncidentOps-style command surface, SOP guidance, historical review flow, CSV export |
| Deployment readiness | `.env` support, Streamlit Cloud secrets support, Supabase pooler use, seeded first-launch behavior |

---

## The Business Problem

Teams often collect large volumes of qualitative text - customer comments, engagement survey responses, support notes, incident narratives, implementation feedback - but the analysis workflow usually breaks down in one of three places: the incoming text is messy, the interpretation lacks business context, or the results are not stored in a way that supports historical comparison. Lens addresses that gap by treating text analysis as an operational workflow rather than a one-off prompt. Analysts can validate a batch, attach business context, compare it against prior cycles, persist the run, and reopen it later without re-calling the model.

The second design problem Lens addresses is governance. A public Streamlit app that can call a paid API needs controls. Lens separates public review access from live execution through runtime mode detection, admin gating, and explicit model selection controls.

---

## Technology Decision

Lens follows the same portfolio stack pattern as the rest of the BA portfolio: Python, Streamlit, PostgreSQL on Supabase, and OpenAI for language analysis.

A few implementation decisions matter:

- **Streamlit over BI tooling**: the app needs both workflow controls and analytical outputs, not just charts.
- **Supabase PostgreSQL as system of record**: analysis runs, normalized record rows, context profiles, and pipeline logs all need to be queryable and durable.
- **Demo Mode as a first-class path**: the app remains reviewable even without an API key because seed data is visible on first deploy.
- **Short-lived psycopg2 connections**: Supabase free tier drops idle sessions, so the app opens per-request connections instead of holding a long-lived import-time connection.
- **Session pooler for deployment**: Streamlit Cloud should use the Supabase pooler connection string rather than a direct connection.
- **Runtime model governance**: the active OpenAI model comes from config instead of being hardcoded, with a small allowlist for controlled testing.

---

## Architecture

```text
Source text input
  - Upload CSV
  - Paste one record per line
        |
        v
lens/ingestion/service.py
  - UTF-8 validation
  - Text-column detection
  - Optional timestamp detection
  - Empty-row rejection
  - 5-row preview generation
  - Batch size enforcement
        |
        v
lens/views/new_analysis.py
  - Preview confirmation gate
  - Admin live-run unlock
  - Batch label + domain tag
  - Optional context profile
  - Optional series name
  - Prior-cycle lookup
  - Model selection for unlocked admin session
  - API footprint warning and confirmation
        |
        v
lens/pipeline/runner.py
  - Record-level sentiment scoring
  - Retry on malformed model output
  - Theme extraction
  - Structured summary generation
  - Key takeaways + priority actions
  - Anomaly detection
        |
        v
lens/storage/service.py
  - Upsert series registry
  - Assign run_sequence
  - Persist analysis_results
  - Persist normalized batch_records
  - Persist context_profiles
  - Persist pipeline_run_log
  - Runtime schema migration guard
  - Retry save without rerunning model
        |
        v
PostgreSQL / Supabase
  - series_index
  - analysis_results
  - batch_records
  - context_profiles
  - pipeline_run_log
        |
        v
Streamlit UI
  - Overview
  - New Analysis
  - Analysis Library
  - Stored dashboard reload
  - CSV export
  - Admin cleanup for duplicate/mistaken runs
```

---

## Repository Structure

```text
lens_sentiment_engine/
|- docs/
|  |- artifacts/
|  |  |- Lens_FRD_001.docx
|  |  |- lens_dfd.html
|  |  |- lens_erd.html
|  |  |- lens_schema.sql
|  |  |- lens_seed.sql
|  |  `- lens_ucd.html
|  `- test_data/
|     |- lens_live_test_batch_small.csv
|     |- lens_live_test_batch_medium_70.csv
|     |- lens_live_test_batch_large_180.csv
|     `- lens_live_test_batch_large_negative_180.csv
|- lens/
|  |- app.py                      # Streamlit entrypoint and routing
|  |- config.py                   # Runtime settings, thresholds, mode detection, admin controls
|  |- db.py                       # Short-lived psycopg2 connection factory
|  |- ingestion/
|  |  |- models.py                # ValidatedBatch and preview models
|  |  `- service.py               # CSV/text validation and BatchInput builders
|  |- pipeline/
|  |  |- api_client.py            # OpenAI provider wrapper, retry logic, structured parsing
|  |  |- anomaly.py               # Batch anomaly detection
|  |  |- models.py                # Core analysis domain models
|  |  |- prompts.py               # Prompt templates for sentiment, themes, summary
|  |  `- runner.py                # End-to-end pipeline orchestration
|  |- storage/
|  |  |- models.py                # StoredAnalysis, history filters, records
|  |  `- service.py               # Bootstrap, migration guard, history queries, persistence, export
|  |- ui/
|  |  |- dashboard.py             # Shared analysis dashboard renderer
|  |  |- runtime.py               # Shared shell, theme, page framing
|  |  |- state.py                 # Session-state initialization and guards
|  |  `- panels/                  # Sentiment, themes, timeline, anomalies, series panels
|  `- views/
|     |- overview.py              # Overview page render
|     |- new_analysis.py          # New Analysis page render
|     `- analysis_library.py      # Analysis Library page render
|- tests/
|  |- test_config.py
|  |- test_ingestion.py
|  |- test_pipeline.py
|  |- test_state.py
|  `- test_storage.py
|- .streamlit/
|  `- config.toml
|- requirements.txt
`- README.md
```

---

## Page Descriptions

**Overview**  
The landing page is the reviewer briefing surface. It explains what Lens is, what each workspace does, which runtime mode the app is in, and where to start depending on whether the audience wants to see finished evidence first or the operational workflow first.

**New Analysis**  
This is the operational workbench. Analysts upload a CSV or paste raw text, validate the batch, inspect a five-row preview, confirm the detected columns, then add batch metadata and optional business context. If a series name is supplied, Lens retrieves the most recent prior cycle and injects that context into the run. In Live Mode, public execution remains locked until the admin password is entered.

**Analysis Library**  
This is the historical evidence workspace. Analysts filter stored runs by series, domain, or date, reopen a completed analysis without calling the model again, inspect the full dashboard, export a normalized CSV, and optionally perform admin cleanup for mistaken or duplicate runs through a collapsed destructive-action section.

**Dashboard Surface**  
The shared dashboard renderer presents the output as one integrated analysis surface: executive summary, ordered takeaways, priority actions, sentiment split, sentiment distribution, dominant themes, anomaly flags, optional sentiment-over-time view when timestamps exist, and prior-cycle context when the run belongs to a longitudinal series.

---

## Setup Instructions

### Prerequisites

- Python 3.12 recommended
- A Supabase PostgreSQL database
- An OpenAI API key for Live Mode
- Git

### 1. Clone the repository

```powershell
git clone https://github.com/hadimercer/Lens_Sentiment_Engine.git
cd Lens_Sentiment_Engine
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy `.env.example` to `.env` and set:

```env
DATABASE_URL=postgresql://postgres.your-project-ref:your-url-encoded-password@aws-1-us-east-1.pooler.supabase.com:5432/postgres
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
LENS_ADMIN_PASSWORD=your-shared-passphrase
LENS_CREATED_BY=Hadi Mercer
```

Notes:
- use the **Supabase session pooler** connection string for deployment
- URL-encode special characters in the password section only
- if `OPENAI_API_KEY` is omitted, the app runs in Demo Mode
- if `LENS_ADMIN_PASSWORD` is omitted, Live Mode stays open by design, which is acceptable only for local testing

### 4. Run locally

```powershell
streamlit run lens/app.py
```

Expected behavior:
- database bootstrap applies the schema and loads demo seed data when the target database is empty
- Demo Mode is active when `OPENAI_API_KEY` is missing
- Live Mode is active when `OPENAI_API_KEY` is present
- live execution requires admin unlock when `LENS_ADMIN_PASSWORD` is configured

### 5. Deploy to Streamlit Community Cloud

1. Push the repository to GitHub.
2. Create a new Streamlit app pointing to `lens/app.py` on branch `main`.
3. Select **Python 3.12**.
4. Add secrets:

```toml
DATABASE_URL="postgresql://postgres.your-project-ref:your-url-encoded-password@aws-1-us-east-1.pooler.supabase.com:5432/postgres"
OPENAI_API_KEY="sk-..."
OPENAI_MODEL="gpt-4o-mini"
LENS_ADMIN_PASSWORD="your-shared-passphrase"
LENS_CREATED_BY="Hadi Mercer"
```

5. Save secrets and reboot the app.

---

## Portfolio Artifacts

| Artifact | File | Traces To |
|---|---|---|
| Functional Requirements Document | `docs/artifacts/Lens_FRD_001.docx` | Full Lens v1 scope |
| Data Flow Diagram | `docs/artifacts/lens_dfd.html` | End-to-end batch and storage flow |
| Entity Relationship Diagram | `docs/artifacts/lens_erd.html` | PostgreSQL schema and table relationships |
| Use Case Diagram | `docs/artifacts/lens_ucd.html` | Analyst workflows and system boundaries |
| PostgreSQL Schema | `docs/artifacts/lens_schema.sql` | Persistence model, indexes, helper functions, migration baseline |
| Seed Dataset | `docs/artifacts/lens_seed.sql` | Demo mode, first-deploy historical analyses |
| Live Test Data | `docs/test_data/` | Smoke tests for small, medium, and negative-skew large runs |

---

## Functional Coverage Snapshot

| Requirement Area | Coverage | Status |
|---|---|---|
| FR-01 | Batch sentiment analysis, structured summary output, dashboard rendering, timestamp-aware trend view | Implemented |
| FR-02 | Validation controls, optional context profile, retry handling, anomaly detection, live execution workflow | Implemented |
| FR-03 | Series registry, autocomplete, prior-cycle retrieval, run sequencing, longitudinal comparison context | Implemented |
| FR-04 | History browser, stored analysis reload, CSV export, pending-save retry path, admin cleanup, demo seed bootstrap | Implemented |

Additional implemented controls visible in the shipped app include:
- admin-only live-run gating for public deployment
- configurable default model via `OPENAI_MODEL`
- admin-only model override for testing
- runtime migration handling for existing databases
- BOM-safe SQL artifact loading for bootstrap reliability

---

## Test Coverage

The current project includes automated tests for:

- configuration and runtime defaults
- ingestion validation behavior
- pipeline retry, summary parsing, and result assembly behavior
- session-state initialization and admin gating behavior
- storage bootstrap, migration guard, delete flow, and run sequencing behavior

Run locally with:

```powershell
python -m unittest discover -s tests -v
```

---

## Live Test Assets

The repository includes synthetic test batches for staged live validation:

| File | Size | Intended Use |
|---|---|---|
| `docs/test_data/lens_live_test_batch_small.csv` | 8 rows | First live sanity check |
| `docs/test_data/lens_live_test_batch_medium_70.csv` | 70 rows | Medium longitudinal run |
| `docs/test_data/lens_live_test_batch_large_180.csv` | 180 rows | Balanced larger-volume test |
| `docs/test_data/lens_live_test_batch_large_negative_180.csv` | 180 rows | Negative-skew directional sensitivity test |

---

## Portfolio Context

Lens is **Small Project 4 (S4)** in the BA portfolio and focuses on AI-assisted qualitative analysis.

| # | Project | Focus |
|---|---|---|
| S1 | Cadence - HR Process Automation Hub | Workflow automation and rules engines |
| S2 | TechNova - Compensation & Market Benchmarking Dashboard | Market intelligence and compensation analytics |
| S3 | Meridian - Portfolio Health Dashboard | Portfolio visibility and RAG reporting |
| **S4** | **Lens - Sentiment & Text Analytics Tool** | **LLM-assisted text analysis and longitudinal sentiment review** |
| F1 | Operational Process Intelligence Platform | Planned flagship |
| F2 | Business Analysis Co-Pilot | Planned flagship |

Lens complements the rest of the portfolio by showing how qualitative text can be turned into structured analytical evidence, then stored and revisited as part of a repeatable business workflow rather than a one-off prompt experiment.

---

## Contact

**Hadi Mercer**  
LinkedIn: [linkedin.com/in/hadimercer](https://linkedin.com/in/hadimercer)  
GitHub: [github.com/hadimercer](https://github.com/hadimercer)
