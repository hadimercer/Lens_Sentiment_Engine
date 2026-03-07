"""Series context dashboard panel."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from lens.storage.models import StoredAnalysis


def render_series_context_panel(analysis: StoredAnalysis) -> None:
    st.markdown("### Series context")
    if not analysis.series_name:
        st.info("This run is not linked to a named series.")
        return

    prior = analysis.prior_cycle_context
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Series", analysis.series_name)
        st.metric("Run sequence", analysis.run_sequence or 1)
    with col2:
        if prior:
            comparison_df = pd.DataFrame(
                [
                    {"sentiment": label.title(), "current": analysis.sentiment_split.get(label, 0), "prior": prior.sentiment_split.get(label, 0)}
                    for label in ["positive", "neutral", "negative"]
                ]
            )
            st.dataframe(comparison_df, use_container_width=True, hide_index=True)
        else:
            st.info("No prior cycle exists for this series yet.")

    if prior:
        st.caption(f"Prior cycle: {prior.batch_label} (run {prior.run_sequence})")
        st.write(prior.executive_summary)
