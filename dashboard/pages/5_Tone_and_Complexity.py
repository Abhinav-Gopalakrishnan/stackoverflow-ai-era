"""Page 5: Tone and Complexity."""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

_repo_root = Path(__file__).resolve().parents[2]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from dashboard.common import render_chart, filter_observations, focus_tag, ALL_TAGS, TAG_COLORS, load_data, render_sidebar

st.set_page_config(
    page_title="Page 5: Tone & Complexity",
    page_icon="💬",
    layout="wide",
)

# Render global sidebar
filters = render_sidebar(log=False)

st.title("Page 5: Tone and Complexity")
st.markdown(
    """
    Sentiment distribution, frustration-flag trends, question structural complexity,
    and distinctive keyword shifts between the pre- and post-AI periods.
    """
)

# Load data
tone_monthly = load_data("tone_monthly.csv")
tone_prepost = load_data("tone_prepost.csv")
complexity_prepost = load_data("complexity_prepost.csv")
keywords_prepost = load_data("keywords_prepost.csv")
validation = load_data("tone_validation.csv")
text_captions = load_data("text_captions.csv")

# Parse month column as datetime
tone_monthly["month_dt"] = pd.to_datetime(tone_monthly["month"])

# Helper: get caption from text_captions by chart name
def _caption(chart_name: str) -> str:
    """Return the owner's takeaway caption, falling back to empty string."""
    row = text_captions[text_captions["chart"] == chart_name]
    if row.empty:
        return ""
    return f"{row.iloc[0]['takeaway']}  \n*Caveat: {row.iloc[0]['caveat']}*"

# Tag selector (synced to session_state)
selected_tag = focus_tag(filters, 'page5_tag_selector')
st.caption("Monthly charts follow the observation window. Pre/post summaries and keyword comparisons use the fixed research periods, excluding the transition.")
tag_color = TAG_COLORS.get(selected_tag, "#1D4E89")

# Metric picker
TONE_METRICS = {
    "negative_share": "Negative Tone Share",
    "neutral_share": "Neutral Tone Share",
    "positive_share": "Positive Tone Share",
    "frustration_flag_share": "Frustration-Flag Rate",
    "politeness_flag_share": "Politeness-Flag Rate",
}
selected_metric = st.selectbox(
    "Tone Metric:",
    options=list(TONE_METRICS.keys()),
    format_func=lambda x: TONE_METRICS[x],
    key="page5_metric_selector",
)

# =============================================================
# 1. Tone shares over time
# =============================================================
st.subheader("1. Monthly Tone Shares")

tm = filter_observations(tone_monthly, "month", filters, monthly=True, tags=[selected_tag]).sort_values("month_dt")

# Grey out low_sample months
tm["opacity"] = tm["low_sample"].apply(lambda x: 0.25 if x else 1.0)

# Compute dynamic takeaway from tone_prepost
tp_tag = tone_prepost[tone_prepost["tag"] == selected_tag]
tp_metric_row = tp_tag[tp_tag["measure"] == selected_metric.replace("_share", "").replace("_flag_share", "")]
if tp_metric_row.empty:
    # Try matching directly on the column name
    measure_map = {
        "negative_share": "negative",
        "neutral_share": "neutral",
        "positive_share": "positive",
        "frustration_flag_share": "frustration",
        "politeness_flag_share": "politeness",
    }
    tp_metric_row = tp_tag[tp_tag["measure"] == measure_map.get(selected_metric, "")]

if not tp_metric_row.empty:
    change_val = tp_metric_row.iloc[0]["change"] * 100  # convert to pp
    lo95 = tp_metric_row.iloc[0]["lower95"] * 100
    hi95 = tp_metric_row.iloc[0]["upper95"] * 100
    change_dir = "increased" if change_val > 0 else "decreased"
    tone_title = (
        f"{TONE_METRICS[selected_metric]} for {selected_tag}: "
        f"{abs(change_val):.1f} pp {change_dir} (95% CI [{lo95:+.1f}, {hi95:+.1f}] pp) "
        f"(fixed pre/post comparison)"
    )
