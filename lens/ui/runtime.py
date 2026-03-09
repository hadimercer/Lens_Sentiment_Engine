"""Shared Streamlit app runtime helpers."""

from __future__ import annotations

import html

import streamlit as st

from lens.config import get_settings
from lens.storage import bootstrap_database

from .state import init_session_state

TOKENS = {
    "font_ui": "'IBM Plex Sans', 'Segoe UI', sans-serif",
    "font_mono": "'IBM Plex Mono', 'Cascadia Code', monospace",
    "bg": "#09131A",
    "bg_alt": "#0D1B24",
    "surface": "#11222C",
    "surface_alt": "#152B37",
    "surface_soft": "#1B3542",
    "border": "rgba(125, 164, 185, 0.18)",
    "border_strong": "rgba(125, 164, 185, 0.34)",
    "text": "#EAF4F8",
    "text_muted": "#A7BBC7",
    "text_soft": "#7F96A3",
    "accent": "#36C2B4",
    "accent_soft": "rgba(54, 194, 180, 0.16)",
    "warning": "#E9A63A",
    "warning_soft": "rgba(233, 166, 58, 0.14)",
    "danger": "#F06D5E",
    "danger_soft": "rgba(240, 109, 94, 0.16)",
    "success": "#74D8A6",
    "success_soft": "rgba(116, 216, 166, 0.16)",
    "shadow": "0 24px 60px rgba(0, 0, 0, 0.22)",
    "radius_xl": "24px",
    "radius_l": "18px",
    "radius_m": "14px",
    "radius_s": "10px",
}



def prepare_app(title: str = "Lens") -> tuple[bool, str]:
    settings = get_settings()
    st.set_page_config(page_title=title, layout="wide", page_icon=":material/analytics:", initial_sidebar_state="expanded")
    init_session_state(settings)
    apply_theme()

    if "bootstrap_status" not in st.session_state:
        try:
            ok, message = bootstrap_database()
        except Exception as error:
            ok, message = False, f"Database bootstrap failed: {error}"
        st.session_state.bootstrap_status = (ok, message)

    return st.session_state.bootstrap_status



