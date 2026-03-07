# Lens - Sentiment & Text Analytics Tool

**Portfolio Project S4 | Hadi Mercer | BA Portfolio 2026**

A Streamlit-based sentiment and text analytics application that accepts uploaded text batches, validates them, enriches them with business context, runs an OpenAI-backed analysis pipeline, stores results in PostgreSQL, and reopens historical runs through a reviewer-friendly analysis library.

> Lens is built as a realistic fictional portfolio product. The seeded organisations, batch labels, and text records are synthetic and exist to demonstrate business analysis, pipeline design, and analytical UX patterns.

---

## Live Demo

> **Deployment in progress** - the Streamlit Community Cloud deployment is now configured and can be linked here once you are ready to publish the public URL.

**Runtime modes:**
- **Demo Mode** - seeded historical analyses load from PostgreSQL and live OpenAI execution is disabled.
- **Live Mode** - upload, validation, and full pipeline execution are enabled when `OPENAI_API_KEY` is configured.

---

## Screenshots

Screenshots will be added after the deployment smoke test. Recommended capture set:

| Screen | Purpose |
|---|---|
| Overview | Reviewer landing page and workflow orientation |
| New Analysis | Batch validation, metadata, and run controls |
| Analysis Library | Historical result reload and CSV export |
| Sentiment Dashboard | Summary KPIs, sentiment mix, themes, anomalies |
| Longitudinal Context | Prior-cycle comparison and series context |

---

## What This Project Demonstrates

| Capability | Evidence |
|---|---|
| Business analysis to working product | FRD, DFD, ERD, UCD, schema, seed data, and deployed Streamlit application |
| LLM workflow design | Prompted sentiment scoring, theme extraction, executive summary generation, retry handling |
| Data validation and ingestion | UTF-8 CSV parsing, text-column detection, timestamp detection, preview gating, batch limits |
| PostgreSQL data design | Five-table schema with FK chains, helper functions, indexes, and idempotent bootstrap logic |
| Longitudinal analysis design | Named series, prior-cycle retrieval, run sequencing, historical comparison context |
| Auditability and resilience | Pipeline run log, partial-run handling, pending-save retry path, demo seed bootstrap |
| Analyst-facing UX | Streamlit command-surface UI with SOP guidance, historical review flow, and CSV export |
| Deployment readiness | `.env` configuration, Streamlit Cloud secrets support, demo/live mode split, automated seed behavior |

---

## The Business Problem

Teams often collect large volumes of qualitative text - customer comments, engagement survey responses, support notes, incident narratives - but the analysis workflow usually breaks down in one of three places: the incoming text is messy, the interpretation lacks business context, or the results are not stored in a way that supports historical comparison. Lens addresses that gap by treating text analysis as an operational workflow rather than a one-off prompt. Analysts can validate a batch, attach business context, compare against prior cycles, persist the run, and reopen it later without re-calling the model.

---

## Technology Decision

Lens follows the same portfolio stack pattern as the rest of the BA portfolio: Python, Streamlit, PostgreSQL on Supabase, and OpenAI for language analysis.

A few decisions matter for the implementation:

- **Streamlit over BI tooling**: the app needs both workflow controls and analytical outputs, not just charts.
- **Supabase PostgreSQL as system of record**: analysis runs, normalized record rows, context profiles, and pipeline logs all need to be queryable and durable.
- **Demo Mode as a first-class path**: the app remains reviewable even without an API key because seed data is visible on first deploy.
- **Short-lived psycopg2 connections**: Supabase free tier drops idle sessions, so the app opens per-request connections instead of holding a long-lived import-time connection.

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
  - Batch label + domain tag
  - Optional context profile
  - Optional series name
  - Prior-cycle lookup
  - API footprint warning and confirmation
        |
        v
