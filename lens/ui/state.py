"""Session-state helpers."""

from __future__ import annotations

import streamlit as st

from lens.config import Settings


DEFAULT_STATE = {
    "validated_batch": None,
    "current_result": None,
    "loaded_analysis": None,
    "pipeline_running": False,
    "pending_save_result": None,
    "preview_confirmed": False,
    "app_mode": None,
    "admin_unlocked": False,
    "selected_model": None,
}



def init_session_state(settings: Settings) -> None:
    for key, default_value in DEFAULT_STATE.items():
        st.session_state.setdefault(key, default_value)

    st.session_state.app_mode = settings.app_mode

    if st.session_state.selected_model not in settings.allowed_models:
        st.session_state.selected_model = settings.openai_model

    if not settings.admin_auth_enabled:
        st.session_state.admin_unlocked = False

    if st.session_state.pipeline_running and st.session_state.current_result is not None:
        st.session_state.pipeline_running = False