def apply_theme() -> None:
    css = f"""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');
      :root {{
        --io-bg: {TOKENS['bg']};
        --io-bg-alt: {TOKENS['bg_alt']};
        --io-surface: {TOKENS['surface']};
        --io-surface-alt: {TOKENS['surface_alt']};
        --io-surface-soft: {TOKENS['surface_soft']};
        --io-border: {TOKENS['border']};
        --io-border-strong: {TOKENS['border_strong']};
        --io-text: {TOKENS['text']};
        --io-text-muted: {TOKENS['text_muted']};
        --io-text-soft: {TOKENS['text_soft']};
        --io-accent: {TOKENS['accent']};
        --io-accent-soft: {TOKENS['accent_soft']};
        --io-warning: {TOKENS['warning']};
        --io-warning-soft: {TOKENS['warning_soft']};
        --io-danger: {TOKENS['danger']};
        --io-danger-soft: {TOKENS['danger_soft']};
        --io-success: {TOKENS['success']};
        --io-success-soft: {TOKENS['success_soft']};
      }}
      html, body, [class*="css"] {{
        font-family: {TOKENS['font_ui']};
      }}
      .stApp {{
        background:
          radial-gradient(circle at top left, rgba(54,194,180,0.10), transparent 28%),
          radial-gradient(circle at top right, rgba(233,166,58,0.09), transparent 22%),
          linear-gradient(180deg, {TOKENS['bg_alt']} 0%, {TOKENS['bg']} 100%);
        color: {TOKENS['text']};
      }}
      [data-testid="stHeader"] {{
        background: rgba(9, 19, 26, 0.72);
      }}
      [data-testid="stAppViewContainer"] > .main {{
        padding-top: 1.4rem;
      }}
      [data-testid="stSidebar"] > div:first-child {{
        background: linear-gradient(180deg, rgba(17,34,44,0.96) 0%, rgba(13,27,36,0.98) 100%);
        border-right: 1px solid {TOKENS['border']};
      }}
      [data-testid="stSidebarNav"] {{ display: none; }}
      [data-testid="stSidebar"] * {{ color: {TOKENS['text']}; }}
      [data-testid="stMetricLabel"], [data-testid="stMetricValue"] {{ color: {TOKENS['text']}; }}
      [data-testid="stCaptionContainer"], .stCaption {{ color: {TOKENS['text_soft']}; }}
      .block-container {{ padding-top: 4.85rem; padding-bottom: 3rem; max-width: 1520px; }}
      .ops-sidebar-brand {{
        padding: 1rem 1rem 0.9rem 1rem;
        border-radius: {TOKENS['radius_l']};
        margin-bottom: 1rem;
        border: 1px solid {TOKENS['border_strong']};
        background: linear-gradient(135deg, rgba(54,194,180,0.18), rgba(17,34,44,0.88));
        box-shadow: {TOKENS['shadow']};
      }}
      .ops-sidebar-brand .eyebrow {{
        color: {TOKENS['accent']};
        font-family: {TOKENS['font_mono']};
        font-size: 0.74rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
      }}
      .ops-sidebar-brand h2 {{ margin: 0.25rem 0 0 0; font-size: 1.25rem; color: {TOKENS['text']}; }}
      .ops-sidebar-brand p {{ margin: 0.4rem 0 0 0; color: {TOKENS['text_muted']}; font-size: 0.88rem; line-height: 1.45; }}
      .ops-sidebar-section-label {{
        color: {TOKENS['text_soft']};
        font-family: {TOKENS['font_mono']};
        font-size: 0.74rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin: 0.9rem 0 0.55rem 0;
      }}
      .ops-masthead {{
        position: relative;
        overflow: hidden;
        padding: 1.35rem 1.45rem 1.25rem 1.45rem;
        border-radius: {TOKENS['radius_xl']};
        border: 1px solid {TOKENS['border_strong']};
        background: linear-gradient(135deg, rgba(54,194,180,0.16) 0%, rgba(17,34,44,0.94) 32%, rgba(9,19,26,0.97) 100%);
        box-shadow: {TOKENS['shadow']};
        margin-bottom: 1rem;
      }}
      .ops-masthead::after {{
        content: "";
        position: absolute;
        inset: auto -5% -45% auto;
        width: 280px;
        height: 280px;
        border-radius: 999px;
        background: radial-gradient(circle, rgba(233,166,58,0.18), transparent 65%);
        pointer-events: none;
      }}
      .ops-eyebrow {{
        color: {TOKENS['accent']};
        font-family: {TOKENS['font_mono']};
        font-size: 0.76rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin-bottom: 0.4rem;
      }}
      .ops-masthead h1 {{ margin: 0; color: {TOKENS['text']}; font-size: 2rem; line-height: 1.05; }}
      .ops-masthead .objective {{ margin-top: 0.55rem; color: {TOKENS['text_muted']}; font-size: 1rem; max-width: 58rem; }}
      .ops-what-matters {{ margin-top: 0.95rem; display: inline-flex; gap: 0.5rem; flex-wrap: wrap; align-items: center; }}
      .ops-what-matters .label {{ color: {TOKENS['text_soft']}; font-family: {TOKENS['font_mono']}; font-size: 0.74rem; text-transform: uppercase; letter-spacing: 0.10em; }}
      .ops-chip {{
        display: inline-flex; align-items: center; border-radius: 999px; padding: 0.24rem 0.68rem;
        border: 1px solid {TOKENS['border_strong']}; background: rgba(17,34,44,0.92);
        color: {TOKENS['text_muted']}; font-size: 0.82rem;
      }}
      .ops-chip.status-good {{ background: {TOKENS['success_soft']}; color: {TOKENS['success']}; border-color: rgba(116,216,166,0.30); }}
      .ops-chip.status-bad {{ background: {TOKENS['danger_soft']}; color: {TOKENS['danger']}; border-color: rgba(240,109,94,0.30); }}
      .ops-chip.status-warn {{ background: {TOKENS['warning_soft']}; color: {TOKENS['warning']}; border-color: rgba(233,166,58,0.30); }}
      .ops-panel-header {{ display: flex; justify-content: space-between; gap: 1rem; align-items: flex-start; margin-bottom: 0.75rem; }}
      .ops-panel-header h3 {{ margin: 0.15rem 0 0 0; color: {TOKENS['text']}; font-size: 1.08rem; }}
      .ops-panel-header p {{ margin: 0.35rem 0 0 0; color: {TOKENS['text_muted']}; font-size: 0.88rem; line-height: 1.45; }}
      .ops-panel-header .eyebrow {{ color: {TOKENS['text_soft']}; font-family: {TOKENS['font_mono']}; font-size: 0.72rem; letter-spacing: 0.10em; text-transform: uppercase; }}
      .ops-kpi-strip {{ margin: 1.15rem 0; }}
      .ops-kpi-card {{
        border: 1px solid {TOKENS['border']};
        background: linear-gradient(180deg, rgba(21,43,55,0.96), rgba(13,27,36,0.96));
        border-radius: {TOKENS['radius_l']};
        padding: 1rem 1rem 0.95rem 1rem;
        min-height: 176px;
        height: 176px;
        display: flex;
        flex-direction: column;
        box-shadow: {TOKENS['shadow']};
      }}
      .ops-kpi-card .label {{ color: {TOKENS['text_soft']}; text-transform: uppercase; letter-spacing: 0.10em; font-size: 0.73rem; font-family: {TOKENS['font_mono']}; }}
      .ops-kpi-card .value {{ margin-top: 0.45rem; color: {TOKENS['text']}; font-size: 1.85rem; line-height: 1; font-weight: 700; }}
      .ops-kpi-card .meta {{ margin-top: 0.6rem; color: {TOKENS['text_muted']}; font-size: 0.84rem; line-height: 1.45; min-height: 3.65rem; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; }}
      .ops-kpi-card .signal {{ margin-top: auto; height: 4px; border-radius: 999px; background: linear-gradient(90deg, rgba(54,194,180,0.12), rgba(54,194,180,0.72)); }}
      .ops-note, .ops-sop, .ops-status, .ops-summary-card, .ops-summary-paragraph {{
        border: 1px solid {TOKENS['border']};
        border-radius: {TOKENS['radius_l']};
        background: linear-gradient(180deg, rgba(17,34,44,0.96), rgba(9,19,26,0.98));
        padding: 1rem 1rem 0.9rem 1rem;
        box-shadow: {TOKENS['shadow']};
        margin-bottom: 1rem;
      }}
      .ops-note h3, .ops-sop h3, .ops-summary-card h3 {{ margin: 0 0 0.45rem 0; color: {TOKENS['text']}; font-size: 1.05rem; }}
      .ops-note p, .ops-sop p, .ops-sop li, .ops-note div, .ops-summary-paragraph p, .ops-summary-card li {{ color: {TOKENS['text_muted']}; line-height: 1.5; }}
      .ops-summary-paragraph p {{ margin: 0; font-size: 0.98rem; }}
      .ops-summary-card ul, .ops-summary-subcard ul {{ margin: 0.1rem 0 0 1rem; padding-left: 0.35rem; }}
      .ops-summary-card li + li, .ops-summary-subcard li + li {{ margin-top: 0.4rem; }}
      .ops-summary-subcard {{
        border: 1px solid {TOKENS['border']};
        border-radius: {TOKENS['radius_m']};
        background: rgba(17,34,44,0.72);
        padding: 0.85rem 0.9rem 0.8rem 0.9rem;
        margin-bottom: 0.8rem;
      }}
      .ops-summary-subcard h3 {{ margin: 0 0 0.45rem 0; color: {TOKENS['text']}; font-size: 0.96rem; }}
      .ops-cluster-card, .ops-positive-card {{ margin-bottom: 0.75rem; }}
      .ops-structured-card {{ margin-bottom: 1rem; }}
      .ops-structured-card__header h3 {{ margin: 0; color: {TOKENS['text']}; font-size: 1.02rem; }}
      .ops-structured-card__meta {{ margin-top: 0.45rem; display: flex; flex-wrap: wrap; gap: 0.8rem; color: {TOKENS['text_soft']}; font-size: 0.84rem; }}
      .ops-structured-card__grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0.85rem; margin-top: 0.95rem; }}
      .ops-structured-card__grid h4 {{ margin: 0 0 0.45rem 0; color: {TOKENS['text']}; font-size: 0.92rem; }}
      .ops-summary-inline-note {{ margin-top: 0.75rem; color: {TOKENS['text_muted']}; line-height: 1.5; }}
      @media (max-width: 900px) {{
        .ops-structured-card__grid {{ grid-template-columns: 1fr; }}
      }}
      .ops-sop ol {{ margin: 0.35rem 0 0 1rem; padding-left: 0.5rem; }}
      .ops-status strong {{ color: {TOKENS['text']}; }}
      .ops-status.demo {{ background: linear-gradient(180deg, rgba(233,166,58,0.12), rgba(17,34,44,0.98)); }}
      .ops-status.live {{ background: linear-gradient(180deg, rgba(54,194,180,0.12), rgba(17,34,44,0.98)); }}
      .ops-status.ok {{ background: linear-gradient(180deg, rgba(116,216,166,0.12), rgba(17,34,44,0.98)); }}
      .ops-status.error {{ background: linear-gradient(180deg, rgba(240,109,94,0.12), rgba(17,34,44,0.98)); }}
      .ops-empty {{ border: 1px dashed {TOKENS['border_strong']}; border-radius: {TOKENS['radius_m']}; padding: 1rem; color: {TOKENS['text_soft']}; background: rgba(17,34,44,0.55); }}
      .stDataFrame, [data-testid="stDataFrame"], div[data-testid="stMetric"] {{ border: 1px solid {TOKENS['border']} !important; border-radius: {TOKENS['radius_m']}; }}
      .stDownloadButton button, .stButton button, .stPageLink a {{ border-radius: 999px; border: 1px solid {TOKENS['border_strong']}; background: rgba(17,34,44,0.92); color: {TOKENS['text']}; }}
      .stSelectbox label, .stMultiSelect label, .stDateInput label, .stTextInput label, .stTextArea label, .stRadio label, .stFileUploader label {{ color: {TOKENS['text_soft']}; font-size: 0.76rem; text-transform: uppercase; letter-spacing: 0.08em; }}
      .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {{ color: {TOKENS['text']}; }}
      [data-testid="stRadio"] > div {{ gap: 0.35rem; }}
      [data-testid="stRadio"] label {{
        border: 1px solid {TOKENS['border']};
        background: rgba(17,34,44,0.82);
        border-radius: {TOKENS['radius_m']};
        padding: 0.55rem 0.7rem;
        margin-bottom: 0.15rem;
      }}
      [data-testid="stRadio"] label:has(input:checked) {{
        border-color: {TOKENS['border_strong']};
        background: linear-gradient(180deg, rgba(54,194,180,0.18), rgba(17,34,44,0.92));
      }}
      @media (max-width: 900px) {{
        .block-container {{ padding-top: 5.6rem; }}
        [data-testid="stAppViewContainer"] > .main {{ padding-top: 1.8rem; }}
      }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)



def render_sidebar_branding() -> None:
    settings = get_settings()
    status_class = "status-good" if settings.app_mode == "live" else "status-warn"
    status_label = "Live mode" if settings.app_mode == "live" else "Demo mode"
    st.sidebar.markdown(
        f"""
        <div class="ops-sidebar-brand">
          <div class="eyebrow">Modern Ops Command</div>
          <h2>Lens</h2>
          <p>Sentiment &amp; Text Analytics Tool for batch review, contextual analysis, and historical comparison.</p>
          <div style="margin-top:0.75rem;"><span class="ops-chip {status_class}">{status_label}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )



