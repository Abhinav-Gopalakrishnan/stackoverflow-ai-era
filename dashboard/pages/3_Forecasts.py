"""Page 3: Forecasts to February 2027."""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

_dashboard_dir = Path(__file__).resolve().parent.parent
_repo_root = _dashboard_dir.parent
for _p in (str(_dashboard_dir), str(_repo_root)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from common import ALL_TAGS, TAG_COLORS, load_data, render_sidebar
except ImportError:
    from dashboard.common import ALL_TAGS, TAG_COLORS, load_data, render_sidebar

st.set_page_config(
    page_title="Page 3: Forecasts to Feb 2027",
    page_icon="🔮",
    layout="wide",
)

# Render global sidebar
filters = render_sidebar()

st.title("Page 3: Demand Forecasts to February 2027")
st.markdown(
    """
    Prospective 26-week probabilistic forecasts across models (ETS, SARIMAX, Baselines),
    out-of-sample backtest evaluations on matched origins, and tag half-life classifications.
    """
)

# Load data
series_df = load_data("series_long.csv")
forecasts_df = load_data("forecasts_26w.csv")
tag_classes_df = load_data("tag_classes.csv")
backtest_summary = load_data("backtest_summary_matched.csv")
backtest_metrics = load_data("backtest_metrics_matched.csv")
captions_df = load_data("ts_captions.csv")

# Tag selector
default_tag = (
    st.session_state["selected_tags"][0]
    if st.session_state.get("selected_tags") and st.session_state["selected_tags"][0] in ALL_TAGS
    else "ALL"
)
col_tag, col_badge = st.columns([2, 3])
with col_tag:
    selected_tag = st.selectbox(
        "Select Technology Tag:",
        options=ALL_TAGS,
        index=ALL_TAGS.index(default_tag),
        key="page3_tag_selector",
    )
    if selected_tag not in st.session_state["selected_tags"]:
        st.session_state["selected_tags"] = [selected_tag]

# Tag class badge
tag_class_row = tag_classes_df[tag_classes_df["tag"] == selected_tag]
with col_badge:
    if not tag_class_row.empty:
        r = tag_class_row.iloc[0]
        st.markdown(f"**Trajectory Classification for `{selected_tag}`:**")
        b1, b2, b3 = st.columns(3)
        b1.info(f"Class: **{r['forecast_class'].title()}**")
        b2.metric("26w Forecast Drift", f"{r['change_26w_pct']:+.1f}%")
        half_life = f"{r['half_life_weeks']:.1f} wks" if not np.isnan(r["half_life_weeks"]) else "Indeterminate"
        b3.metric("Half-Life", half_life)

st.divider()

# Controls row: model picker, horizon slider, band toggle
tag_forecasts = forecasts_df[forecasts_df["tag"] == selected_tag]
available_models = sorted(tag_forecasts["model"].unique().tolist())
default_model = "sarimax" if "sarimax" in available_models else available_models[0]

c_model, c_horiz, c_bands = st.columns([2, 2, 2])
with c_model:
    model_choice = st.selectbox(
        "Forecasting Model:",
        options=available_models,
        index=available_models.index(default_model),
    )
with c_horiz:
    horizon_max = st.slider("Forecast Horizon (Weeks to Feb 2027):", min_value=1, max_value=26, value=26)
with c_bands:
    show_intervals = st.multiselect(
        "Prediction Intervals:",
        options=["80% Band", "95% Band"],
        default=["80% Band", "95% Band"],
    )

# Filter forecasts
selected_fc = tag_forecasts[
    (tag_forecasts["model"] == model_choice)
    & (tag_forecasts["horizon"] <= horizon_max)
].sort_values("week_start")

# Historical series
hist_series = series_df[series_df["tag"] == selected_tag].sort_values("week_start")
# Limit history to recent 104 weeks (2 years) for clear fan visualization
hist_recent = hist_series.tail(104)

# Dynamic title
if not selected_fc.empty:
    end_val = selected_fc["pred"].iloc[-1]
    start_val = hist_series["count"].iloc[-1]
    chg_pct = ((end_val - start_val) / start_val) * 100.0 if start_val > 0 else 0.0
    direction = "decline" if chg_pct < 0 else "increase"
    takeaway_title = (
        f"{model_choice.upper()} 26-Week Forecast for {selected_tag}: "
        f"{abs(chg_pct):.1f}% {direction} to February 2027 "
        f"({int(round(end_val))} questions vs {int(round(start_val))} observed)"
    )
else:
    takeaway_title = f"Demand Forecast for {selected_tag}"

# Build Fan Chart
fig_fc = go.Figure()

# History
tag_color = TAG_COLORS.get(selected_tag, "#1D4E89")
fig_fc.add_trace(
    go.Scatter(
        x=hist_recent["week_start"],
        y=hist_recent["count"],
        mode="lines",
        name="Observed History",
        line=dict(color=tag_color, width=2.2),
    )
)

# 95% Confidence Band
if "95% Band" in show_intervals and not selected_fc.empty:
    fig_fc.add_trace(
        go.Scatter(
            x=list(selected_fc["week_start"]) + list(selected_fc["week_start"])[::-1],
            y=list(selected_fc["upper95"]) + list(selected_fc["lower95"])[::-1],
            fill="toself",
            fillcolor="rgba(220, 38, 38, 0.10)",
            line=dict(color="rgba(255,255,255,0)"),
            hoverinfo="skip",
            name="95% Interval",
        )
    )

# 80% Confidence Band
if "80% Band" in show_intervals and not selected_fc.empty:
    fig_fc.add_trace(
        go.Scatter(
            x=list(selected_fc["week_start"]) + list(selected_fc["week_start"])[::-1],
            y=list(selected_fc["upper80"]) + list(selected_fc["lower80"])[::-1],
            fill="toself",
            fillcolor="rgba(220, 38, 38, 0.20)",
            line=dict(color="rgba(255,255,255,0)"),
            hoverinfo="skip",
            name="80% Interval",
        )
    )

# Point Forecast Line
if not selected_fc.empty:
    # Connect last history point to first forecast point
    conn_x = [hist_recent["week_start"].iloc[-1]] + list(selected_fc["week_start"])
    conn_y = [hist_recent["count"].iloc[-1]] + list(selected_fc["pred"])
    fig_fc.add_trace(
        go.Scatter(
            x=conn_x,
            y=conn_y,
            mode="lines+markers",
            name=f"Forecast ({model_choice})",
            line=dict(color="#DC2626", width=2.4, dash="dash"),
            marker=dict(size=4),
        )
    )

fig_fc.update_layout(
    title=dict(text=f"<b>{takeaway_title}</b>", font=dict(size=15, color="#1F2937")),
    xaxis=dict(title="Week", showgrid=True, gridcolor="#E5E7EB"),
    yaxis=dict(title="Weekly Questions", showgrid=True, gridcolor="#E5E7EB"),
    height=480,
    plot_bgcolor="#FFFFFF",
    paper_bgcolor="#FFFFFF",
    legend=dict(orientation="h", y=1.05, x=1, xanchor="right"),
    margin=dict(l=40, r=40, t=60, b=40),
)

st.plotly_chart(fig_fc, use_container_width=True)

# Owner caption from ts_captions.csv
fan_caption = captions_df[captions_df["chart"] == "Forecast fan"]
if not fan_caption.empty:
    row = fan_caption.iloc[0]
    st.caption(f"**Takeaway:** {row['takeaway']} *Caveat:* {row['caveat']}")
else:
    st.caption("Forecast horizons extend through February 23, 2027. Prediction intervals are uncertain.")

st.divider()

# -------------------------------------------------------------
# Backtest Evaluation Table (Matched Origins)
# -------------------------------------------------------------
st.subheader("Backtest Performance on Matched Origins (26-Week Horizon)")

tag_bm = backtest_metrics[
    (backtest_metrics["tag"] == selected_tag)
    & (backtest_metrics["horizon"] == 26)
].copy()

if not tag_bm.empty:
    display_bm = tag_bm[["model", "mase", "smape", "skill_vs_naive", "coverage80", "coverage95"]].copy()
    display_bm["mase"] = display_bm["mase"].round(3)
    display_bm["smape"] = (display_bm["smape"] * 100).round(1).astype(str) + "%"
    display_bm["skill_vs_naive"] = (display_bm["skill_vs_naive"] * 100).round(1).astype(str) + "%"
    display_bm["coverage80"] = (display_bm["coverage80"] * 100).round(1).astype(str) + "%"
    display_bm["coverage95"] = (display_bm["coverage95"] * 100).round(1).astype(str) + "%"
    st.dataframe(display_bm, use_container_width=True)
else:
    st.info("Global matched summary across 14 series:")
    st.dataframe(backtest_summary, use_container_width=True)

# Owner caption for backtest skill
skill_caption = captions_df[captions_df["chart"] == "Backtest skill"]
if not skill_caption.empty:
    row = skill_caption.iloc[0]
    st.caption(f"**Backtest Note:** {row['takeaway']} *Note:* {row['caveat']}")
