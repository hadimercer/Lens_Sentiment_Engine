"""Theme heatmap dashboard panel."""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from lens.storage.models import StoredAnalysis


def render_theme_heatmap_panel(analysis: StoredAnalysis) -> None:
    st.markdown("### Theme heatmap")
    if not analysis.themes:
        st.info("No themes were identified for this analysis.")
        return

    df = pd.DataFrame(
        [
            {
                "theme": theme.label,
                "sentiment": theme.dominant_sentiment.title(),
                "frequency": theme.frequency,
                "quotes": " | ".join(theme.representative_quotes),
            }
            for theme in analysis.themes
        ]
    )
    chart = (
        alt.Chart(df)
        .mark_rect()
        .encode(
            x=alt.X("sentiment:N", title="Dominant sentiment"),
            y=alt.Y("theme:N", sort="-x", title="Theme"),
            color=alt.Color("frequency:Q", title="Frequency"),
            tooltip=["theme", "sentiment", "frequency", "quotes"],
        )
        .properties(height=max(240, len(df) * 40))
    )
    st.altair_chart(chart, use_container_width=True)
    st.dataframe(df[["theme", "frequency", "quotes"]], use_container_width=True, hide_index=True)
