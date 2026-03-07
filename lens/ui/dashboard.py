"""Dashboard composition."""

from __future__ import annotations

import html

import streamlit as st

from lens.storage.models import StoredAnalysis

from .panels import (
    render_anomaly_panel,
    render_sentiment_distribution_chart,
    render_sentiment_split_chart,
    render_series_context_panel,
    render_theme_heatmap_chart,
    render_theme_table,
    render_timeline_panel,
)
from .runtime import render_metric_strip, render_note_panel, render_section_header


def render_dashboard(analysis: StoredAnalysis, *, historical: bool = False) -> None:
    st.markdown(f"## {analysis.batch_label}")
    st.caption(f"Analysis ID: {analysis.analysis_id} | Domain: {analysis.domain_tag or 'untagged'} | Records: {analysis.record_count}")

    render_section_header(
        "Executive summary",
        "Use the paragraph, takeaways, and priority actions together as the fast read before you move into the charts.",
        eyebrow="Briefing",
    )
    _render_summary_brief(analysis)

    render_metric_strip(
        [
            {
                "label": "Positive sentiment",
                "value": f"{analysis.sentiment_split.get('positive', 0):.1f}%",
                "meta": "Top-line positive share from the scored records in this batch.",
            },
            {
                "label": "Anomalies flagged",
                "value": f"{analysis.anomaly_count}",
                "meta": "Outlier records and time-based spikes that warrant closer reviewer attention.",
            },
            {
                "label": "Series run",
                "value": f"{analysis.run_sequence or 1}",
                "meta": "Run position inside the linked series, or 1 for standalone analyses.",
            },
        ]
    )

    if analysis.series_name:
        render_section_header("Series context", "When this run belongs to a named series, Lens surfaces the prior-cycle context here.", eyebrow="Comparison")
        render_series_context_panel(analysis)
    else:
        render_note_panel("Series context", "This analysis is not linked to a named series, so there is no prior-cycle comparison panel for this run.")

    render_section_header(
        "Dashboard panels",
        "Scan the top row for distribution and theme shape, then use the theme table and timeline to understand what changed and where action is required.",
        eyebrow="Review surface",
    )
    sentiment_col, distribution_col, theme_col = st.columns(3)
    with sentiment_col:
        render_sentiment_split_chart(analysis)
    with distribution_col:
        render_sentiment_distribution_chart(analysis)
    with theme_col:
        render_theme_heatmap_chart(analysis)

    render_theme_table(analysis)
    render_timeline_panel(analysis)
    render_anomaly_panel(analysis, historical=historical)



def _render_summary_brief(analysis: StoredAnalysis) -> None:
    paragraph = html.escape(analysis.executive_summary or "Summary unavailable.")
    st.markdown(
        f"""
        <section class="ops-summary-paragraph">
            <p>{paragraph}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    takeaway_col, action_col = st.columns(2)
    with takeaway_col:
        _render_summary_card(
            "Key takeaways",
            analysis.key_takeaways,
            "No specific takeaways were returned for this analysis.",
        )
    with action_col:
        _render_summary_card(
            "Priority actions",
            analysis.priority_actions,
            "No priority actions were returned for this analysis.",
        )



def _render_summary_card(title: str, items: list[str], empty_message: str) -> None:
    if items:
        list_items = "".join(f"<li>{html.escape(item)}</li>" for item in items)
    else:
        list_items = f"<li>{html.escape(empty_message)}</li>"
    st.markdown(
        f"""
        <section class="ops-summary-card">
            <h3>{html.escape(title)}</h3>
            <ul>{list_items}</ul>
        </section>
        """,
        unsafe_allow_html=True,
    )
