"""Prompt construction for Lens pipeline calls."""

from __future__ import annotations

from typing import Optional

from .models import ContextProfile, PriorCycleContext


def build_system_prompt(
    context: Optional[ContextProfile] = None,
    prior_cycle: Optional[PriorCycleContext] = None,
    has_timestamps: bool = False,
) -> str:
    sections = [
        (
            "You are an expert business text analyst. "
            "You analyse business text with precision, referencing any organisational context supplied. "
            "You always respond with valid JSON exactly matching the requested schema."
        )
    ]

    if context and not context.is_empty():
        sections.append("ORGANISATIONAL CONTEXT:\n" + context.to_prompt_block())
    else:
        sections.append(
            "ORGANISATIONAL CONTEXT: None supplied. Use domain-agnostic professional framing."
        )

    if prior_cycle:
        sections.append(
            "PRIOR CYCLE DATA - you must reference directional change, trend, and momentum in your output:\n"
            + prior_cycle.to_prompt_block()
        )

    if has_timestamps:
        sections.append(
            "TIMESTAMP NOTE: Some records have timestamps. Be consistent with date references when a user message requests trend-aware output."
        )

    sections.append(
        "IMPORTANT: Respond only with valid JSON. No explanation, no markdown, no code fences."
    )
    return "\n\n".join(sections)


def build_sentiment_prompt(text: str) -> str:
    return (
        "Analyse the sentiment of the following business text.\n\n"
        f'TEXT: """{text}"""\n\n'
        "Respond with JSON matching exactly this schema:\n"
        '{"sentiment_label": "positive|neutral|negative", '
        '"confidence_score": 0.0, '
        '"reasoning": "One sentence."}'
    )


def build_theme_prompt(records: list[str], context: Optional[ContextProfile] = None) -> str:
    max_record_chars = 200
    max_records_in_prompt = 200
    sampled = records[:max_records_in_prompt]
    numbered = "\n".join(
        f"[{index + 1}] {record[:max_record_chars]}{'...' if len(record) > max_record_chars else ''}"
        for index, record in enumerate(sampled)
    )

    context_note = ""
    if context and not context.is_empty():
        context_note = f"\nThis text comes from: {context.to_prompt_block()}\n"

    return (
        f"Identify the top 5 to 8 recurring themes across the following {len(sampled)} business text records.\n"
        f"{context_note}\n"
        f"RECORDS:\n{numbered}\n\n"
        "For each theme, identify: a specific descriptive label, the estimated number of records it appears in, "
        "the dominant sentiment, and 1-2 representative direct quotes from the records above.\n\n"
        "Respond with JSON matching exactly this schema:\n"
        '{"themes": [{"label": "str", "frequency": 0, "dominant_sentiment": "positive|neutral|negative", '
        '"representative_quotes": ["str", "str"]}]}'
    )


def build_summary_prompt(
    sentiment_split: dict,
    top_themes: list[str],
    context: Optional[ContextProfile] = None,
    prior_cycle: Optional[PriorCycleContext] = None,
    batch_label: str = "",
) -> str:
    pos = sentiment_split.get("positive", 0)
    neu = sentiment_split.get("neutral", 0)
    neg = sentiment_split.get("negative", 0)
    themes_str = ", ".join(top_themes[:3])

    context_block = ""
    if context and not context.is_empty():
        context_block = f"\nContext: {context.to_prompt_block()}\n"

    longitudinal_instruction = ""
    if prior_cycle:
        longitudinal_instruction = (
            "\nIMPORTANT: This run belongs to a series with prior history. Your summary must explicitly reference directional change, "
            "whether key themes are emerging, persistent, or resolved, and whether sentiment improved, declined, or held steady."
        )

    return (
        "Write a 2-3 sentence executive summary for a business text analysis.\n"
        f"{context_block}"
        f"Batch label: {batch_label or 'Unnamed batch'}\n"
        f"Sentiment split: {pos:.0f}% positive, {neu:.0f}% neutral, {neg:.0f}% negative\n"
        f"Top themes: {themes_str}\n"
        f"{longitudinal_instruction}\n\n"
        "The summary should be plain language, suitable as a dashboard header. Reference the organisation and context where available.\n\n"
        'Respond with JSON matching exactly this schema:\n{"executive_summary": "Your 2-3 sentence summary here."}'
    )
