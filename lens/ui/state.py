"""Session-state helpers."""

from __future__ import annotations

import streamlit as st


DEFAULT_STATE = {
    "validated_batch": None,
    "current_result": None,
    "loaded_analysis": None,
    "pipeline_running": False,
    "pending_save_result": None,
    "preview_confirmed": False,
    "app_mode": None,
}


def init_session_state(app_mode: str) -> None:
    for key, default_value in DEFAULT_STATE.items():
        st.session_state.setdefault(key, default_value)
    st.session_state.app_mode = app_mode
    if st.session_state.pipeline_running and st.session_state.current_result is not None:
        st.session_state.pipeline_running = False
