# Streamlit Community Cloud Deployment & Verification Guide

This document defines the deployment procedure, responsive mobile verification, and a 2-minute screen-recording walkthrough script for the **Stack Overflow in the AI Era** Streamlit dashboard.

---

## 1. Streamlit Community Cloud Configuration Settings

When deploying the app to [share.streamlit.io](https://share.streamlit.io), enter the following exact parameters:

| Parameter | Value | Notes |
|---|---|---|
| **Repository** | `Abhinav-Gopalakrishnan/stackoverflow-ai-era` | GitHub repository containing the dashboard code |
| **Branch** | `main` (or active release branch `m1/deploy-prep`) | Deploys the verified release state |
| **Main file path** | `dashboard/app.py` | Root entry point containing Overview and page navigation |
| **App URL (subdomain)** | `stackoverflow-ai-era` (or custom slug) | Resulting URL: `https://stackoverflow-ai-era.streamlit.app` |
| **Python Version** | `3.10` | Matches project development environment |
| **Requirements file** | `dashboard/requirements.txt` | Automatically detected; pins `numpy`, `pandas`, `plotly`, `streamlit` |
| **Secrets / Env Vars** | None required | All data files are packaged locally in `dashboard/data/` |

### Pre-Deploy Verification Highlights
- **Data payload:** Total uncompressed size of `dashboard/data/` is **1.62 MB** across 27 CSV files (well below the 50 MB Streamlit bundle limit).
- **Zero raw/PII content:** Contains 0 `.parquet` files, 0 full question bodies, and 0 user PII. Titles only, linked directly to canonical Stack Overflow URLs under CC BY-SA 4.0.
- **Fresh-clone verified:** Passes headless testing (`pytest tests/test_dashboard_pages.py`) and standalone daemon launch with isolated `venv`.

---

## 2. Mobile Responsive Testing Procedure (Smartphone / Tablet)

To verify cross-device responsive layout on iOS Safari or Android Chrome:

1. **Access Link:** Open the deployed Community Cloud URL on your mobile browser (or open desktop Chrome DevTools in Mobile Emulation mode: iPhone 14 Pro / Pixel 7).
2. **Sidebar Collapse:** Verify that the Streamlit sidebar automatically collapses into the top-left hamburger menu (`☰`). Tap the menu to confirm tag multi-select, period selector, and CC BY-SA licence expander render cleanly.
3. **Plotly Touch Interactions:**
   - On **Page 1 (Overview)**: Pinch-to-zoom and swipe across the volume trend line. Tap points to inspect tooltips.
   - On **Page 2 (Patterns & 2022 Break)**: Scroll down the 3-panel STL decomposition; ensure subplots stay vertically aligned and readable on narrow viewports.
   - On **Page 3 (Forecasts)**: Verify horizontal touch scroll on the backtest metrics summary table.
   - On **Page 4 (Topics)**: Tap topic horizontal bar charts; ensure label text does not truncate.
   - On **Page 5 (Tone & Complexity)**: Verify keyword horizontal bar charts render with readable labels.
   - On **Page 6 (Recommendations)**: Ensure multi-column cards stack into single-column vertical cards on mobile screens.
4. **Bandwidth / Latency:** Confirm initial cold start loads in under 3 seconds on a 4G/5G mobile connection.

---

## 3. Fallback Video: 2-Minute Screen-Recording Script

In the event of network latency or presentation room connectivity failure, record a high-definition 1080p 60fps walkthrough video following this exact script and timeline.

### Recording Setup
- **Browser:** Full screen (1920×1080), browser bookmarks hidden, 100% zoom.
- **Theme:** Streamlit Light theme.
- **Audio:** Clear microphone, quiet background.

### Script & Action Matrix (0:00 to 2:00)

| Timestamp | Page & Action | On-Screen Click / Interaction | Spoken Narration (What to Say) |
|---|---|---|---|
| **0:00 – 0:20** | **Page 1: Overview** | Open app root. Hover cursor over the November 2022 red dashed line. Toggle "Log Scale" in sidebar. | *"Welcome. This dashboard presents our quasi-experimental and text-mining investigation of Stack Overflow question trends around the launch of generative AI. On the Overview page, we track weekly question volume across 13 major technologies from 2019 to 2026. Notice the immediate structural shift right at the November 2022 ChatGPT event."* |
| **0:20 – 0:45** | **Page 2: Patterns & 2022 Break** | Click Page 2 in navigation. Select `python` from the Focus Tag dropdown. Scroll to STL decomposition, then check "Show Placebo Counterfactual Test". | *"On Page 2, log-additive STL decomposition separates smooth trend from seasonal cycles. PELT changepoints align within weeks of AI release milestones. Our Interrupted Time Series model reveals statistically significant negative slope shifts across all 13 tags, and our 2021 placebo test confirms the post-2022 break is unprecedented."* |
| **0:45 – 1:05** | **Page 3: Forecasts** | Navigate to Page 3. Select `pandas`. Move horizon slider to 26 weeks. Toggle 95% prediction interval band. | *"Page 3 displays 26-week horizon forecasts. Six tags fall into 'steep decline', losing over half their volume. We benchmarked five models; seasonal naive and ETS lead across training backtests. Notice the fan chart with expanding 80 and 95 percent prediction intervals."* |
| **1:05 – 1:25** | **Page 4 & 5: Topics, Tone & Complexity** | Quickly navigate to Page 4, highlight Topic 2 forest chart, then switch to Page 5. Point to Tone Validation status box and Complexity shift chart. | *"On Page 4 and 5, text mining shows where activity moved. While basic syntax questions declined, execution errors and framework migration gained share. Prose length increased from 76 to 89 words with 95% bootstrap confidence. Importantly, on tone validation, we report our status honestly: awaiting human labels, avoiding made-up precision."* |
| **1:25 – 1:50** | **Page 6: Recommendations** | Switch to Page 6. Filter stakeholder to 'Q&A platform product team'. Expand 'ITS Results' tab in the Insight Matrix. | *"Finally, Page 6 synthesises these findings into actionable policies for developer forum managers and DevRel teams. We provide stakeholder-filtered recommendations, KPI trackers, and an integrated cross-method matrix linking time-series slopes, topics, and complexity."* |
| **1:50 – 2:00** | **Closing & Link** | Return to sidebar, show CC BY-SA 4.0 licence expander, and display public URL. | *"The dashboard runs entirely on lightweight aggregated metrics with zero PII and full CC BY-SA compliance. Thank you."* |

---

## 4. Deployed Public Link & Video Assets

- **Live Public URL:** `[To be populated upon manual deployment]`
- **Screen Recording (MP4):** `[To be populated upon manual recording]`
