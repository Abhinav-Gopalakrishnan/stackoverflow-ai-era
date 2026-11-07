"""Page 6: Recommendations."""

import sys
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

_repo_root = Path(__file__).resolve().parents[2]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from dashboard.common import filter_observations, focus_tag, ALL_TAGS, TAG_COLORS, load_data, render_sidebar
from dashboard.decision_support import tag_pilots

st.set_page_config(
    page_title="Page 6: Recommendations",
    page_icon="💡",
    layout="wide",
)

# Render global sidebar
filters = render_sidebar(observations=False, log=False, events=False)
st.caption("These are saved full-period fits and comparisons. Observation-window controls are disabled; use the page controls below.")

st.title("Page 6: Strategic Recommendations")
from dashboard.scenarios import render_scenario
render_scenario()
st.markdown(
    """
    Evidence-based policy recommendations synthesised from time-series patterns,
    text-mining results, and the cross-method insight matrix.
    Suggested pilots include evidence, an owner and a measurable outcome.
    """
)

# Load data
recs = load_data("recommendations.csv")
insight = load_data("insight_matrix.csv")

# =============================================================
# 1. Stakeholder filter
# =============================================================
stakeholders = sorted(recs["stakeholder"].unique())
sel_stakeholders = st.multiselect(
    "Filter by Stakeholder:",
    options=stakeholders,
    default=stakeholders,
    key="page6_stakeholder_filter",
)

if not sel_stakeholders:
    sel_stakeholders = stakeholders

recs_filtered = recs[recs["stakeholder"].isin(sel_stakeholders)].copy()

# Tag selector (synced with session_state for cross-page linking)
selected_tag = focus_tag(filters, 'page6_tag_selector')
st.divider()

# Suggestions use the selected tag's saved numerical evidence. Global cards below
# remain explicitly global because their evidence mixes several technologies.
st.subheader(f"Suggested actions for {selected_tag}")
st.caption(
    "Rule-based decision support from saved results. These are proposed pilots; "
    "their benefits have not been measured. Fixed pre/post comparisons exclude November–December 2022."
)
tag_evidence = insight[insight["tag"] == selected_tag]
if tag_evidence.empty:
    st.info("Select one of the 13 technologies to generate its suggested actions. ALL shows the global recommendations below.")
else:
    pilots = [p for p in tag_pilots(tag_evidence.iloc[0]) if p["stakeholder"] in sel_stakeholders]
    if not pilots:
        st.info("No tag-specific pilot matches the selected stakeholders. Change the stakeholder filter to see other owners.")
    for pilot in pilots:
        st.markdown(f"### {pilot['title']}")
        st.markdown(f"**Evidence:** {pilot['evidence']}")
        st.markdown(f"**Suggested action:** {pilot['action']}")
        st.markdown(f"**Owner:** {pilot['stakeholder']}  \n**KPI and comparison:** {pilot['kpi']}")
        st.caption(f"Evidence scope: {pilot['scope']}")
        st.warning(pilot["caveat"])
    if pilots:
        st.download_button(
            "Download selected action plan (CSV)",
            pd.DataFrame(pilots).to_csv(index=False).encode("utf-8"),
            file_name=f"{selected_tag}_suggested_pilots.csv", mime="text/csv",
        )
    links = st.columns(3)
    links[0].page_link("pages/3_Forecasts.py", label="Inspect forecast evidence")
    links[1].page_link("pages/4_Topics.py", label="Inspect topic examples")
    links[2].page_link("pages/7_Dataset_and_Classification.py", label="Resolution proxy definition")
st.divider()

# =============================================================
# 2. Recommendation cards
# =============================================================
st.subheader(f"Global recommendations ({len(recs_filtered)} of {len(recs)})")
st.caption("These saved cross-project proposals retain their original evidence and scope. The technology selector changes the suggested actions and matrix, not these global cards.")

# Page link mapping for relevant evidence
PAGE_LINKS = {
    "time_series": "Page 2 (Patterns & 2022 Break)",
    "forecast": "Page 3 (Forecasts)",
    "topic": "Page 4 (Topics)",
    "tone": "Page 5 (Tone & Complexity)",
    "frustration": "Page 5 (Tone & Complexity)",
    "complexity": "Page 5 (Tone & Complexity)",
    "keyword": "Page 5 (Tone & Complexity)",
}

for idx, rec in recs_filtered.iterrows():
    with st.container():
        st.markdown(f"### Recommendation {idx + 1}")
        st.markdown(f"**Finding:** {rec['finding']}")

        col_e1, col_e2 = st.columns(2)
        with col_e1:
            st.markdown("📈 **Time-Series Evidence:**")
            st.markdown(f"> {rec['time_series_evidence']}")
        with col_e2:
            st.markdown("📝 **Text-Mining Evidence:**")
            st.markdown(f"> {rec['text_mining_evidence']}")

        col_a, col_s, col_k = st.columns(3)
        with col_a:
            st.markdown(f"**Action:** {rec['action']}")
        with col_s:
            st.markdown(f"**Stakeholder:** `{rec['stakeholder']}`")
        with col_k:
            st.markdown(f"**KPI to Track:** {rec['kpi_to_track']}")

        st.warning(f"⚠️ **Caveat:** {rec['caveat']}")

        # Infer relevant page links from evidence text
        evidence_text = (str(rec["time_series_evidence"]) + " " + str(rec["text_mining_evidence"])).lower()
        relevant_pages = set()
        for keyword, page_label in PAGE_LINKS.items():
            if keyword in evidence_text:
                relevant_pages.add(page_label)
        if relevant_pages:
            st.caption(f"🔗 Related pages: {', '.join(sorted(relevant_pages))}")

        st.divider()

