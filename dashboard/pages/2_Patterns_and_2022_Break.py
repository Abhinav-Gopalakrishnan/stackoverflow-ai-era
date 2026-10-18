"""Page 2: Patterns and the 2022 Break."""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

_dashboard_dir = Path(__file__).resolve().parent.parent
_repo_root = _dashboard_dir.parent
for _p in (str(_dashboard_dir), str(_repo_root)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from common import filter_observations, focus_tag, ALL_TAGS, TAG_COLORS, load_data, render_sidebar
except ImportError:
    from dashboard.common import filter_observations, focus_tag, ALL_TAGS, TAG_COLORS, load_data, render_sidebar

st.set_page_config(
    page_title="Page 2: Patterns & 2022 Break",
    page_icon="📈",
    layout="wide",
)

# Render global sidebar
filters = render_sidebar(log=False)

st.title("Page 2: Time Series Patterns & 2022 Structural Break")
st.markdown(
    """
    Decomposition of question series into underlying trend and seasonal cycles,
    unsupervised changepoint detection, and observational Interrupted Time Series (ITS) modeling.
    """
)

# Load data
stl_df = load_data("stl_components.csv")
cps_df = load_data("changepoints.csv")
its_df = load_data("its_results.csv")
events_df = load_data("event_list.csv")

# Tag selector for deep-dive
selected_tag = focus_tag(filters, 'page2_tag_selector')
st.caption("Charts show the selected window of full-series STL and PELT fits. ITS statistics always use all 400 weeks; changing the window does not refit the model.")
tag_color = TAG_COLORS.get(selected_tag, "#1D4E89")

# -------------------------------------------------------------
# 1. STL Decomposition (Trend, Seasonal, Remainder)
# -------------------------------------------------------------
st.subheader("1. STL Loess Decomposition (Log Scale)")

stl_tag = filter_observations(stl_df, "week_start", filters, tags=[selected_tag]).sort_values("week_start")
stl_tag["week_start_dt"] = pd.to_datetime(stl_tag["week_start"])

stl_title = f"{selected_tag}: full-series STL components in the selected window"

fig_stl = make_subplots(
    rows=3,
    cols=1,
    shared_xaxes=True,
    vertical_spacing=0.08,
    subplot_titles=["Trend Component (Loess)", "Seasonal Component (Annual)", "Residual Noise"],
)

fig_stl.add_trace(
    go.Scatter(
        x=stl_tag["week_start"],
        y=stl_tag["trend"],
        mode="lines",
        name="Trend",
        line=dict(color=tag_color, width=2.2),
    ),
    row=1,
    col=1,
)

fig_stl.add_trace(
    go.Scatter(
        x=stl_tag["week_start"],
        y=stl_tag["seasonal"],
        mode="lines",
        name="Seasonal",
        line=dict(color="#059669", width=1.5),
    ),
    row=2,
    col=1,
)

fig_stl.add_trace(
    go.Scatter(
        x=stl_tag["week_start"],
        y=stl_tag["resid"],
        mode="lines",
        name="Residual",
        line=dict(color="#9CA3AF", width=1.2),
    ),
    row=3,
    col=1,
)

# Mark 2022-11 break on all subplots
for row_idx in ((1, 2, 3) if filters["show_events"] else ()):
    fig_stl.add_vline(
        x="2022-11-29",
        line_width=1.2,
        line_dash="dash",
        line_color="#DC2626",
        row=row_idx,
        col=1,
    )

fig_stl.update_layout(
    title=dict(text=f"<b>{stl_title}</b>", font=dict(size=15, color="#1F2937")),
    height=560,
    plot_bgcolor="#FFFFFF",
    paper_bgcolor="#FFFFFF",
    showlegend=False,
    margin=dict(l=40, r=40, t=70, b=40),
)
fig_stl.update_xaxes(showgrid=True, gridcolor="#E5E7EB")
fig_stl.update_yaxes(showgrid=True, gridcolor="#E5E7EB")

st.plotly_chart(fig_stl, width='stretch')

st.caption(
    "Full-series STL separates log1p counts into smooth trend, "
    "regular calendar seasonality, and remaining residual variation (not assumed white noise). "
    "Vertical red dashed line denotes November 2022."
)

st.divider()

# -------------------------------------------------------------
# 2. Detected Changepoints vs Event Milestones
# -------------------------------------------------------------
st.subheader("2. Unsupervised Changepoints & Milestone Alignment")

tag_cps = filter_observations(cps_df, "week_start", filters, tags=[selected_tag]).sort_values("week_start")
n_cps = len(tag_cps)
cps_near_event = tag_cps[tag_cps["within_4_weeks_of_event"] == True]

cp_title = (
    f"Pelt Changepoints for {selected_tag}: {len(cps_near_event)} of {n_cps} break points "
    f"detected within 4 weeks of major generative AI releases"
)

fig_cp = go.Figure()

# Plot STL trend as reference
fig_cp.add_trace(
    go.Scatter(
        x=stl_tag["week_start"],
        y=stl_tag["trend"],
        mode="lines",
        name="Underlying Trend",
        line=dict(color=tag_color, width=2.0),
    )
)

# Mark detected changepoints
for _, cp in tag_cps.iterrows():
    cp_date = cp["week_start"]
    near = cp["within_4_weeks_of_event"]
    fig_cp.add_vline(
        x=cp_date,
        line_width=1.5,
        line_dash="dot",
        line_color="#7C3AED" if near else "#9CA3AF",
        annotation_text="Break" if not near else f"Break: {cp['nearest_event_name']}",
        annotation_position="top left",
        annotation=dict(font_size=9, font_color="#7C3AED" if near else "#4B5563"),
    )

if filters["show_events"]:
    # Mark ChatGPT release in red
    fig_cp.add_vline(
        x="2022-11-30",
        line_width=2.0,
        line_dash="dash",
        line_color="#DC2626",
        annotation_text="ChatGPT Launch (2022-11-30)",
        annotation_position="bottom right",
        annotation=dict(font_size=10, font_color="#DC2626"),
    )

fig_cp.update_layout(
    title=dict(text=f"<b>{cp_title}</b>", font=dict(size=15, color="#1F2937")),
    xaxis=dict(title="Week", showgrid=True, gridcolor="#E5E7EB"),
    yaxis=dict(title="Log Trend", showgrid=True, gridcolor="#E5E7EB"),
    height=400,
    plot_bgcolor="#FFFFFF",
    paper_bgcolor="#FFFFFF",
    margin=dict(l=40, r=40, t=60, b=40),
)
st.plotly_chart(fig_cp, width='stretch')

st.caption(
    "How to read changepoints: Ruptures Pelt algorithm detects penalised shifts in mean log volume (not significance tests). "
    "Purple dotted lines flag changepoints occurring within 4 weeks of documented AI industry milestones."
)

st.divider()

# -------------------------------------------------------------
# 3. Interrupted Time Series (ITS) Model & Placebo Check
# -------------------------------------------------------------
st.subheader("3. Interrupted Time Series (ITS) and Placebo Sensitivity Check")

tag_its = its_df[its_df["tag"] == selected_tag]
if not tag_its.empty:
    its_row = tag_its.iloc[0]
    lvl_chg = its_row["level_change_pct"]
    slp_chg = its_row["slope_change_pct"]
    lvl_p = its_row["level_p"]
    slp_p = its_row["slope_p"]
    status_desc = its_row["status"]
    exceeds_placebo = its_row["effect_exceeds_placebo"]

    its_title = (
        f"ITS Regression for {selected_tag}: {slp_chg:+.1f}% slope change per week "
        f"(p={slp_p:.3f}), status: {status_desc}"
    )

    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.metric(
            "Immediate Level Shift (Beta 2)",
            f"{lvl_chg:+.1f}%",
            help=f"95% CI: [{its_row['level_ci_lo']:.2f}, {its_row['level_ci_hi']:.2f}], p={lvl_p:.4f}",
        )
    with col_m2:
        st.metric(
            "Weekly Growth-Rate Shift (Beta 3)",
            f"{slp_chg:+.1f}%",
            delta=f"{slp_chg:+.1f}%",
            delta_color="inverse",
            help=f"95% CI: [{its_row['slope_ci_lo']:.2f}, {its_row['slope_ci_hi']:.2f}], p={slp_p:.4f}",
        )
    with col_m3:
        st.metric(
            "Empirical Model Status",
            status_desc.title(),
            delta="Significant" if slp_p < 0.05 else "Non-significant",
        )

    # Placebo check toggle
    show_placebo = st.checkbox("Show Placebo Counterfactual Test (False Break at 2021-11)", value=False)

    if show_placebo:
        st.info(
            f"**Placebo Test Results (Break Date: {its_row['placebo_break_date']}):**\n\n"
            f"- Placebo Level Change: {its_row['placebo_level_change']:.3f} (p={its_row['placebo_level_p']:.3f})\n"
            f"- Placebo Slope Change: {its_row['placebo_slope_change']:.3f} (p={its_row['placebo_slope_p']:.3f})\n"
            f"- **Actual Intervention Exceeds Placebo:** `{'YES (larger absolute slope effect)' if exceeds_placebo else 'NO (Indeterminate)'}`\n\n"
            f"*A single placebo is a sensitivity check; it does not establish causal identification.*"
        )
else:
    st.warning(f"No ITS results found for tag '{selected_tag}'.")
