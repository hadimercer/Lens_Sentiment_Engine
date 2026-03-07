from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from lens.ui.runtime import prepare_app, render_sidebar_branding, render_sidebar_navigation
from lens.views import (
    render_analysis_library_page,
    render_new_analysis_page,
    render_overview_page,
)

bootstrap_status = prepare_app("Lens")

pages: dict[str, object] = {}
pages["overview"] = st.Page(
    lambda: render_overview_page(pages, bootstrap_status),
    title="Overview",
    icon=":material/home:",
    url_path="overview",
    default=True,
)
pages["new_analysis"] = st.Page(
    render_new_analysis_page,
    title="New Analysis",
    icon=":material/playlist_add_check:",
    url_path="new-analysis",
)
pages["analysis_library"] = st.Page(
    render_analysis_library_page,
    title="Analysis Library",
    icon=":material/library_books:",
    url_path="analysis-library",
)

current_page = st.navigation(list(pages.values()), position="hidden")
page_map = {
    "Overview": "overview",
    "New Analysis": "new_analysis",
    "Analysis Library": "analysis_library",
}
current_key = page_map.get(current_page.title, "overview")
render_sidebar_branding()
render_sidebar_navigation(current_key, pages)
current_page.run()