else:
    tone_title = f"{TONE_METRICS[selected_metric]} for {selected_tag}"

fig_tone = go.Figure()

# Separate low_sample and normal for styling
normal = tm[~tm["low_sample"]]
low = tm[tm["low_sample"]]

fig_tone.add_trace(
    go.Scatter(
        x=normal["month_dt"],
        y=normal[selected_metric],
        mode="lines+markers",
        name=TONE_METRICS[selected_metric],
        line=dict(color=tag_color, width=2),
        marker=dict(size=4),
    )
)
if not low.empty:
    fig_tone.add_trace(
        go.Scatter(
            x=low["month_dt"],
            y=low[selected_metric],
            mode="markers",
            name="Low sample (greyed)",
            marker=dict(color="#D1D5DB", size=5, symbol="circle-open"),
        )
    )

if filters["show_events"]:
    # ChatGPT break
    fig_tone.add_vline(
        x="2022-11-30",
        line_width=1.5,
        line_dash="dash",
        line_color="#DC2626",
        annotation_text="ChatGPT Launch",
        annotation_position="top left",
        annotation=dict(font_size=9, font_color="#DC2626"),
    )

fig_tone.update_layout(
    title=dict(text=f"<b>{selected_tag}: {TONE_METRICS[selected_metric]}</b>", font=dict(size=14, color="#1F2937")),
    xaxis=dict(title="Month", showgrid=True, gridcolor="#E5E7EB"),
    yaxis=dict(title="Share", showgrid=True, gridcolor="#E5E7EB",
               tickformat=".0%"),
    height=400,
    plot_bgcolor="#FFFFFF",
    paper_bgcolor="#FFFFFF",
    margin=dict(l=40, r=40, t=60, b=40),
)
render_chart(fig_tone, width='stretch')

st.caption(tone_title)
st.caption(_caption("Tone and complexity"))

st.divider()

# =============================================================
# 2. Frustration-flag rate detail
# =============================================================
st.subheader("2. Frustration-Flag Rate")

