from __future__ import annotations

from datetime import date

import streamlit as st

from lens.storage import export_analysis_csv, list_analyses, load_analysis
from lens.storage.models import HistoryFilters
from lens.ui.dashboard import render_dashboard
from lens.ui.runtime import render_mode_banner, render_note_panel, render_page_masthead, render_section_header, render_sop_panel, render_empty_state


def render_page() -> None:
    render_page_masthead(
        "Analysis Library",
        "Reopen stored runs, inspect historical outputs, and export structured evidence without calling the model again.",
        "Use this page first when you want to show the finished analytical product before the workflow that produces it.",
        badge="Historical review",
    )
    render_mode_banner()

    intro, sop = st.columns([1.15, 1.0])
    with intro:
        render_note_panel(
            "Purpose of this page",
            "Analysis Library is the evidence workspace. It is intended for historical review, side-by-side explanation of prior runs, and downstream export of record-level results.",
        )
    with sop:
        render_sop_panel(
            "Standard operating procedure",
            [
                "Filter the analysis library by series, domain, or date range to narrow the run list.",
                "Load a stored analysis to reopen the full dashboard without rerunning the pipeline.",
                "Inspect the dashboard panels together so you see sentiment, themes, timelines, and anomalies in context.",
                "Use CSV export only after you have interpreted the dashboard result.",
            ],
            note="For reviewer walkthroughs, this page is the cleanest starting point because it shows completed outputs immediately.",
        )

    render_section_header("Find stored analyses", "Scope the library before loading a run back into the dashboard.", eyebrow="Filters")
    series_filter = st.text_input("Series filter")
    domain_filter = st.selectbox("Domain tag", options=["", "cx", "hr", "ops"])
    date_from = st.date_input("From date", value=None)
    date_to = st.date_input("To date", value=None)

    filters = HistoryFilters(
        series_name=series_filter or None,
        domain_tag=domain_filter or None,
        date_from=date_from if isinstance(date_from, date) else None,
        date_to=date_to if isinstance(date_to, date) else None,
    )
    items = list_analyses(filters)
    all_items = list_analyses()

    if not all_items:
        render_empty_state("No analyses are stored yet. Configure the database and seed data to populate the library.")
    elif not items:
        render_empty_state("No analyses match the current filters. Clear one or more filters to see stored runs.")
    else:
        selection_col, notes_col = st.columns([1.35, 1])
        with selection_col:
            selected_label = st.selectbox("Select an analysis", options=[item.label for item in items])
            selected_item = next(item for item in items if item.label == selected_label)
            if st.button("Load selected analysis"):
                st.session_state.loaded_analysis = load_analysis(selected_item.analysis_id)
        with notes_col:
            render_note_panel(
                "Library note",
                "Loading a stored run rehydrates the saved result surface. It does not call the model again, and it does not alter the historical record.",
            )

    loaded_analysis = st.session_state.loaded_analysis
    if loaded_analysis is not None:
        render_section_header("Stored analysis dashboard", "Review the reopened result and export the record-level CSV if you need downstream reporting output.", eyebrow="Evidence")
        render_dashboard(loaded_analysis, historical=True)
        csv_data = export_analysis_csv(loaded_analysis.analysis_id)
        st.download_button(
            "Download CSV export",
            data=csv_data,
            file_name=f"{loaded_analysis.batch_label}_{loaded_analysis.analysis_id[:8]}_export.csv",
            mime="text/csv",
        )