def render_sidebar_navigation(current_page: str, pages: dict[str, object]) -> None:
    st.sidebar.markdown('<div class="ops-sidebar-section-label">Workstreams</div>', unsafe_allow_html=True)
    labels = {
        "overview": "Overview",
        "new_analysis": "New Analysis",
        "analysis_library": "Analysis Library",
    }
    options = list(labels.keys())
    current_index = options.index(current_page) if current_page in options else 0
    selected = st.sidebar.radio(
        "Navigation",
        options,
        format_func=lambda key: labels[key],
        index=current_index,
        label_visibility="collapsed",
        key=f"sidebar_nav_{current_page}",
    )
    if selected != current_page:
        st.switch_page(pages[selected])



def render_page_masthead(title: str, objective: str, what_matters: str, badge: str | None = None) -> None:
    badge_html = f'<span class="ops-chip">{html.escape(badge)}</span>' if badge else ""
    st.markdown(
        f"""
        <section class="ops-masthead">
          <div class="ops-eyebrow">Operations Review Surface</div>
          <div style="display:flex;justify-content:space-between;gap:1rem;align-items:flex-start;flex-wrap:wrap;">
            <div>
              <h1>{html.escape(title)}</h1>
              <div class="objective">{html.escape(objective)}</div>
              <div class="ops-what-matters">
                <span class="label">What matters now</span>
                <span class="ops-chip">{html.escape(what_matters)}</span>
              </div>
            </div>
            <div>{badge_html}</div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )



def render_section_header(title: str, description: str, eyebrow: str = "Analysis") -> None:
    st.markdown(
        f"""
        <div class="ops-panel-header">
          <div>
            <div class="eyebrow">{html.escape(eyebrow)}</div>
            <h3>{html.escape(title)}</h3>
            <p>{html.escape(description)}</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )



