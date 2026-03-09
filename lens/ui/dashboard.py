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
from .runtime import render_metric_strip, render_section_header



def render_dashboard(analysis: StoredAnalysis, *, historical: bool = False) -> None:
    st.markdown(f"## {analysis.batch_label}")
    st.caption(f"Analysis ID: {analysis.analysis_id} | Domain: {analysis.domain_tag or 'untagged'} | Records: {analysis.record_count}")

    st.markdown("### Executive summary")
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

    if analysis.series_name and analysis.prior_cycle_context:
        render_series_context_panel(analysis)

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
            <p>{paragraph.replace(chr(10), '<br/><br/>')}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Priority actions")
    _render_text_list(
        analysis.priority_actions,
        "No priority actions were returned for this analysis.",
        css_class="ops-summary-card",
    )

    st.markdown("### Issue clusters")
    if analysis.issue_clusters:
        for cluster in analysis.issue_clusters:
            _render_issue_cluster(cluster)
    else:
        _render_text_list([], "No issue clusters were returned for this analysis.", css_class="ops-summary-card")

    st.markdown("### Positive signals")
    if analysis.positive_signals:
        for signal in analysis.positive_signals:
            _render_positive_signal(signal)
    else:
        _render_text_list([], "No positive signals were returned for this analysis.", css_class="ops-summary-card")



def _render_issue_cluster(cluster) -> None:
    with st.container(border=True):
        st.markdown(f"#### {html.escape(cluster.label)}")
        st.caption(
            f"Severity: {cluster.severity.title()} | Frequency: {cluster.frequency} | Sentiment: {cluster.sentiment_direction.title()}"
        )
        if cluster.trend_note:
            st.markdown(f"**Trend note:** {html.escape(cluster.trend_note)}")

        left, middle, right = st.columns(3)
        with left:
            st.markdown("**Reported problems**")
            _render_markdown_list(cluster.problem_patterns, "No detailed problem patterns were returned.")
        with middle:
            st.markdown("**Evidence**")
            _render_markdown_list(cluster.evidence_quotes, "No evidence quotes were returned.")
        with right:
            st.markdown("**Recommended actions**")
            _render_markdown_list(cluster.recommended_actions, "No recommended actions were returned.")



def _render_positive_signal(signal) -> None:
    with st.container(border=True):
        st.markdown(f"#### {html.escape(signal.label)}")
        st.caption(f"Frequency: {signal.frequency}")
        st.write(signal.why_it_matters or "No explanation returned.")

        left, right = st.columns(2)
        with left:
            st.markdown("**Evidence**")
            _render_markdown_list(signal.evidence_quotes, "No evidence quotes were returned.")
        with right:
            st.markdown("**What to preserve or scale**")
            _render_markdown_list(
                signal.recommended_preservation_actions,
                "No preservation actions were returned.",
            )



def _render_text_list(items: list[str], empty_message: str, *, heading: str | None = None, css_class: str = "ops-summary-subcard") -> None:
    title_html = f"<h3>{html.escape(heading)}</h3>" if heading else ""
    list_items = _list_html(items, empty_message)
    st.markdown(
        f"""
        <section class="{css_class}">
            {title_html}
            {list_items}
        </section>
        """,
        unsafe_allow_html=True,
    )



def _render_markdown_list(items: list[str], empty_message: str) -> None:
    if items:
        st.markdown("\n".join(f"- {item}" for item in items))
    else:
        st.markdown(f"- {empty_message}")



def _list_html(items: list[str], empty_message: str) -> str:
    if items:
        list_items = "".join(f"<li>{html.escape(item)}</li>" for item in items)
    else:
        list_items = f"<li>{html.escape(empty_message)}</li>"
    return f"<ul>{list_items}</ul>"
