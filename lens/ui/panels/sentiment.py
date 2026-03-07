"""Sentiment dashboard panel."""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from lens.storage.models import StoredAnalysis


def render_sentiment_panel(analysis: StoredAnalysis) -> None:
    st.markdown("### Sentiment breakdown")
    split_df = pd.DataFrame(
        [
            {"sentiment": label.title(), "percentage": value}
            for label, value in analysis.sentiment_split.items()
        ]
    )
    donut = (
        alt.Chart(split_df)
        .mark_arc(innerRadius=50)
        .encode(
            theta=alt.Theta(field="percentage", type="quantitative"),
            color=alt.Color(field="sentiment", type="nominal"),
            tooltip=["sentiment", alt.Tooltip("percentage", format=".1f")],
        )
        .properties(height=260)
    )
    st.altair_chart(donut, use_container_width=True)

    histogram_df = pd.DataFrame(
        [
            {
                "sentiment": record.sentiment_label.title(),
                "confidence": record.confidence_score,
                "sequence": record.sequence_number,
            }
            for record in analysis.records
        ]
    )
    histogram = (
        alt.Chart(histogram_df)
        .mark_bar()
        .encode(
            x=alt.X("sentiment:N", title="Sentiment"),
            y=alt.Y("count():Q", title="Record count"),
            color="sentiment:N",
        )
        .properties(height=220)
    )
    st.altair_chart(histogram, use_container_width=True)