def render_metric_strip(metrics: list[dict[str, str]]) -> None:
    if not metrics:
        return
    st.markdown('<div class="ops-kpi-strip">', unsafe_allow_html=True)
    cols = st.columns(len(metrics))
    for col, metric in zip(cols, metrics):
        with col:
            accent_style = metric.get("accent_style", "")
            st.markdown(
                f"""
                <div class="ops-kpi-card" style="{accent_style}">
                  <div class="label">{html.escape(metric['label'])}</div>
                  <div class="value">{html.escape(metric['value'])}</div>
                  <div class="meta">{html.escape(metric.get('meta', ''))}</div>
                  <div class="signal"></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    st.markdown('</div>', unsafe_allow_html=True)



def render_sop_panel(title: str, steps: list[str], *, note: str | None = None) -> None:
    steps_html = "".join(f"<li>{html.escape(step)}</li>" for step in steps)
    note_html = f"<p><strong>Tip:</strong> {html.escape(note)}</p>" if note else ""
    st.markdown(
        f"""
        <section class="ops-sop">
            <h3>{html.escape(title)}</h3>
            <ol>{steps_html}</ol>
            {note_html}
        </section>
        """,
        unsafe_allow_html=True,
    )



def render_note_panel(title: str, body: str) -> None:
    st.markdown(
        f"""
        <section class="ops-note">
            <h3>{html.escape(title)}</h3>
            <div>{html.escape(body)}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )



def render_status_banner(kind: str, title: str, body: str) -> None:
    st.markdown(
        f"""
        <section class="ops-status {html.escape(kind)}">
            <strong>{html.escape(title)}</strong><br/>
            <span>{html.escape(body)}</span>
        </section>
        """,
        unsafe_allow_html=True,
    )



def render_mode_banner() -> None:
    settings = get_settings()
    if settings.app_mode == "demo":
        render_status_banner("demo", "Demo mode is active", "OPENAI_API_KEY is not configured. Historical demo data remains available, but live pipeline execution is disabled.")
    else:
        render_status_banner("live", "Live mode is active", "Uploads and OpenAI-powered analysis runs are enabled for this session.")



def render_bootstrap_status(ok: bool, message: str) -> None:
    if ok:
        render_status_banner("ok", "Database status", message)
    else:
        render_status_banner("error", "Database status", message)



def render_empty_state(message: str) -> None:
    st.markdown(f'<div class="ops-empty">{html.escape(message)}</div>', unsafe_allow_html=True)