# =============================================================
# 3. Insight Matrix (expandable table)
# =============================================================
st.subheader("Cross-Method Insight Matrix")

st.markdown(
    "A synthesised view across all 13 study tags: forecast trajectory, ITS results, "
    "topic trends, tone, and complexity changes. "
    "Wording note: All changes are *associated with*, not *caused by*, AI adoption."
)

# Highlight selected tag row
insight_display = insight.copy() if selected_tag == "ALL" else insight[insight.tag == selected_tag].copy()

# Define readable column groups
TS_COLS = ["tag", "forecast_class", "change_26w_pct", "half_life_weeks", "load_index_vs_2025"]
ITS_COLS = ["tag", "its_level_change_pct", "its_level_p", "its_slope_change_pct", "its_slope_p",
            "its_status", "its_exceeds_placebo"]
TOPIC_COLS = ["tag", "rising_topics", "falling_topics", "topic_evidence_scope"]
TONE_COLS = ["tag", "frustration_change", "frustration_lower95", "frustration_upper95",
             "resolved_rate_pre", "resolved_rate_post", "resolved_rate_change"]
COMPLEX_COLS = ["tag", "complexity_prose_words_change", "complexity_code_lines_change",
                "complexity_version_flag_change"]

tab_full, tab_ts, tab_its, tab_topic, tab_tone = st.tabs(
    ["Full Matrix", "Forecasts", "ITS Results", "Topics", "Tone & Complexity"]
)

def _highlight_tag(row):
    """Highlight the selected tag row."""
    if row["tag"] == selected_tag:
        return ["background-color: #DBEAFE; color: #18334A"] * len(row)
    return [""] * len(row)

with tab_full:
    st.dataframe(
        insight_display.style.apply(_highlight_tag, axis=1).format(
            {c: "{:.2f}" for c in insight_display.select_dtypes("number").columns},
            na_rep="—",
        ),
        hide_index=True,
        height=500,
    )

with tab_ts:
    st.dataframe(
        insight_display[TS_COLS].style.apply(_highlight_tag, axis=1).format(
            {"change_26w_pct": "{:.1f}%", "half_life_weeks": "{:.0f}",
             "load_index_vs_2025": "{:.1f}"},
            na_rep="—",
        ),
        hide_index=True,
    )

with tab_its:
    st.dataframe(
        insight_display[ITS_COLS].style.apply(_highlight_tag, axis=1).format(
            {"its_level_change_pct": "{:.1f}%", "its_slope_change_pct": "{:.1f}%",
             "its_level_p": "{:.4f}", "its_slope_p": "{:.4f}"},
            na_rep="—",
        ),
        hide_index=True,
    )

with tab_topic:
    st.dataframe(
        insight_display[TOPIC_COLS].style.apply(_highlight_tag, axis=1),
        hide_index=True,
    )

with tab_tone:
    tone_complex = insight_display[TONE_COLS + COMPLEX_COLS[1:]].copy()
    st.dataframe(
        tone_complex.style.apply(_highlight_tag, axis=1).format(
            {c: "{:.2f}" for c in tone_complex.select_dtypes("number").columns},
            na_rep="—",
        ),
        hide_index=True,
    )

# Tag-specific summary card
st.divider()
st.subheader(f"Tag Summary: {selected_tag}")

tag_row = insight[insight["tag"] == selected_tag]
if not tag_row.empty:
    tr = tag_row.iloc[0]
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    with col_s1:
        st.metric("Forecast Class", tr["forecast_class"])
    with col_s2:
        change_26 = tr["change_26w_pct"]
        st.metric("26-Week Change", f"{change_26:.1f}%" if pd.notna(change_26) else "N/A")
    with col_s3:
        slope = tr["its_slope_change_pct"]
        st.metric("ITS Growth-Rate Shift (%/week)", f"{slope:+.1f}%" if pd.notna(slope) else "N/A")
    with col_s4:
        frust = tr["frustration_change"]
        st.metric("Frustration Δ (pp)",
                  f"{frust:+.1f}" if pd.notna(frust) else "N/A")

    # Evidence narrative
    rising = tr["rising_topics"] if pd.notna(tr["rising_topics"]) else "—"
    falling = tr["falling_topics"] if pd.notna(tr["falling_topics"]) else "—"
    st.markdown(
        f"**Rising topics:** {rising}  \n"
        f"**Falling topics:** {falling}  \n"
        f"**Evidence scope:** {tr['topic_evidence_scope']}  \n"
        f"**Prose words change:** {tr['complexity_prose_words_change']:+.0f} | "
        f"**Code lines change:** {tr['complexity_code_lines_change']:+.0f} | "
        f"**Version flag change:** {tr['complexity_version_flag_change']:+.2f}"
    )
else:
    st.info("ALL displays all 13 study tags above. Select a technology to see its summary.")
