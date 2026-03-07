from __future__ import annotations

import streamlit as st

from lens.config import estimate_api_calls, get_settings
from lens.ingestion import build_batch_input, validate_batch
from lens.ingestion.service import ValidationError
from lens.pipeline.models import ContextProfile
from lens.storage import get_prior_cycle, get_series_names, retry_save_pending_analysis, save_analysis
from lens.storage.models import StoredAnalysis
from lens.ui.dashboard import render_dashboard
from lens.ui.runtime import (
    render_metric_strip,
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
        "New Analysis",
        "Validate a new batch, add business context, and run the Lens pipeline under the correct controls.",
        "Confirm the preview before you add metadata. Treat context and series linkage as analysis quality controls, not optional cosmetics.",
        badge="Operational workflow",
    )
    render_mode_banner()

    render_metric_strip(
        [
            {
                "label": "Batch warning threshold",
                "value": f"{settings.warn_batch_size}",
                "meta": "Lens begins surfacing cost and speed warnings at this record count.",
            },
            {
                "label": "Extra confirmation",
                "value": f"{settings.extra_confirm_batch_size}",
                "meta": "Large runs above this threshold require an explicit analyst acknowledgement.",
            },
            {
                "label": "Default model",
                "value": settings.openai_model,
                "meta": "The runtime default comes from OPENAI_MODEL and can be overridden only after admin unlock.",
            },
        ]
    )

    intro, sop = st.columns([1.15, 1.0])
    with intro:
        render_note_panel(
            "Purpose of this page",
            "This page is the operational workbench. It controls what enters the pipeline, how that batch is contextualized, and whether the resulting run can be trusted as a meaningful analysis record.",
        )
    with sop:
        render_sop_panel(
            "Standard operating procedure",
            [
                "Choose the input method and validate the batch before touching metadata.",
                "Review the preview carefully to confirm the right text field and timestamp behavior were detected.",
                "Unlock live access if required, then add the batch label, optional series name, and context profile.",
                "Check cost, size, and active-model warnings before running the pipeline.",
            ],
            note="In demos, you can explain the full process even when live execution is disabled.",
        )

    if st.session_state.pending_save_result is not None:
        st.warning("The previous pipeline run succeeded but saving to the database failed. Retry the save below without re-running the pipeline.")
        if st.button("Retry save", key="retry_save_button"):
            try:
                stored_retry = retry_save_pending_analysis(st.session_state.pending_save_result)
                st.session_state.pending_save_result = None
                st.session_state.loaded_analysis = stored_retry
                st.success("Pending result saved successfully.")
            except Exception as error:
                st.error(f"Retry save failed: {error}")

    render_section_header("Step 1 - Prepare the batch", "Choose an input method and validate the incoming text before any scoring begins.", eyebrow="Preparation")
    input_method = st.radio("Input method", options=["Upload CSV", "Paste text"], horizontal=True)

    validated_batch = None
    if input_method == "Upload CSV":
        uploaded_file = st.file_uploader("Upload UTF-8 CSV", type=["csv"])
        if uploaded_file and st.button("Validate uploaded batch", key="validate_upload"):
            try:
                validated_batch = validate_batch(csv_bytes=uploaded_file.getvalue())
                st.session_state.validated_batch = validated_batch
                st.session_state.preview_confirmed = False
                st.session_state.current_result = None
            except ValidationError as error:
                st.error(str(error))
    else:
        raw_text = st.text_area("Paste one record per line", height=240)
        if st.button("Validate pasted batch", key="validate_text"):
            try:
                validated_batch = validate_batch(raw_text=raw_text)
                st.session_state.validated_batch = validated_batch
                st.session_state.preview_confirmed = False
                st.session_state.current_result = None
            except ValidationError as error:
                st.error(str(error))

    validated_batch = st.session_state.validated_batch
    if validated_batch is not None:
        preview = validated_batch.to_preview()
        render_section_header("Step 2 - Review validation", "Confirm record counts, rejected rows, and the first five samples before continuing.", eyebrow="Validation")
        stats_left, stats_right = st.columns([1.45, 1.0])
        with stats_left:
            st.write(
                f"Valid records: {preview.valid_record_count} | Rejected rows: {preview.rejected_row_count} | Detected columns: {', '.join(preview.detected_columns)}"
            )
            st.dataframe(preview.sample_records, use_container_width=True, hide_index=True)
        with stats_right:
            render_note_panel(
                "Preview checkpoint",
                "This is the control gate before metadata. If the preview looks wrong, stop here and correct the source file or text paste instead of pushing a bad batch downstream.",
            )
            st.session_state.preview_confirmed = st.checkbox(
                "I have reviewed the preview and want to continue to metadata.",
                value=st.session_state.preview_confirmed,
            )

    if validated_batch is None or not st.session_state.preview_confirmed:
        current_result = st.session_state.current_result
        if current_result is not None:
            render_section_header("Analysis output", "Once the run completes, review the dashboard as an integrated operating surface rather than a collection of independent widgets.", eyebrow="Results")
            render_dashboard(StoredAnalysis.from_analysis_result(current_result), historical=False)
        return

    access_ready = _render_live_access_controls(settings)
    if not access_ready:
        current_result = st.session_state.current_result
        if current_result is not None:
            render_section_header("Analysis output", "Once the run completes, review the dashboard as an integrated operating surface rather than a collection of independent widgets.", eyebrow="Results")
            render_dashboard(StoredAnalysis.from_analysis_result(current_result), historical=False)
        return

    render_section_header("Step 4 - Add analysis context", "Metadata and context turn a generic sentiment run into a business-specific analysis record.", eyebrow="Context")
    series_names = get_series_names()
    meta_col, context_col = st.columns([1.05, 1.0])
    with meta_col:
        batch_label = st.text_input("Batch label", max_chars=80, help="A human-readable run label such as NPS Q1 2026.")
        domain_tag = st.selectbox("Domain tag", options=["", "cx", "hr", "ops"])
        series_name = st.text_input("Series name (optional)", max_chars=100)
        if series_name:
            matching = [name for name in series_names if series_name.lower() in name.lower()][:5]
            if matching:
                st.caption("Matching series: " + ", ".join(matching))
    with context_col:
        with st.expander("Context profile", expanded=True):
            org_name = st.text_input("Organisation name", max_chars=100)
            industry = st.text_input("Industry", max_chars=80)
            department = st.text_input("Department or team", max_chars=100)
            reporting_period = st.text_input("Reporting period", max_chars=60)
            situational_notes = st.text_area("Situational notes", max_chars=500)

    context = ContextProfile(
        org_name=org_name or None,
        industry=industry or None,
        department=department or None,
        reporting_period=reporting_period or None,
        situational_notes=situational_notes or None,
    )

    render_section_header("Step 5 - Run readiness", "Lens shows the expected API footprint, active model, and any extra acknowledgements required before execution.", eyebrow="Execution")
    selected_model = st.session_state.selected_model or settings.openai_model
    estimated_calls = estimate_api_calls(validated_batch.valid_record_count)
    st.info(f"Estimated API calls for this run: {estimated_calls}")
    st.caption(f"Active model for this session: {selected_model}")

    if validated_batch.valid_record_count >= settings.warn_batch_size:
        st.warning(f"This batch has {validated_batch.valid_record_count} records. Large runs can be slow and expensive on the public deployment.")
    extra_confirmed = True
    if validated_batch.valid_record_count >= settings.extra_confirm_batch_size:
        extra_confirmed = st.checkbox(
            f"I understand this batch exceeds {settings.extra_confirm_batch_size} records and may incur higher API usage.",
            value=False,
        )

    prior_cycle = get_prior_cycle(series_name.strip() or None)
    if prior_cycle:
        st.caption(f"Prior cycle detected: {prior_cycle.batch_label} (run {prior_cycle.run_sequence})")

    run_disabled = (
        st.session_state.pipeline_running
        or settings.app_mode == "demo"
        or not batch_label.strip()
        or not extra_confirmed
        or (settings.admin_auth_enabled and not st.session_state.admin_unlocked)
    )
    progress_slot = st.empty()

    if settings.app_mode == "demo":
        st.info("Live execution is disabled in demo mode because OPENAI_API_KEY is not configured.")

    if st.button("Run pipeline", disabled=run_disabled, key="run_pipeline_button"):
        batch_input = build_batch_input(
            validated_batch,
            batch_label=batch_label.strip(),
            domain_tag=domain_tag or None,
            context=context,
            series_name=series_name.strip() or None,
            prior_cycle=prior_cycle,
        )
        st.session_state.pipeline_running = True
        st.session_state.current_result = None

        progress_bar = st.progress(0)

        def handle_progress(stage: str, processed: int, total: int) -> None:
            total = max(total, 1)
            progress_bar.progress(min(processed / total, 1.0))
            progress_slot.info(f"{stage}: {processed}/{total}")

        try:
            from lens.pipeline import run_pipeline

            result = run_pipeline(
                batch=batch_input,
                api_key=settings.openai_api_key or "",
                progress_callback=handle_progress,
                model=selected_model,
            )
            st.session_state.current_result = result
            try:
                stored = save_analysis(result)
                st.session_state.loaded_analysis = stored
                st.success("Analysis saved to history.")
            except Exception as error:
                st.session_state.pending_save_result = result
                st.warning(f"Analysis completed but saving failed. You can retry saving without re-running. Error: {error}")
        except Exception as error:
            st.error(f"Pipeline run failed: {error}")
        finally:
            st.session_state.pipeline_running = False

    current_result = st.session_state.current_result
    if current_result is not None:
        render_section_header("Analysis output", "Once the run completes, review the dashboard as an integrated operating surface rather than a collection of independent widgets.", eyebrow="Results")
        render_dashboard(StoredAnalysis.from_analysis_result(current_result), historical=False)