lens/pipeline/runner.py
  - Record-level sentiment scoring
  - Retry on malformed model output
  - Theme extraction
  - Executive summary generation
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
```

---

## Repository Structure

```text
lens_sentiment_engine/
|- docs/
|  `- artifacts/
|     |- Lens_FRD_001.docx
|     |- lens_dfd.html
|     |- lens_erd.html
|     |- lens_schema.sql
|     |- lens_seed.sql
|     `- lens_ucd.html
|- lens/
|  |- app.py                      # Streamlit entrypoint and page routing
|  |- config.py                   # Runtime settings, thresholds, mode detection
|  |- db.py                       # Short-lived psycopg2 connection factory
|  |- ingestion/
|  |  |- models.py                # ValidatedBatch and preview models
|  |  `- service.py               # CSV/text validation and BatchInput builders
|  |- pipeline/
|  |  |- api_client.py            # OpenAI provider wrapper and retry logic
|  |  |- anomaly.py               # Batch anomaly detection
|  |  |- models.py                # Core analysis domain models
|  |  |- prompts.py               # Prompt templates
|  |  `- runner.py                # End-to-end pipeline orchestration
|  |- storage/
|  |  |- models.py                # StoredAnalysis, history filters, records
|  |  `- service.py               # Bootstrap, history queries, persistence, export
|  |- ui/
|  |  |- dashboard.py             # Shared dashboard renderer
|  |  |- runtime.py               # IncidentOps-style shell and layout helpers
|  |  |- state.py                 # Session-state initialization and guards
|  |  `- panels/                  # Sentiment, themes, timeline, anomalies, series
|  `- views/
|     |- overview.py              # Overview page render
|     |- new_analysis.py          # New Analysis page render
|     `- analysis_library.py      # Analysis Library page render
|- tests/
|  |- test_ingestion.py
|  |- test_pipeline.py
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
This is the operational workbench. Analysts upload a CSV or paste raw text, validate the batch, inspect a five-row preview, confirm the detected columns, then add batch metadata and optional business context. If a series name is supplied, Lens retrieves the most recent prior cycle and injects that context into the run. Live execution is disabled automatically when `OPENAI_API_KEY` is absent.

**Analysis Library**  
This is the historical evidence workspace. Analysts filter stored runs by series, domain, or date, reopen a completed analysis without calling the model again, inspect the full dashboard, and export a normalized CSV with record-level sentiment results.

**Dashboard Panels**  
The shared dashboard renderer presents the output as one integrated analysis surface: sentiment distribution, dominant themes, anomaly flags, optional sentiment-over-time view when timestamps exist, and prior-cycle context when the run belongs to a longitudinal series.

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
LENS_CREATED_BY=Hadi Mercer
```

Notes:
- Use the **Supabase session pooler** connection string for deployment.
- URL-encode special characters in the password section only.
- If `OPENAI_API_KEY` is omitted, the app runs in Demo Mode.

### 4. Run locally

```powershell
streamlit run lens/app.py
```

Expected behavior:
- Database bootstrap applies the schema and loads demo seed data when the target database is empty.
- Demo Mode is active when `OPENAI_API_KEY` is missing.
- Live Mode is active when `OPENAI_API_KEY` is present.

### 5. Deploy to Streamlit Community Cloud

1. Push the repository to GitHub.
2. Create a new Streamlit app pointing to `lens/app.py` on branch `main`.
3. Select **Python 3.12**.
4. Add secrets:

```toml
DATABASE_URL="postgresql://postgres.your-project-ref:your-url-encoded-password@aws-1-us-east-1.pooler.supabase.com:5432/postgres"
OPENAI_API_KEY="sk-..."
LENS_CREATED_BY="Hadi Mercer"
```

5. Reboot the app after saving secrets.

---

## Portfolio Artifacts

| Artifact | File | Traces To |
|---|---|---|
| Functional Requirements Document | `docs/artifacts/Lens_FRD_001.docx` | Full Lens v1 scope |
| Data Flow Diagram | `docs/artifacts/lens_dfd.html` | End-to-end batch and storage flow |
| Entity Relationship Diagram | `docs/artifacts/lens_erd.html` | PostgreSQL schema and table relationships |
| Use Case Diagram | `docs/artifacts/lens_ucd.html` | Analyst workflows and system boundaries |
| PostgreSQL Schema | `docs/artifacts/lens_schema.sql` | Persistence model, indexes, helper functions |
| Seed Dataset | `docs/artifacts/lens_seed.sql` | Demo mode, first-deploy historical analyses |

---

## Functional Coverage Snapshot

| Requirement Area | Coverage | Status |
|---|---|---|
| FR-01 | Batch sentiment analysis, summary output, dashboard rendering, timestamp-aware trend view | Implemented |
| FR-02 | Validation controls, optional context profile, retry handling, anomaly detection, live execution workflow | Implemented |
| FR-03 | Series registry, autocomplete, prior-cycle retrieval, run sequencing, longitudinal comparison context | Implemented |
| FR-04 | History browser, stored analysis reload, CSV export, pending-save retry path, demo seed bootstrap | Implemented |

Additional implemented constraints visible in the shipped schema and app logic include:
- optional context fields with app and database limits
- retained placeholder records when API retries are exhausted
- idempotent schema and seed bootstrap behavior
- public demo-safe mode split between seeded review and live execution

---

## Test Coverage

The current project includes automated tests for:

- ingestion validation behavior
- pipeline retry and result assembly behavior
- storage bootstrap and run sequencing behavior

Run locally with:

```powershell
python -m unittest discover -s tests -v
```

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
