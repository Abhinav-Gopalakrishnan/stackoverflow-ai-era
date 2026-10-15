import sys
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

_dashboard_dir = Path(__file__).resolve().parent
_repo_root = _dashboard_dir.parent
for _p in (str(_dashboard_dir), str(_repo_root)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from common import TAG_COLORS, load_data, render_sidebar
except ImportError:
    from dashboard.common import TAG_COLORS, load_data, render_sidebar

st.set_page_config(
    page_title="Stack Overflow in the AI Era: Overview",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Render global sidebar filters
filters = render_sidebar()

st.title("Stack Overflow in the AI Era: Executive Overview")
st.markdown(
    """
    Empirical investigation of question-resolution dynamics, time-series break patterns,
    and text complexity across **14 technology series (2019–2026)**.
    """
)

# Load core datasets
series_df = load_data("series_long.csv")
rates_df = load_data("monthly_rates_masked.csv")
events_df = load_data("event_list.csv")

# Filter series by selected tags and date range
selected_tags = filters["tags"]
start_date = pd.to_datetime(filters["start_date"])
end_date = pd.to_datetime(filters["end_date"])

series_filtered = series_df[
    (series_df["tag"].isin(selected_tags))
    & (pd.to_datetime(series_df["week_start"]) >= start_date)
    & (pd.to_datetime(series_df["week_start"]) <= end_date)
].copy()
series_filtered["week_start_dt"] = pd.to_datetime(series_filtered["week_start"])

# -------------------------------------------------------------
# KPI Computations (computed dynamically, never hard-coded)
# -------------------------------------------------------------
# 1. Weekly volume baseline (2022 pre-ChatGPT: Jan - Oct 2022) vs recent (last 8 weeks of 2025/2026)
pre_2022_mask = (
    (series_filtered["week_start_dt"] >= "2022-01-01")
    & (series_filtered["week_start_dt"] < "2022-11-01")
)
pre_weekly_avg = (
    series_filtered[pre_2022_mask].groupby("week_start")["count"].sum().mean()
    if not series_filtered[pre_2022_mask].empty
    else np.nan
)

# Recent weekly average (last 8 recorded weeks)
unique_weeks = sorted(series_filtered["week_start"].unique())
recent_weeks = unique_weeks[-8:] if len(unique_weeks) >= 8 else unique_weeks
recent_weekly_avg = (
    series_filtered[series_filtered["week_start"].isin(recent_weeks)]
    .groupby("week_start")["count"]
    .sum()
    .mean()
    if recent_weeks
    else np.nan
)

pct_volume_change = (
    ((recent_weekly_avg - pre_weekly_avg) / pre_weekly_avg) * 100.0
    if (pre_weekly_avg and not np.isnan(pre_weekly_avg) and pre_weekly_avg > 0)
    else 0.0
)

# 2. Resolution rate: pre (<2022-11) vs post (>=2023-01), excluding low_sample
rates_tag = rates_df[rates_df["tag"].isin(selected_tags)].copy()
# Strict validity rule: omit low_sample months from conclusions
valid_rates = rates_tag[~rates_tag["low_sample"]].copy()

pre_rates = valid_rates[valid_rates["month"] < "2022-11"]
post_rates = valid_rates[valid_rates["month"] >= "2023-01"]

pre_resolved = (
    (pre_rates["resolved_rate_7d"] * pre_rates["est_questions"]).sum()
    / pre_rates["est_questions"].sum()
    if not pre_rates.empty and pre_rates["est_questions"].sum() > 0
    else np.nan
)
post_resolved = (
    (post_rates["resolved_rate_7d"] * post_rates["est_questions"]).sum()
    / post_rates["est_questions"].sum()
    if not post_rates.empty and post_rates["est_questions"].sum() > 0
    else np.nan
)
resolved_delta = (
    (post_resolved - pre_resolved) * 100.0
    if (not np.isnan(pre_resolved) and not np.isnan(post_resolved))
    else np.nan
)

# 3. Median hours to accept
pre_hours = pre_rates["median_hours_to_accept"].median() if not pre_rates.empty else np.nan
post_hours = post_rates["median_hours_to_accept"].median() if not post_rates.empty else np.nan

# -------------------------------------------------------------
# 4 KPI Tiles
# -------------------------------------------------------------
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.metric(
        label="Recent Weekly Questions",
        value=f"{int(recent_weekly_avg):,}" if not np.isnan(recent_weekly_avg) else "N/A",
        help="Mean weekly questions across selected tag(s) over the most recent 8 weeks.",
    )

with kpi2:
    st.metric(
        label="Volume Shift vs 2022 Pre-AI",
        value=f"{pct_volume_change:+.1f}%",
        delta=f"{pct_volume_change:.1f}%",
        delta_color="normal",
        help="Percentage change in weekly question volume relative to 2022 pre-ChatGPT baseline.",
    )

with kpi3:
    pre_str = f"{pre_resolved * 100:.1f}%" if not np.isnan(pre_resolved) else "N/A"
    post_str = f"{post_resolved * 100:.1f}%" if not np.isnan(post_resolved) else "N/A"
    st.metric(
        label="Resolved Rate (Pre -> Post)",
        value=f"{pre_str} -> {post_str}",
        delta=f"{resolved_delta:+.1f} pp" if not np.isnan(resolved_delta) else "N/A",
        delta_color="normal",
        help="Weighted 7-day question resolution rate before vs after November 2022 (low-sample months excluded).",
    )

with kpi4:
    pre_h_str = f"{pre_hours:.1f}h" if not np.isnan(pre_hours) else "N/A"
    post_h_str = f"{post_hours:.1f}h" if not np.isnan(post_hours) else "N/A"
    st.metric(
        label="Median Hours to Accept",
        value=f"{pre_h_str} -> {post_h_str}",
        help="Median hours elapsed from question creation to answer acceptance.",
    )

st.divider()

# -------------------------------------------------------------
# Plotly Weekly Volume Chart with Shading & Event Markers
# -------------------------------------------------------------
# Dynamic takeaway title strictly observing wording rules
direction = "decline" if pct_volume_change < 0 else "increase"
takeaway_title = (
    f"Weekly Question Volume: {abs(pct_volume_change):.1f}% {direction} "
    f"consistent with post-2022 AI adoption"
)

fig = go.Figure()

# Add line per selected tag
for tag in selected_tags:
    df_tag = series_filtered[series_filtered["tag"] == tag].sort_values("week_start")
    y_values = df_tag["count"] if not filters["log_scale"] else df_tag["log_count"]
    color = TAG_COLORS.get(tag, "#6B7280")

    fig.add_trace(
        go.Scatter(
            x=df_tag["week_start"],
            y=y_values,
            mode="lines",
            name=tag,
            line=dict(color=color, width=2.4 if tag == "ALL" else 1.8),
            hovertemplate="<b>%{x}</b><br>Tag: " + tag + "<br>Count: %{y:,}<extra></extra>",
        )
    )

# Pre / Transition / Post period shading
fig.add_vrect(
    x0="2019-01-01",
    x1="2022-10-31",
    fillcolor="rgba(30, 144, 255, 0.04)",
    layer="below",
    line_width=0,
    annotation_text="Pre-AI Era",
    annotation_position="top left",
    annotation=dict(font_size=11, font_color="#4B5563"),
)
fig.add_vrect(
    x0="2022-11-01",
    x1="2022-12-31",
    fillcolor="rgba(245, 158, 11, 0.12)",
    layer="below",
    line_width=0,
    annotation_text="Transition",
    annotation_position="top",
    annotation=dict(font_size=11, font_color="#D97706"),
)
fig.add_vrect(
    x0="2023-01-01",
    x1="2026-08-31",
    fillcolor="rgba(220, 38, 38, 0.04)",
    layer="below",
    line_width=0,
    annotation_text="Post-AI Adoption",
    annotation_position="top right",
    annotation=dict(font_size=11, font_color="#991B1B"),
)

# Event markers from event_list.csv
if filters["show_events"]:
    for _, event in events_df.iterrows():
        ev_date = event["date"]
        ev_name = event["event_name"]
        fig.add_vline(
            x=ev_date,
            line_width=1.2,
            line_dash="dash",
            line_color="#DC2626",
            annotation_text=ev_name,
            annotation_position="top left",
            annotation=dict(font_size=9, font_color="#DC2626"),
        )

y_axis_title = "Log(Questions + 1)" if filters["log_scale"] else "Weekly Questions"
fig.update_layout(
    title=dict(
        text=f"<b>{takeaway_title}</b>",
        font=dict(size=16, color="#1F2937"),
    ),
    xaxis=dict(title="Week", showgrid=True, gridcolor="#E5E7EB"),
    yaxis=dict(title=y_axis_title, showgrid=True, gridcolor="#E5E7EB"),
    hovermode="x unified",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
    ),
    margin=dict(l=40, r=40, t=80, b=40),
    height=480,
    plot_bgcolor="#FFFFFF",
    paper_bgcolor="#FFFFFF",
)

st.plotly_chart(fig, use_container_width=True)

st.caption(
    "How to read this chart: Weekly question volume from 2019 through 2026. "
    "Vertical dashed lines indicate key generative AI release milestones. "
    "The sustained deceleration post-November 2022 is consistent with developer substitution to LLMs; "
    "effects are not causally attributed to any single event."
)

# -------------------------------------------------------------
# Monthly Rates Context Table with low_sample indication
# -------------------------------------------------------------
with st.expander("Monthly Resolution Rates & Sample Quality Inspection"):
    st.markdown(
        "Monthly aggregated rates across selected tags. "
        "Rows flagged with `low_sample = True` (fewer than 30 collected questions in that tag-month) "
        "are displayed with warning indicators and excluded from empirical takeaways."
    )
    display_rates = rates_tag.sort_values(["tag", "month"], ascending=[True, False]).copy()
    display_rates["resolved_rate_7d"] = (display_rates["resolved_rate_7d"] * 100).round(1).astype(str) + "%"
    display_rates["answered_rate_7d"] = (display_rates["answered_rate_7d"] * 100).round(1).astype(str) + "%"
    st.dataframe(
        display_rates[[
            "tag",
            "month",
            "n_sampled",
            "est_questions",
            "resolved_rate_7d",
            "answered_rate_7d",
            "median_hours_to_accept",
            "low_sample",
        ]],
        use_container_width=True,
    )
