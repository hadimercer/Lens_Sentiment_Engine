from __future__ import annotations

from datetime import date

import streamlit as st

from lens.config import get_settings
from lens.storage import delete_analysis, export_analysis_csv, list_analyses, load_analysis
from lens.storage.models import HistoryFilters
from lens.ui.dashboard import render_dashboard
from lens.ui.runtime import (
    render_empty_state,
    render_mode_banner,
    render_note_panel,
    render_page_masthead,
    render_section_header,
    render_sop_panel,
    render_status_banner,
)



def render_page() -> None:
    settings = get_settings()

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
        _clear_selection_state()
        return
    if not items:
        render_empty_state("No analyses match the current filters. Clear one or more filters to see stored runs.")
        _clear_selection_state()
        return

    selection_col, notes_col = st.columns([1.35, 1])
    with selection_col:
        selected_label = st.selectbox("Select an analysis", options=[item.label for item in items])
        selected_item = next(item for item in items if item.label == selected_label)
        st.session_state.library_selected_analysis_id = selected_item.analysis_id
        if st.button("Load selected analysis"):
            st.session_state.loaded_analysis = load_analysis(selected_item.analysis_id)
    with notes_col:
        render_note_panel(
            "Library note",
            "Loading a stored run rehydrates the saved result surface. It does not call the model again, and it does not alter the historical record.",
        )

    _render_delete_controls(settings, selected_item.analysis_id)

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



def _render_delete_controls(settings, selected_analysis_id: str) -> None:
    if settings.app_mode != "live" or not settings.admin_auth_enabled or not st.session_state.admin_unlocked:
        return

    render_section_header(
        "Admin cleanup",
        "Delete a mistaken or duplicate run from the historical library. This is a hard delete from history and should be used carefully.",
        eyebrow="Admin",
    )
    render_status_banner(
        "error",
        "Destructive action",
        "Deleting a run removes it from the library. Batch records and context are deleted with it, while pipeline logs remain for audit history.",
    )

    confirm = st.checkbox(
        "I understand this permanently deletes the selected analysis from the library.",
        key=f"confirm_delete_{selected_analysis_id}",
    )
    if st.button("Delete selected analysis", key=f"delete_analysis_{selected_analysis_id}", disabled=not confirm):
        try:
            delete_analysis(selected_analysis_id)
            if st.session_state.loaded_analysis and st.session_state.loaded_analysis.analysis_id == selected_analysis_id:
                st.session_state.loaded_analysis = None
            if st.session_state.get("library_selected_analysis_id") == selected_analysis_id:
                st.session_state.library_selected_analysis_id = None
            st.success("Selected analysis deleted successfully.")
            st.rerun()
        except Exception as error:
            st.error(f"Delete failed: {error}")



def _clear_selection_state() -> None:
    st.session_state.library_selected_analysis_id = None
    if st.session_state.loaded_analysis is not None:
        st.session_state.loaded_analysis = None
