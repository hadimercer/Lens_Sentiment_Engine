# lens/pipeline/test_pipeline.py
#
# Manual test harness for the pipeline scaffold.
# Runs a small synthetic batch through the full pipeline.
# Set OPENAI_API_KEY in your environment to test with real API calls.
# If no key is set, the script validates imports and model construction only.
#
# Usage:
#   export OPENAI_API_KEY=sk-...
#   python -m lens.pipeline.test_pipeline

import os
import logging
import json

logging.basicConfig(level=logging.INFO, format="%(levelname)s — %(message)s")

from lens.pipeline import run_pipeline
from lens.pipeline.models import BatchInput, ContextProfile, PriorCycleContext


# ── SYNTHETIC TEST DATA ───────────────────────────────────────────────────────

SYNTHETIC_CX_RECORDS = [
    "The onboarding process was seamless and the team was incredibly helpful.",
    "Waited 3 weeks for a response. Completely unacceptable for a paying customer.",
    "Product works as advertised but documentation could be clearer.",
    "Had an issue last month but it was resolved quickly. Happy with the outcome.",
    "Billing error took 6 emails to fix. Very frustrated with support.",
    "The new dashboard is a massive improvement. Much easier to navigate.",
    "My account was locked for no reason and no one could explain why.",
    "Excellent value for money. Would recommend to colleagues.",
    "The API integration was painful — missing examples in the docs.",
    "Signed up 3 months ago and haven't had a single issue. Very impressed.",
    "Customer service rep was rude and unhelpful. I'll be cancelling soon.",
    "Feature request submitted, implemented within two weeks. Incredible responsiveness.",
]

SYNTHETIC_CONTEXT = ContextProfile(
    org_name="Meridian SaaS",
    industry="B2B Software",
    department="Customer Experience",
    reporting_period="Q1 2026",
    situational_notes="Post-migration feedback following the January platform upgrade.",
)

SYNTHETIC_PRIOR_CYCLE = PriorCycleContext(
    batch_label="NPS Q4 2025",
    run_sequence=3,
    sentiment_split={"positive": 54.0, "neutral": 28.0, "negative": 18.0},
    top_themes=["onboarding friction", "billing issues", "API documentation gaps"],
    executive_summary=(
        "Q4 2025 feedback reflected cautious optimism following the product roadmap announcement, "
        "with billing complaints remaining the dominant negative theme and onboarding satisfaction improving."
    ),
)


def progress_handler(stage: str, processed: int, total: int):
    pct = int(processed / total * 100) if total > 0 else 0
    print(f"  [{pct:3d}%] {stage} ({processed}/{total})")


def main():
    api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        print("\n⚠  OPENAI_API_KEY not set — validating model construction only (no API calls).\n")
        _validate_models()
        return

    print("\n🚀 Running Lens pipeline scaffold test\n")
    print(f"  Batch:    {len(SYNTHETIC_CX_RECORDS)} records")
    print(f"  Context:  {SYNTHETIC_CONTEXT.org_name} / {SYNTHETIC_CONTEXT.department}")
    print(f"  Series:   Q-Series (with prior cycle injection)")
    print()

    batch = BatchInput(
        batch_label="NPS Q1 2026",
        domain_tag="cx",
        records=SYNTHETIC_CX_RECORDS,
        timestamps=None,            # No timestamps in this test batch
        context=SYNTHETIC_CONTEXT,
        series_name="Meridian CX Q-Series",
        prior_cycle=SYNTHETIC_PRIOR_CYCLE,
    )

    result = run_pipeline(
        batch=batch,
        api_key=api_key,
        progress_callback=progress_handler,
    )

    # ── Print results ─────────────────────────────────────────────────────────
    print("\n" + "═" * 60)
    print("PIPELINE RESULT")
    print("═" * 60)

    print(f"\nAnalysis ID:    {result.analysis_id}")
    print(f"Duration:       {result.duration_seconds}s")
    print(f"API calls:      {result.api_call_count}")
    print(f"Scored:         {result.records_scored}/{result.record_count}")
    print(f"Failed:         {result.records_failed}")

    print(f"\nSentiment Split:")
    for label, pct in result.sentiment_split.items():
        print(f"  {label:10s} {pct:.1f}%")

    print(f"\nThemes ({len(result.themes)}):")
    for t in result.themes:
        print(f"  [{t.dominant_sentiment:8s}] {t.label} (×{t.frequency})")

    print(f"\nExecutive Summary:\n  {result.executive_summary}")

    print(f"\nAnomalies ({result.anomaly_count}):")
    for a in result.anomaly_flags:
        print(f"  [{a.anomaly_type}] {a.description[:80]}...")

    print(f"\nDB dict (analysis_results row):")
    db = result.to_db_dict()
    # Show a preview of the JSONB fields
    print(f"  sentiment_split:    {db['sentiment_split']}")
    print(f"  themes count:       {len(db['top_themes'])}")
    print(f"  per_record count:   {len(db['per_record_results'])}")
    print(f"  context_profile:    {db['context_profile']}")

    print("\n✅ Pipeline test complete\n")


def _validate_models():
    """Validate that all imports and model construction work without an API key."""
    from lens.pipeline.models import BatchInput, ContextProfile, PriorCycleContext, AnalysisResult
    from lens.pipeline.prompts import build_system_prompt, build_sentiment_prompt

    ctx = ContextProfile(org_name="Test Org", industry="Tech")
    assert not ctx.is_empty()
    assert "Test Org" in ctx.to_prompt_block()

    prior = PriorCycleContext(
        batch_label="Q4",
        run_sequence=1,
        sentiment_split={"positive": 50, "neutral": 30, "negative": 20},
        top_themes=["theme a", "theme b"],
        executive_summary="Good quarter."
    )
    assert "Q4" in prior.to_prompt_block()

    sys_prompt = build_system_prompt(context=ctx, prior_cycle=prior)
    assert "Test Org" in sys_prompt
    assert "Q4" in sys_prompt

    record_prompt = build_sentiment_prompt("This product is great.")
    assert "positive|neutral|negative" in record_prompt

    print("\n✅ All model and prompt validations passed (no API key needed)\n")


if __name__ == "__main__":
    main()
