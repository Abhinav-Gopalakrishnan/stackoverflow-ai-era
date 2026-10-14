"""Page 4: Topics."""

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
    from common import load_data, render_sidebar
except ImportError:
    from dashboard.common import load_data, render_sidebar

st.set_page_config(
    page_title="Page 4: Topics",
    page_icon="🏷️",
    layout="wide",
)

# Render global sidebar
filters = render_sidebar()

st.title("Page 4: Topic Mining & Thematic Disruption")
st.markdown(
    """
    NMF topic modeling across the question corpus, tracking shifting developer inquiry shares,
    pre/post AI topic reallocation, and 7-day resolution outcomes.
    """
)

# Load data
terms_df = load_data("topics_top_terms.csv")
shares_df = load_data("topic_monthly_share.csv")
prepost_df = load_data("topic_prepost.csv")
outcomes_df = load_data("topic_outcomes.csv")
examples_df = load_data("topic_examples.csv")
labels_df = load_data("topic_labels.csv")

# Merge labels into prepost
topics_meta = prepost_df.merge(labels_df, on="topic", how="left")

# Topic selector & sort controls
c_sort, c_picker = st.columns([2, 3])
with c_sort:
    sort_criterion = st.radio("Sort Topics Table By:", options=["Pre/Post Change (%)", "Corpus Volume"], horizontal=True)

if sort_criterion == "Pre/Post Change (%)":
    topics_meta = topics_meta.sort_values("change_pct", ascending=False)
else:
    topics_meta = topics_meta.sort_values("pre_share", ascending=False)

topic_options = topics_meta["topic"].tolist()
topic_display_names = {
    t: f"Topic {t}: {labels_df.loc[labels_df['topic'] == t, 'final_name'].iloc[0]}"
    for t in topic_options
}

with c_picker:
    selected_topic = st.selectbox(
        "Select Focus Topic:",
        options=topic_options,
        format_func=lambda x: topic_display_names[x],
        key="topic_selector",
    )

focus_label_row = labels_df[labels_df["topic"] == selected_topic].iloc[0]
focus_prepost_row = prepost_df[prepost_df["topic"] == selected_topic].iloc[0]
focus_outcome_row = outcomes_df[outcomes_df["topic"] == selected_topic].iloc[0]

# Check if mixed
is_mixed = "mixed" in str(focus_label_row["agreement"]).lower()
if is_mixed:
    st.warning("⚠️ **Flagged Topic:** Independent raters marked this topic as 'mixed/inconclusive'. It is excluded from strategic conclusions.")

# -------------------------------------------------------------
# Topic Summary Metrics
# -------------------------------------------------------------
m1, m2, m3, m4 = st.columns(4)
m1.metric("Pre-AI Share", f"{focus_prepost_row['pre_share'] * 100:.2f}%")
m2.metric("Post-AI Share", f"{focus_prepost_row['post_share'] * 100:.2f}%")
chg = focus_prepost_row["change_pct"]
m3.metric(
    "Pre/Post Shift",
    f"{chg:+.2f}%",
    delta=f"{chg:+.1f}%",
    delta_color="normal",
    help=f"95% CI: [{focus_prepost_row['lower95'] * 100:.2f}%, {focus_prepost_row['upper95'] * 100:.2f}%]",
)
m4.metric("7-Day Resolved Rate", f"{focus_outcome_row['resolved_rate_7d'] * 100:.1f}%")

st.divider()

# -------------------------------------------------------------
# Top Terms & Monthly Share Charts (Side-by-Side)
# -------------------------------------------------------------
col_terms, col_share = st.columns(2)

with col_terms:
    st.subheader(f"Top Characteristic Terms (Topic {selected_topic})")
    top_terms = terms_df[terms_df["topic"] == selected_topic].sort_values("rank").head(10)

    fig_terms = go.Figure(
        go.Bar(
            x=top_terms["weight"],
            y=top_terms["term"],
            orientation="h",
            marker=dict(color="#1D4E89"),
        )
    )
    fig_terms.update_layout(
        title=dict(text=f"<b>Salient Lexical Features: {focus_label_row['final_name']}</b>", font=dict(size=13)),
        xaxis=dict(title="NMF Feature Weight", showgrid=True, gridcolor="#E5E7EB"),
        yaxis=dict(autorange="reversed"),
        height=380,
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        margin=dict(l=20, r=20, t=50, b=30),
    )
    st.plotly_chart(fig_terms, use_container_width=True)
    st.caption("Top 10 tokens extracted by non-negative matrix factorisation.")

