"""Sentiment dashboard panels."""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from lens.storage.models import StoredAnalysis

CHART_HEIGHT = 310
SENTIMENT_ORDER = ["Positive", "Neutral", "Negative"]
SENTIMENT_COLORS = ["#36C2B4", "#E9A63A", "#F06D5E"]


def render_sentiment_split_chart(analysis: StoredAnalysis) -> None:
    st.markdown("### Sentiment split")
    split_df = pd.DataFrame(
        [
            {"sentiment": label.title(), "percentage": value}
            for label, value in analysis.sentiment_split.items()
        ]
    )
    if split_df.empty:
        st.info("No scored sentiment data is available for this analysis.")
        return

    chart = (
        alt.Chart(split_df)
        .mark_arc(innerRadius=70)
        .encode(
            theta=alt.Theta(field="percentage", type="quantitative"),
            color=alt.Color(
                field="sentiment",
                type="nominal",
                sort=SENTIMENT_ORDER,
                scale=alt.Scale(domain=SENTIMENT_ORDER, range=SENTIMENT_COLORS),
                legend=alt.Legend(title=None, orient="bottom"),
            ),
            tooltip=[
                alt.Tooltip("sentiment:N", title="Sentiment"),
                alt.Tooltip("percentage:Q", title="Share", format=".1f"),
            ],
        )
        .properties(height=CHART_HEIGHT)
        .configure_view(strokeOpacity=0)
    )
    st.altair_chart(chart, use_container_width=True)


def render_sentiment_distribution_chart(analysis: StoredAnalysis) -> None:
    st.markdown("### Sentiment distribution")
    records = [record for record in analysis.records if record.scored]
    if not records:
        st.info("No scored records are available for the distribution view.")
        return

    histogram_df = pd.DataFrame(
        [
            {
                "sentiment": record.sentiment_label.title(),
                "confidence": record.confidence_score,
                "sequence": record.sequence_number,
            }
            for record in records
        ]
    )
    chart = (
        alt.Chart(histogram_df)
        .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
        .encode(
            x=alt.X("sentiment:N", title="Sentiment", sort=SENTIMENT_ORDER),
            y=alt.Y("count():Q", title="Record count"),
            color=alt.Color(
                "sentiment:N",
                sort=SENTIMENT_ORDER,
                scale=alt.Scale(domain=SENTIMENT_ORDER, range=SENTIMENT_COLORS),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("sentiment:N", title="Sentiment"),
                alt.Tooltip("count():Q", title="Records"),
            ],
        )
        .properties(height=CHART_HEIGHT)
        .configure_view(strokeOpacity=0)
    )
    st.altair_chart(chart, use_container_width=True)