def _render_live_access_controls(settings) -> bool:
    render_section_header("Step 3 - Live run access", "Live runs can be locked behind an admin password so the public deployment cannot consume API budget freely.", eyebrow="Access")

    if settings.app_mode == "demo":
        render_status_banner("demo", "Demo walkthrough", "Live execution is unavailable in Demo Mode. You can still review the full workflow and historical outputs.")
        st.session_state.admin_unlocked = False
        st.session_state.selected_model = settings.openai_model
        return True

    if not settings.admin_auth_enabled:
        render_status_banner("ok", "Live run gate disabled", "LENS_ADMIN_PASSWORD is not configured, so live execution remains open in this deployment. The environment default model will be used.")
        st.session_state.selected_model = settings.openai_model
        return True

    if st.session_state.admin_unlocked:
        render_status_banner("ok", "Admin unlocked", "This browser session can execute live runs. The model selector below only affects the current session.")
        selector_index = list(settings.allowed_models).index(st.session_state.selected_model)
        st.selectbox(
            "Live run model",
            options=list(settings.allowed_models),
            index=selector_index,
            key="selected_model",
            help="This override is session-scoped and does not change the deployment default.",
        )
        if st.button("Lock again", key="lock_live_run_access"):
            st.session_state.admin_unlocked = False
            st.session_state.selected_model = settings.openai_model
            st.rerun()
        return True

    password = st.text_input("Admin password", type="password", key="admin_password_input", help="Required for live runs on the public deployment.")
    if st.button("Unlock live runs", key="unlock_live_runs"):
        if password == settings.admin_run_password:
            st.session_state.admin_unlocked = True
            st.session_state.selected_model = settings.openai_model
            st.session_state.admin_password_input = ""
            st.success("Live run access unlocked for this session.")
            st.rerun()
        else:
            st.error("Incorrect password. Live execution remains locked.")
    return False
