"""Anomaly dashboard panel."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from lens.storage.models import StoredAnalysis


def render_anomaly_panel(analysis: StoredAnalysis, *, historical: bool = False) -> None:
    st.markdown("### Anomaly flags")
    if not analysis.anomaly_flags:
        st.success("No anomalies were flagged for this analysis.")
        return

    flags_df = pd.DataFrame(
        [
            {
                "type": flag.anomaly_type,
                "record_id": flag.record_id,
                "time_period": flag.time_period,
                "deviation": flag.deviation_value,
                "description": flag.description,
            }
            for flag in analysis.anomaly_flags
        ]
    )
    st.dataframe(flags_df, use_container_width=True, hide_index=True)

    flagged_records = [record for record in analysis.records if record.is_anomaly]
    if flagged_records:
        flagged_df = pd.DataFrame(
            [
                {
                    "sequence": record.sequence_number,
                    "sentiment": record.sentiment_label,
                    "confidence": record.confidence_score,
                    "reasoning": record.reasoning,
                    "text": record.text_body,
                }
                for record in flagged_records
            ]
        )
        st.dataframe(flagged_df, use_container_width=True, hide_index=True)
