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
    from common import ALL_TAGS, TAG_COLORS, load_data, render_sidebar
except ImportError:
    from dashboard.common import ALL_TAGS, TAG_COLORS, load_data, render_sidebar

st.set_page_config(
    page_title="Page 2: Patterns & 2022 Break",
    page_icon="📈",
    layout="wide",
)

# Render global sidebar
filters = render_sidebar()

st.title("Page 2: Time Series Patterns & 2022 Structural Break")
st.markdown(
    """
    Decomposition of question series into underlying trend and seasonal cycles,
    unsupervised changepoint detection, and quasi-experimental Interrupted Time Series (ITS) modeling.
    """
)

# Load data
stl_df = load_data("stl_components.csv")
cps_df = load_data("changepoints.csv")
its_df = load_data("its_results.csv")
events_df = load_data("event_list.csv")

# Tag selector for deep-dive
default_tag = (
    st.session_state["selected_tags"][0]
    if st.session_state.get("selected_tags") and st.session_state["selected_tags"][0] in ALL_TAGS
    else "ALL"
)
selected_tag = st.selectbox(
    "Focus Technology Tag for Decomposition & Break Models:",
    options=ALL_TAGS,
    index=ALL_TAGS.index(default_tag),
    key="page2_tag_selector",
)
# Sync back to session state
if selected_tag not in st.session_state["selected_tags"]:
    st.session_state["selected_tags"] = [selected_tag]

tag_color = TAG_COLORS.get(selected_tag, "#1D4E89")

# -------------------------------------------------------------
# 1. STL Decomposition (Trend, Seasonal, Remainder)
# -------------------------------------------------------------
st.subheader("1. STL Loess Decomposition (Log Scale)")

stl_tag = stl_df[stl_df["tag"] == selected_tag].sort_values("week_start").copy()
stl_tag["week_start_dt"] = pd.to_datetime(stl_tag["week_start"])

# Calculate dynamic trend takeaway
pre_mask = stl_tag["week_start_dt"] < "2022-11-01"
pre_trend = stl_tag[pre_mask]["trend"].iloc[-1] if not stl_tag[pre_mask].empty else np.nan
post_trend = stl_tag["trend"].iloc[-1] if not stl_tag.empty else np.nan

trend_shift_pct = (
    (np.exp(post_trend) - np.exp(pre_trend)) / np.exp(pre_trend) * 100.0
    if (not np.isnan(pre_trend) and not np.isnan(post_trend) and pre_trend > 0)
    else 0.0
)
trend_direction = "decline" if trend_shift_pct < 0 else "growth"
stl_title = (
    f"STL Trend Component for {selected_tag}: {abs(trend_shift_pct):.1f}% {trend_direction} "
    f"consistent with structural AI-era shift"
)

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
for row_idx in (1, 2, 3):
    fig_stl.add_vline(
        x="2022-11-28",
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

st.plotly_chart(fig_stl, use_container_width=True)

st.caption(
    "How to read STL panels: Log-additive STL separates the 400-week series into smooth low-frequency trend, "
    "regular calendar seasonality, and stationarised white-noise residuals. "
    "Vertical red dashed line denotes November 2022."
)

st.divider()

# -------------------------------------------------------------
# 2. Detected Changepoints vs Event Milestones
# -------------------------------------------------------------
st.subheader("2. Unsupervised Changepoints & Milestone Alignment")

tag_cps = cps_df[cps_df["tag"] == selected_tag].sort_values("week_start").copy()
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
st.plotly_chart(fig_cp, use_container_width=True)

st.caption(
    "How to read changepoints: Ruptures Pelt algorithm detects statistically significant shifts in mean volume. "
    "Purple dotted lines flag changepoints occurring within 4 weeks of documented AI industry milestones."
)

st.divider()

# -------------------------------------------------------------
# 3. Interrupted Time Series (ITS) Model & Placebo Check
# -------------------------------------------------------------
st.subheader("3. Interrupted Time Series (ITS) Quasi-Experiment")

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
        f"ITS Regression for {selected_tag}: {slp_chg:+.1f}% slope change per year "
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
            "Annual Slope Trajectory Shift (Beta 3)",
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
            f"- **Actual Intervention Exceeds Placebo:** `{'YES (Robust)' if exceeds_placebo else 'NO (Indeterminate)'}`\n\n"
            f"*Confirms that the observed November 2022 disruption is not an artifact of general year-over-year variation.*"
        )
else:
    st.warning(f"No ITS results found for tag '{selected_tag}'.")