frust_prepost = tp_tag[tp_tag["measure"] == "frustration"]
if not frust_prepost.empty:
    fr = frust_prepost.iloc[0]
    fr_change = fr["change"] * 100
    fr_pre = fr["pre"] * 100
    fr_post = fr["post"] * 100
    fr_lo = fr["lower95"] * 100
    fr_hi = fr["upper95"] * 100
    fr_dir = "rose" if fr_change > 0 else "fell"

    frust_title = (
        f"Frustration-flag rate for {selected_tag}: {fr_dir} from "
        f"{fr_pre:.1f}% to {fr_post:.1f}% ({fr_change:+.1f} pp, "
        f"95% CI [{fr_lo:+.1f}, {fr_hi:+.1f}] pp)"
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Pre-Period Rate", f"{fr_pre:.1f}%")
    with col2:
        st.metric("Post-Period Rate", f"{fr_post:.1f}%")
    with col3:
        st.metric(
            "Change (pp)",
            f"{fr_change:+.1f}",
            delta=f"{fr_change:+.1f} pp",
            delta_color="inverse",
        )
    st.markdown(f"**{frust_title}**")
    st.caption(_caption("Frustration phrases"))
else:
    st.warning(f"No frustration-flag data found for tag '{selected_tag}'.")

st.divider()

# =============================================================
# 3. Tone Validation Audit
# =============================================================
st.subheader("3. Tone Validation Against One Human Reference")
val_row = validation.iloc[0]
st.warning(str(val_row['reference']) + ". " + str(val_row['limitation']))
cols = st.columns(4)
cols[0].metric("VADER accuracy", f"{val_row['accuracy']:.1%}")
cols[1].metric("VADER macro F1", f"{val_row['macro_f1']:.3f}")
cols[2].metric("AI–human agreement", f"{val_row['ai_human_agreement']:.1%}")
cols[3].metric("AI–human Cohen's κ", f"{val_row['ai_human_kappa']:.3f}")
st.caption("200 posts. Two-human kappa and adjudicated gold labels are unavailable. AI annotations are disclosed; VADER and frustration flags remain exploratory.")
st.dataframe(load_data('tone_confusion.csv'), hide_index=True)

st.divider()

# =============================================================
# 4. Complexity Pre vs Post with 95% CIs
# =============================================================
st.subheader("4. Question Structural Complexity: Pre vs Post")

cx = complexity_prepost[complexity_prepost["tag"] == selected_tag].copy()
cx_median = cx[cx["statistic"] == "median"].copy()

if not cx_median.empty:
    # Focus on key metrics
    key_metrics = ["prose_words", "code_lines", "n_code_blocks", "flesch_reading_ease", "tag_count"]
    cx_show = cx_median[cx_median["metric"].isin(key_metrics)].copy()

    metric_labels = {
        "prose_words": "Prose Words",
        "code_lines": "Code Lines",
        "n_code_blocks": "Code Blocks",
        "flesch_reading_ease": "Flesch Reading Ease",
        "tag_count": "Tag Count",
    }
    cx_show["label"] = cx_show["metric"].map(metric_labels)

    # Compute takeaway from largest absolute change
    largest = cx_show.loc[cx_show["change"].abs().idxmax()]
    cx_dir = "increased" if largest["change"] > 0 else "decreased"
    cx_title = (
        f"Complexity for {selected_tag}: Median {metric_labels.get(largest['metric'], largest['metric'])} "
        f"{cx_dir} by {abs(largest['change']):.0f} "
        f"(95% CI [{largest['lower95']:.0f}, {largest['upper95']:.0f}])"
    )

    fig_cx = go.Figure()

    for _, row in cx_show.iterrows():
        fig_cx.add_trace(
            go.Bar(
                x=[row["label"]],
                y=[row["change"]],
                name=row["label"],
                marker_color=tag_color,
                error_y=dict(
                    type="data",
                    symmetric=False,
                    array=[row["upper95"] - row["change"]],
                    arrayminus=[row["change"] - row["lower95"]],
                    color="#4B5563",
                ),
                text=f"Δ{row['change']:+.1f}",
                textposition="outside",
                showlegend=False,
            )
        )

    fig_cx.update_layout(
        title=dict(text=f"<b>{selected_tag}: changes in weighted medians</b>", font=dict(size=14, color="#1F2937")),
        xaxis=dict(title="", showgrid=False),
        yaxis=dict(title="Change (Median, Pre→Post)", showgrid=True, gridcolor="#E5E7EB"),
        height=400,
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        margin=dict(l=40, r=40, t=60, b=40),
    )
    fig_cx.add_hline(y=0, line_width=1, line_color="#9CA3AF")
    render_chart(fig_cx, width='stretch')

    st.caption("Metrics have different native units (words, lines, blocks, reading-ease points and tag counts); bar heights are not comparable across metrics.")
    st.caption(_caption("Complexity intervals"))

    # Show full data table
    with st.expander("Full Complexity Data (all metrics, median & mean)"):
        cx_all = cx.copy()
        cx_all["CI 95%"] = cx_all.apply(
            lambda r: f"[{r['lower95']:.2f}, {r['upper95']:.2f}]", axis=1
        )
        st.dataframe(
            cx_all[["metric", "statistic", "pre", "post", "change", "CI 95%", "n_pre", "n_post"]],
            hide_index=True,
        )
else:
    st.warning(f"No complexity data found for tag '{selected_tag}'.")

st.divider()

# =============================================================
# 5. Rising and Falling Keywords
# =============================================================
st.subheader("5. Distinctive Keyword Shifts (Pre → Post)")

# Keywords are scoped to certain tags
kw = keywords_prepost.copy()
include_placeholders = st.checkbox('Include preprocessing placeholders in keyword view', value=False, key='page5_placeholders')
if not include_placeholders:
    kw = kw[~kw.term.astype(str).str.contains(r'(?:^|\s)(?:numbertoken|pathtoken|urltoken)(?:\s|$)',regex=True)]
st.caption('The default keyword view excludes numeric/path/URL placeholders; original rankings are retained in the saved CSV.')
available_scopes = sorted(kw["tag_scope"].unique())

# Default to the selected tag's scope if available, else ALL
kw_scope = selected_tag if selected_tag in available_scopes else "ALL"
if kw_scope not in available_scopes:
    kw_scope = available_scopes[0] if available_scopes else "ALL"

kw_scope = st.selectbox(
    "Keyword Scope:",
    options=available_scopes,
    index=available_scopes.index(kw_scope) if kw_scope in available_scopes else 0,
    key="page5_keyword_scope",
)

kw_tag = kw[kw["tag_scope"] == kw_scope].copy()

n_show = st.slider("Top N keywords per direction:", min_value=5, max_value=30, value=15, key="page5_kw_n")

rising = kw_tag[kw_tag["direction"] == "rising"].nlargest(n_show, "z_score")
falling = kw_tag[kw_tag["direction"] == "falling"].nlargest(n_show, "z_score")

# Takeaway: top rising keyword
if not rising.empty:
    top_rising = rising.iloc[0]
    kw_title = (
        f"Top rising keyword in {kw_scope} scope: '{top_rising['term']}' "
        f"(z = {top_rising['z_score']:.1f}, "
        f"{top_rising['freq_pre_pct']:.2f}% → {top_rising['freq_post_pct']:.2f}%)"
    )
else:
    kw_title = f"Keyword shifts for {kw_scope}"

col_r, col_f = st.columns(2)

with col_r:
    st.markdown(f"**Rising Keywords** (more frequent post-AI)")
    if not rising.empty:
        fig_r = go.Figure()
        fig_r.add_trace(
            go.Bar(
                y=rising["term"].iloc[::-1],
                x=rising["z_score"].iloc[::-1],
                orientation="h",
                marker_color="#059669",
                text=rising["z_score"].iloc[::-1].apply(lambda z: f"z={z:.1f}"),
                textposition="outside",
            )
        )
        fig_r.update_layout(
            title=dict(text="<b>Rising (z-score)</b>", font=dict(size=13)),
            xaxis=dict(title="z-score", showgrid=True, gridcolor="#E5E7EB"),
            yaxis=dict(title=""),
            height=max(300, n_show * 28),
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF",
            margin=dict(l=120, r=60, t=40, b=30),
        )
        render_chart(fig_r, width='stretch')
    else:
        st.info("No rising keywords found.")

with col_f:
    st.markdown(f"**Falling Keywords** (less frequent post-AI)")
    if not falling.empty:
        fig_f = go.Figure()
        fig_f.add_trace(
            go.Bar(
                y=falling["term"].iloc[::-1],
                x=falling["z_score"].iloc[::-1],
                orientation="h",
                marker_color="#DC2626",
                text=falling["z_score"].iloc[::-1].apply(lambda z: f"z={z:.1f}"),
                textposition="outside",
            )
        )
        fig_f.update_layout(
            title=dict(text="<b>Falling (z-score)</b>", font=dict(size=13)),
            xaxis=dict(title="z-score", showgrid=True, gridcolor="#E5E7EB"),
            yaxis=dict(title=""),
            height=max(300, n_show * 28),
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF",
            margin=dict(l=120, r=60, t=40, b=30),
        )
        render_chart(fig_f, width='stretch')
    else:
        st.info("No falling keywords found.")

st.markdown(f"**{kw_title}**")

# Keywords detail table
with st.expander("Full Keywords Table"):
    st.dataframe(
        kw_tag[["term", "direction", "z_score", "log_odds", "freq_pre_pct", "freq_post_pct", "rank"]].sort_values("z_score", ascending=False),
        hide_index=True,
    )
