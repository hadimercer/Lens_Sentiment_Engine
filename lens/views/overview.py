from __future__ import annotations

import streamlit as st

from lens.storage import list_analyses
from lens.ui.runtime import (
    render_bootstrap_status,
    render_metric_strip,
    render_mode_banner,
    render_note_panel,
    render_page_masthead,
    render_section_header,
    render_sop_panel,
)


def render_page(pages: dict[str, object], bootstrap_status: tuple[bool, str]) -> None:
    ok, message = bootstrap_status

    render_page_masthead(
        "Lens Command Center",
        "Review what Lens is, how the workflow is structured, and where a reviewer or analyst should start.",
        "Use the library first for finished outputs, then move to New Analysis for the operational walkthrough.",
        badge="Sentiment & Text Analytics Tool",
    )
    render_mode_banner()
    render_bootstrap_status(ok, message)

    analyses = list_analyses()
    render_metric_strip(
        [
            {
                "label": "Stored analyses",
                "value": f"{len(analyses)}",
                "meta": "Completed runs currently available in the database for review and export.",
            },
            {
                "label": "Mode",
                "value": st.session_state.app_mode.upper(),
                "meta": "Demo keeps the workflow visible without live OpenAI calls. Live enables fresh runs.",
            },
            {
                "label": "Pending save retry",
                "value": "1" if st.session_state.pending_save_result else "0",
                "meta": "If a save fails after pipeline completion, the result can be retried without re-running.",
            },
        ]
    )

    render_section_header(
        "Workspace paths",
        "Each page has a different job in the review flow, mirroring the IncidentOps command-surface pattern.",
        eyebrow="Navigation",
    )
    col1, col2, col3 = st.columns(3)
    with col1:
        render_note_panel(
            "Overview",
            "Use this page to orient reviewers, explain the operating model, and set the path through the rest of the app.",
        )
        st.page_link(pages["overview"], label="Open Overview", use_container_width=True)
    with col2:
        render_note_panel(
            "New Analysis",
            "Use this page to validate a batch, add context, and run the analysis pipeline when live mode is available.",
        )
        st.page_link(pages["new_analysis"], label="Open New Analysis", use_container_width=True)
    with col3:
        render_note_panel(
            "Analysis Library",
            "Use this page to inspect finished outputs, reopen dashboards, and export record-level CSV results.",
        )
        st.page_link(pages["analysis_library"], label="Open Analysis Library", use_container_width=True)

    left, right = st.columns([1.15, 1.0])
    with left:
        render_sop_panel(
            "How to use Lens",
            [
                "Start in Analysis Library if you want to show the completed product before explaining the workflow.",
                "Move to New Analysis to demonstrate how a batch is validated, previewed, labeled, and contextualized.",
                "Use the dashboard panels together to interpret sentiment, themes, anomalies, and series context as one review surface.",
                "Download exports only after you have interpreted the run inside the dashboard, not as a substitute for it.",
            ],
            note="For a portfolio demo, treat Overview as the briefing page, not the work page.",
        )
    with right:
        render_note_panel(
            "Reviewer guidance",
            "Lens is meant to feel like an analyst command surface: orient, inspect stored evidence, then walk the audience through how a new run is prepared and executed.",
        )
        render_note_panel(
            "What changes between pages",
            "Overview is explanatory, New Analysis is operational, and Analysis Library is evidentiary. That separation is intentional and should stay clear in demos.",
        )
