"""Dashboard composition."""

from __future__ import annotations

import streamlit as st

from lens.storage.models import StoredAnalysis

from .panels import (
    render_anomaly_panel,
    render_sentiment_panel,
    render_series_context_panel,
    render_theme_heatmap_panel,
    render_timeline_panel,
)
from .runtime import render_metric_strip, render_note_panel, render_section_header


def render_dashboard(analysis: StoredAnalysis, *, historical: bool = False) -> None:
    st.markdown(f"## {analysis.batch_label}")
    st.caption(f"Analysis ID: {analysis.analysis_id} | Domain: {analysis.domain_tag or 'untagged'} | Records: {analysis.record_count}")
    st.write(analysis.executive_summary)

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

    render_section_header("Dashboard panels", "Read the result surface from left to right: sentiment, themes, timeline, and anomalies form one integrated narrative.", eyebrow="Review surface")
    col1, col2 = st.columns(2)
    with col1:
        render_sentiment_panel(analysis)
    with col2:
        render_theme_heatmap_panel(analysis)

    render_timeline_panel(analysis)
    render_anomaly_panel(analysis, historical=historical)