with col_share:
    st.subheader("Monthly Weighted Share Over Time")
    topic_monthly = shares_df[shares_df["topic"] == selected_topic].sort_values("month")

    # Dynamic takeaway title
    direction = "expanded" if chg > 0 else "contracted"
    share_title = (
        f"Topic {selected_topic} share {direction} by {abs(chg):.1f}% "
        f"consistent with workflow changes"
    )

    fig_share = go.Figure()
    fig_share.add_trace(
        go.Scatter(
            x=topic_monthly["month"],
            y=topic_monthly["weighted_share"] * 100,
            mode="lines+markers",
            name="Share %",
            line=dict(color="#0284C7", width=2.2),
        )
    )
    # Shading
    fig_share.add_vrect(x0="2019-01", x1="2022-10", fillcolor="rgba(30, 144, 255, 0.05)", line_width=0)
    fig_share.add_vrect(x0="2022-11", x1="2022-12", fillcolor="rgba(245, 158, 11, 0.15)", line_width=0)
    fig_share.add_vrect(x0="2023-01", x1="2026-08", fillcolor="rgba(220, 38, 38, 0.05)", line_width=0)

    fig_share.update_layout(
        title=dict(text=f"<b>{share_title}</b>", font=dict(size=13)),
        xaxis=dict(title="Month", showgrid=True, gridcolor="#E5E7EB"),
        yaxis=dict(title="Weighted Share (% of Site Questions)", showgrid=True, gridcolor="#E5E7EB"),
        height=380,
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        margin=dict(l=20, r=20, t=50, b=30),
    )
    st.plotly_chart(fig_share, use_container_width=True)
    st.caption("Monthly prevalence preserving sampling weights. Shading marks pre, transition, and post-AI eras.")

st.divider()

# -------------------------------------------------------------
# Overall Topic Shift Comparison (95% CI Forest Chart)
# -------------------------------------------------------------
st.subheader("All Topics: Pre vs Post AI Adoption Shift (%) with 95% Bootstrap CIs")

topics_forest = topics_meta.sort_values("change_pct", ascending=True)
colors_bar = [
    "#9CA3AF" if "mixed" in str(a).lower() else ("#059669" if c > 0 else "#DC2626")
    for a, c in zip(topics_forest["agreement"], topics_forest["change_pct"])
]

fig_forest = go.Figure()
fig_forest.add_trace(
    go.Bar(
        x=topics_forest["change_pct"],
        y=[f"T{t}: {n[:28]}" for t, n in zip(topics_forest["topic"], topics_forest["final_name"])],
        orientation="h",
        marker=dict(color=colors_bar),
        error_x=dict(
            type="data",
            symmetric=False,
            array=(topics_forest["upper95"] - topics_forest["change"]) * 100,
            arrayminus=(topics_forest["change"] - topics_forest["lower95"]) * 100,
            color="#1F2937",
        ),
    )
)
fig_forest.update_layout(
    title=dict(
        text="<b>Shift in Topic Shares (Post vs Pre 2022 Break) with 95% Bootstrap Intervals</b>",
        font=dict(size=14),
    ),
    xaxis=dict(title="Relative Change in Prevalence (%)", showgrid=True, gridcolor="#E5E7EB"),
    height=440,
    plot_bgcolor="#FFFFFF",
    paper_bgcolor="#FFFFFF",
    margin=dict(l=20, r=20, t=50, b=30),
)
st.plotly_chart(fig_forest, use_container_width=True)
st.caption(
    "How to read topic shift: Green bars denote expanding topics; red denote contracting. "
    "Grey indicates mixed agreement. 95% intervals computed via 1,000 weighted bootstrap resamples."
)

st.divider()

# -------------------------------------------------------------
# 10 Representative Example Titles with Canonical Links
# -------------------------------------------------------------
st.subheader(f"10 Canonical Question Examples (Topic {selected_topic}: {focus_label_row['final_name']})")
st.markdown("*Titles only, hyperlinked to Stack Overflow (CC BY-SA 4.0; no bodies or user identifiers).*")

topic_exs = examples_df[examples_df["topic"] == selected_topic].head(10)
if not topic_exs.empty:
    for i, (_, ex) in enumerate(topic_exs.iterrows(), 1):
        st.markdown(f"{i}. [{ex['title']}]({ex['link']})")
else:
    st.info("No examples listed for this topic.")
