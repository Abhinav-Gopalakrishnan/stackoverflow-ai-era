"""Shared components, loaders, and state management for the Streamlit dashboard."""

from pathlib import Path
import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).resolve().parent / "data"

# Academic & Publication Palette for 13 study tags + ALL
TAG_COLORS = {
    "ALL": "#1D4E89",          # Deep Academic Navy
    "python": "#3572A5",       # Python Blue
    "javascript": "#F7DF1E",   # JavaScript Gold
    "java": "#B07219",         # Java Warm Coffee
    "sql": "#E38C00",          # SQL Burnt Orange
    "pandas": "#150458",       # Pandas Dark Indigo
    "reactjs": "#61DAFB",      # React Cyan
    "android": "#3DDC84",      # Android Green
    "excel": "#107C41",        # Excel Forest Green
    "r": "#198CE7",            # R Blue
    "docker": "#2496ED",       # Docker Blue
    "powerbi": "#F2C811",      # PowerBI Yellow
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


@st.cache_data
def load_data(filename: str) -> pd.DataFrame:
    """Load a CSV file from dashboard/data/ with caching."""
    filepath = DATA_DIR / filename
    if not filepath.exists():
        raise FileNotFoundError(f"Dashboard data file not found: {filename}")
    return pd.read_csv(filepath)


def render_sidebar():
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
        )
        if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
            start_date, end_date = date_range
        else:
            start_date, end_date = min_date, max_date

        st.session_state["start_date"] = start_date
        st.session_state["end_date"] = end_date

        # Display toggles
        col1, col2 = st.columns(2)
        with col1:
            show_events = st.checkbox(
                "Event Markers",
                value=st.session_state["show_events"],
                key="events_checkbox",
            )
            st.session_state["show_events"] = show_events
        with col2:
            log_scale = st.checkbox(
                "Log Scale",
                value=st.session_state["log_scale"],
                key="log_scale_checkbox",
            )
            st.session_state["log_scale"] = log_scale

        st.divider()

        # Download filtered data button
        filtered_df = series_df[
            (series_df["tag"].isin(selected_tags))
            & (pd.to_datetime(series_df["week_start"]).dt.date >= start_date)
            & (pd.to_datetime(series_df["week_start"]).dt.date <= end_date)
        ]
        csv_data = filtered_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Filtered Data (CSV)",
            data=csv_data,
            file_name="stackoverflow_filtered_series.csv",
            mime="text/csv",
            use_container_width=True,
        )

        # About data and license panel
        with st.expander("About Data & Licence", expanded=False):
            st.markdown(
                """
                **Licence & Provenance**
                - Stack Overflow user contributions are licensed under **CC BY-SA 4.0**.
                - Data collected via Stack Exchange API 2.3 and BigQuery public datasets.
                - Question references display **titles only**, hyperlinked directly to canonical URLs: `https://stackoverflow.com/q/<id>`.
                - No question bodies, code text, or user identifiers are retained or served.
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
