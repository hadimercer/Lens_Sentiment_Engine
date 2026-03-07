"""Timeline dashboard panel."""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from lens.storage.models import StoredAnalysis


def render_timeline_panel(analysis: StoredAnalysis) -> None:
    st.markdown("### Sentiment over time")
    records_with_time = [record for record in analysis.records if record.record_timestamp]
    if not records_with_time:
        st.info("No timestamp column was detected, so the timeline panel is hidden for this batch.")
        return

    df = pd.DataFrame(
        [
            {
                "date": record.record_timestamp,
                "score": _score(record.sentiment_label, record.confidence_score),
                "is_anomaly": record.is_anomaly,
            }
            for record in records_with_time
        ]
    )
    grouped = df.groupby("date", as_index=False).agg(avg_score=("score", "mean"), anomaly_points=("is_anomaly", "sum"))
    grouped["positivity"] = ((grouped["avg_score"] + 1) / 2) * 100

    line = alt.Chart(grouped).mark_line(point=True).encode(
        x=alt.X("date:T", title="Date"),
        y=alt.Y("positivity:Q", title="Positivity %", scale=alt.Scale(domain=[0, 100])),
        tooltip=[alt.Tooltip("date:T"), alt.Tooltip("positivity:Q", format=".1f")],
    )
    points = alt.Chart(grouped[grouped["anomaly_points"] > 0]).mark_circle(size=140, color="#d62728").encode(
        x="date:T",
        y="positivity:Q",
        tooltip=[alt.Tooltip("date:T"), alt.Tooltip("positivity:Q", format=".1f")],
    )
    st.altair_chart((line + points).properties(height=260), use_container_width=True)


def _score(sentiment_label: str, confidence: float) -> float:
    if sentiment_label == "positive":
        return confidence
    if sentiment_label == "negative":
        return -confidence
    return 0.0
