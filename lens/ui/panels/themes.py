"""Theme dashboard panels."""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from lens.storage.models import StoredAnalysis

CHART_HEIGHT = 310


def render_theme_heatmap_chart(analysis: StoredAnalysis) -> None:
    st.markdown("### Theme heatmap")
    if not analysis.themes:
        st.info("No themes were identified for this analysis.")
        return

    df = _theme_dataframe(analysis)
    chart = (
        alt.Chart(df)
        .mark_rect()
        .encode(
            x=alt.X("dominant_sentiment:N", title="Dominant sentiment"),
            y=alt.Y("theme:N", sort="-x", title="Theme"),
            color=alt.Color("frequency:Q", title="Frequency"),
            tooltip=[
                alt.Tooltip("theme:N", title="Theme"),
                alt.Tooltip("dominant_sentiment:N", title="Dominant sentiment"),
                alt.Tooltip("frequency:Q", title="Frequency"),
                alt.Tooltip("quotes:N", title="Representative quotes"),
            ],
        )
        .properties(height=CHART_HEIGHT)
        .configure_view(strokeOpacity=0)
    )
    st.altair_chart(chart, use_container_width=True)


def render_theme_table(analysis: StoredAnalysis) -> None:
    st.markdown("### Theme details")
    if not analysis.themes:
        st.info("No theme detail table is available for this analysis.")
        return

    df = _theme_dataframe(analysis)
    st.dataframe(
        df[["theme", "frequency", "dominant_sentiment", "quotes"]],
        use_container_width=True,
        hide_index=True,
    )


def _theme_dataframe(analysis: StoredAnalysis) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "theme": theme.label,
                "dominant_sentiment": theme.dominant_sentiment.title(),
                "frequency": theme.frequency,
                "quotes": " | ".join(theme.representative_quotes),
            }
            for theme in analysis.themes
        ]
    )
