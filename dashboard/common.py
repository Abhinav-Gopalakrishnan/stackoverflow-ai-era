"""Shared components, loaders, and state management for the Streamlit dashboard."""

from pathlib import Path
import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).resolve().parent / "data"

# Academic & Publication Palette for 13 study tags + ALL
TAG_COLORS = {
    "ALL": "#1D4E89",          # Deep Academic Navy
    "python": "#3572A5",       # Python Blue
    "javascript": "#9B7100",   # Gold with contrast on white chart canvases
    "java": "#B07219",         # Java Warm Coffee
    "sql": "#E38C00",          # SQL Burnt Orange
    "pandas": "#150458",       # Pandas Dark Indigo
    "reactjs": "#087F9C",      # React Teal
    "android": "#20814B",      # Android Green
    "excel": "#107C41",        # Excel Forest Green
    "r": "#198CE7",            # R Blue
    "docker": "#2496ED",       # Docker Blue
    "powerbi": "#A87900",      # PowerBI Gold
    "fastapi": "#059669",      # FastAPI Emerald / Teal
    "openai-api": "#DC2626",   # OpenAI Crimson
}

ALL_TAGS = [
    "ALL",
    "python",
    "javascript",
    "java",
    "sql",
    "pandas",
    "reactjs",
    "android",
    "excel",
    "r",
    "docker",
    "powerbi",
    "fastapi",
    "openai-api",
]


def render_chart(figure, **kwargs):
    """Keep axes, legends and hover labels legible in light or dark app themes."""
    figure.update_layout(
        template="plotly_white",
        font=dict(color="#18334A", size=13),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        legend=dict(font=dict(color="#18334A")),
        hoverlabel=dict(bgcolor="#FFFFFF", font=dict(color="#18334A")),
    )
    figure.update_xaxes(color="#18334A", gridcolor="#E5E7EB", automargin=True)
    figure.update_yaxes(color="#18334A", gridcolor="#E5E7EB", automargin=True)
    # Disable Streamlit's theme injection so explicit white figures stay readable.
    return st.plotly_chart(figure, theme=None, **kwargs)


def load_data(filename: str) -> pd.DataFrame:
    """Load a CSV file from dashboard/data/ with caching."""
    filepath = DATA_DIR / filename
    if not filepath.exists():
        raise FileNotFoundError(f"Dashboard data file not found: {filename}")
    return _read_csv(str(filepath), filepath.stat().st_mtime_ns)


@st.cache_data
def _read_csv(path: str, modification_ns: int) -> pd.DataFrame:
    """Invalidate cached data whenever the published artifact changes."""
    return pd.read_csv(path)


def filter_observations(df, date_column, filters, *, monthly=False, tags=None):
    """Intersect tag, date and pre/transition/post selections. Never sum tags."""
    out = df.copy()
    dates = pd.to_datetime(out[date_column])
    start, end = pd.Timestamp(filters['start_date']), pd.Timestamp(filters['end_date'])
    if monthly:
        start, end = start.to_period('M').start_time, end.to_period('M').end_time
    mask = dates.between(start, end)
    period = filters['period']
    if period == 'pre': mask &= dates < '2022-11-01'
    elif period == 'transition': mask &= dates.between('2022-11-01', '2022-12-31')
    elif period == 'post': mask &= dates >= '2023-01-01'
    if 'tag' in out:
        mask &= out['tag'].isin(tags or filters['tags'])
    return out.loc[mask].copy()


def focus_tag(filters, key, label='Focus Technology Tag:'):
    """Carry the focused technology across pages; reset on sidebar changes."""
    signature = tuple(filters['tags'])
    if st.session_state.get('_focus_global_signature') != signature:
        st.session_state['_focus_tag'] = filters['tags'][0]
        st.session_state['_focus_global_signature'] = signature
    focused = st.session_state.get('_focus_tag', filters['tags'][0])
    if st.session_state.get(key) != focused:
        st.session_state[key] = focused

    def remember_focus():
        st.session_state['_focus_tag'] = st.session_state[key]

    return st.selectbox(label, ALL_TAGS, key=key, on_change=remember_focus)


def render_sidebar(*, observations=True, log=True, events=True):
    """Render the global persistent sidebar across all dashboard pages."""
    with st.sidebar:
        st.header("Global Controls")

        # Session state defaults
        if "selected_tags" not in st.session_state:
            st.session_state["selected_tags"] = ["ALL"]
        if "period" not in st.session_state:
            st.session_state["period"] = "all"
        if "show_events" not in st.session_state:
            st.session_state["show_events"] = True
        if "log_scale" not in st.session_state:
            st.session_state["log_scale"] = False

        # Tag multi-select
        selected_tags = st.multiselect(
            "Select Technology Tag(s):",
            options=ALL_TAGS,
            default=st.session_state["selected_tags"],
            key="tag_selector",
        )
        if not selected_tags:
            selected_tags = ["ALL"]
        st.session_state["selected_tags"] = selected_tags

        # Period filter
        period_choice = st.radio(
            "Observation Period:",
            options=["all", "pre", "transition", "post"],
            format_func=lambda x: {
                "all": "All (2019 - 2026)",
                "pre": "Pre-AI (2019-01 to 2022-10)",
                "transition": "Transition (2022-11 to 2022-12)",
                "post": "Post-AI (2023-01 to 2026-08)",
            }[x],
            index=["all", "pre", "transition", "post"].index(st.session_state["period"]),
            key="period_radio",
            disabled=not observations,
        )
        st.session_state["period"] = period_choice

        # Date range picker based on series_long
        series_df = load_data("series_long.csv")
        min_date = pd.to_datetime(series_df["week_start"]).min().date()
        max_date = pd.to_datetime(series_df["week_start"]).max().date()

        date_range = st.date_input(
            "Date Range Window:",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            key="date_range_picker",
            disabled=not observations,
        )
        if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
            start_date, end_date = date_range
        else:
            start_date, end_date = min_date, max_date

        st.session_state["start_date"] = start_date
        st.session_state["end_date"] = end_date

        st.caption("Monthly tables include whole months that overlap the date window. Weekly charts use week-start dates.")

        # Display toggles
        col1, col2 = st.columns(2)
        with col1:
            show_events = st.checkbox(
                "Event Markers",
                value=st.session_state["show_events"],
                key="events_checkbox",
                disabled=not events,
            )
            st.session_state["show_events"] = show_events
        with col2:
            log_scale = st.checkbox(
                "Log Scale",
                value=st.session_state["log_scale"],
                key="log_scale_checkbox",
                disabled=not log,
            )
            st.session_state["log_scale"] = log_scale

        st.divider()

        # Download filtered data button
        filtered_df = filter_observations(series_df, 'week_start', {
            'tags': selected_tags, 'period': period_choice if observations else 'all',
            'start_date': start_date if observations else min_date,
            'end_date': end_date if observations else max_date})
        csv_data = filtered_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Filtered Data (CSV)",
            data=csv_data,
            file_name="stackoverflow_filtered_series.csv",
            mime="text/csv",
            width='stretch',
        )

        # About data and license panel
        with st.expander("About Data & Licence", expanded=False):
            st.markdown(
                """
                **Licence & Provenance**
                - Stack Overflow user contributions are licensed under **CC BY-SA 4.0**.
                - Data collected via Stack Exchange API 2.3; historic records have sampling weights.
                - Question references display **titles only**, hyperlinked directly to canonical URLs: `https://stackoverflow.com/q/<id>`.
                - This dashboard serves aggregated tables and title-only examples; bodies and user identifiers are excluded from dashboard exports.
                """
            )

        return {
            "tags": selected_tags,
            "period": period_choice,
            "start_date": start_date,
            "end_date": end_date,
            "show_events": show_events,
            "log_scale": log_scale,
        }
