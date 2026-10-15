# Review 2 Presentation: Member 1 (Abhinav) Slides & Speaker Script

This document provides the exact slide content, presentation cues, data figures, and speaker notes for Member 1's sections in the Review 2 presentation deck.

**Total Allocated Time for Member 1:** 3 minutes 30 seconds
- **Opening (Slides 1 & 2):** 1:00
- **Live Dashboard Demonstration (Slide 11):** 2:00
- **Closing & Synthesis (Slide 13):** 0:30

---

## Slide 1: Title, Team & Methodological Evolution since Review 1

### Slide Content
- **Project Title:** Stack Overflow in the AI Era: Platform Trajectories & Content Evolution
- **Course / Phase:** Business Analytics Group Case Study — Review 2 (Unit 3 Deliverable)
- **Team Members:**
  - Member 1: Abhinav (Data Governance, Architecture, Dashboard & Unified Synthesis)
  - Member 2: Rishiikesh (Corpus Preparation, VADER Sentiment & Complexity Intervals)
  - Member 3: Akshay (Time-Series Patterns, Stationarity, PELT Changepoints & ITS)
  - Member 4: Nishanth (NMF Topic Modeling & Monroe Distinctive Keyword Dynamics)
  - Member 5: Adhikkesh (Forecasting Benchmarks, Backtesting & 26-Week Projections)
- **Key Methodological Upgrades Since Review 1:**
  1. *Zero Leakage / Strict Temporal Split:* Pre-intervention parameters strictly locked; no hyperparameter tuning on test weeks.
  2. *Empirical Baselines Everywhere:* Advanced architectures (ETS, SARIMAX, NMF) benchmarked against formal naive, seasonal naive, and drift baselines evaluated with Diebold-Mariano tests.
  3. *Fully Executed, Reproducible Notebooks:* Clean top-to-bottom execution in <10 seconds without external GPU dependencies.
  4. *Quasi-Experimental Identification:* 2021 placebo counterfactual tests to verify that the November 2022 break was structural, not regular seasonal variance.

### Speaker Notes (Opening: 0:00 – 0:35)
> *"Good morning professors. In Review 1, our team explored question resolution predictors on Stack Overflow. In Review 2, we tackle the structural shift: how has the platform evolved since ChatGPT launched on November 30, 2022?*
>
> *Before presenting our results, we addressed every critique from Review 1: we enforced zero data leakage by isolating training windows, benchmarked every forecast against formal naive and drift baselines with Diebold-Mariano tests, and validated structural breaks against an empirical 2021 placebo test. Every notebook executes top-to-bottom cleanly without synthetic numbers."*

---

## Slide 2: Research Questions (RQ4, RQ5) & Two Analytical Methods

### Slide Content
- **RQ4 (Topics and Complexity):** What developers still bring to human communities (text mining) — how latent topics, question complexity, asker tone, and distinctive keywords shifted between pre- and post-AI eras.
  - *Method 2:* Natural Language Processing & Text Mining on stratified question corpora.
  - *Pipeline:* NMF Topic Modeling grid ($k=8$ selected), Monroe weighted log-odds vocabulary shift, VADER sentiment/frustration tracking, and 1,000-resample bootstrap intervals for question code/prose complexity.
- **RQ5 (Technology Forecasting):** Which tags keep declining or stabilise (time series) — how weekly volume trajectories evolve around the 2022 break, and what 26-week forecast projections emerge across technologies.
  - *Method 1:* Time Series Analysis on 400 weekly observations per tag (2019–2026).
  - *Pipeline:* STL Loess decomposition (annual 52-week cycle), ADF/KPSS unit-root tests, Ruptures PELT changepoints, segmented Interrupted Time Series (ITS) regressions with 2021 placebo checks, and rolling-origin backtested forecasts.

### Speaker Notes (Opening: 0:35 – 1:00)
> *"Our Review 2 framework bridges two complementary lenses. Method 2 addresses RQ4 by examining topics and complexity to uncover what developers still bring to human communities. Method 1 addresses RQ5 through time-series forecasting across 400 continuous weeks for 13 representative technologies to determine which tags keep declining or stabilise.*
>
> *Through 8-topic NMF modeling, Monroe weighted log-odds, and 1,000-sample bootstrap intervals, we show that while question volume dropped, residual questions grew significantly longer and more architecturally complex."*

---

## Slide 11: Interactive Dashboard Live Demonstration

### Slide Content
- **Live Streamlit URL:** `https://stackoverflow-ai-era.streamlit.app` (Local: `dashboard/app.py`)
- **Interactive Multi-Page Architecture:**
  - *Page 1 (Overview):* 400-week volume trajectory across 13 technologies with log/linear toggles.
  - *Page 2 (Patterns & 2022 Break):* STL decomposition, PELT changepoints, and ITS segmented regression with placebo check.
  - *Page 3 (Forecasts):* 26-week fan chart with 80%/95% prediction intervals, backtest metrics, and tag classification badges.
  - *Page 4 (Topics):* NMF topic share shifts, top term bars, 95% bootstrap CIs, and 7-day resolution outcomes.
  - *Page 5 (Tone & Complexity):* VADER shares, honest tone validation audit (`awaiting_independent_human_labels`), and structural complexity bootstrap CIs.
  - *Page 6 (Recommendations):* Stakeholder-filtered policy cards linked directly to evidence and the 13-tag insight matrix.
- **Governance & Integrity:**
  - 1.62 MB total footprint (27 CSV files, 0 PII, 0 full bodies, CC BY-SA 4.0 compliance).
  - Synchronized cross-page tag state via `st.session_state`.

### Speaker Notes (Live Demo: 1:00 – 3:00)
> *(Action: Open browser to dashboard/app.py or live deployment)*
>
> *"Let us examine our findings directly through our interactive multi-page dashboard. The dashboard runs on 27 schema-validated, aggregated datasets under 2 MB, strictly adhering to CC BY-SA 4.0 with zero PII.*
>
> *(Click Page 2: Select 'python')*  
> *Here on Page 2, our STL decomposition strips out holiday dips to reveal the true trajectory. The PELT algorithm detects breaks clustering between November 2022 and March 2023. Notice our ITS model: Python exhibits a -2.34% per week slope decline post-break ($p < 0.001$). When I toggle the 2021 Placebo test, we see the actual intervention vastly exceeds any pre-AI variation.*
>
> *(Click Page 3: Select 'fastapi' or 'pandas')*  
> *On Page 3, we project the next 26 weeks. Six tags are classed in 'steep decline' losing over 50% volume. Our backtesting proves Seasonal Naive and ETS dominate with MASE < 1.0, and prediction intervals widen appropriately to reflect uncertainty.*
>
> *(Click Page 4: Topics)*  
> *On Page 4, text mining reveals where activity moved. Basic syntax topics dropped by over 2 percentage points, while runtime errors and container deployment gained share. But crucially, runtime error topics resolve at only 33.2% within 7 days.*
>
> *(Click Page 5: Tone & Complexity)*  
> *On Page 5, we report tone validation transparently: human labels are pending, so we present no synthetic accuracy scores. In structural complexity, prose words increased from 76 to 89 words (+13 words, 95% bootstrap CI [12, 13]), and code lines grew from 16 to 20.*
>
> *(Click Page 6: Recommendations)*  
> *Finally, Page 6 links this evidence directly to stakeholders: Q&A product teams should reallocate moderation to steep-decline tags, while DevRel teams must build documentation for the rising setup and migration keywords identified in our Monroe analysis."*

---

## Slide 13: Limitations, Governance & Team Contributions

### Slide Content
- **Analytical Limitations:**
  1. *Sampling weights:* Historical pre-2025 data relies on uniform daily strata weights.
  2. *Scope:* 13 curated ecosystems represent major stacks, not long-tail niche libraries.
  3. *Resolution Proxy:* Accepted answers mark lower-bound resolution; non-accepted upvoted answers remain uncaptured.
  4. *Lexicon Constraints:* VADER is social-media calibrated, requiring independent human validation on code-heavy text.
  5. *Epistemic Precision:* All findings reflect statistical *association* and *consistency*, never direct causal proof.
- **Governance & Open Science Links:**
  - *Project Board:* [GitHub Project Board #3](https://github.com/users/Abhinav-Gopalakrishnan/projects/3) (9 issues, Review 2 milestone)
  - *Repository:* `https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era`
  - *Automated Test Suite:* 54 passing tests (`pytest`) covering schema, latency (<5s), and headless rendering.
- **Review 2 Member Contributions:**
  - M1 (Abhinav): Dashboard architecture, data export validation, unified notebook, repo hygiene, viva guide.
  - M2 (Rishiikesh): Corpus extraction, VADER tone, question complexity bootstrap CIs.
  - M3 (Akshay): STL decomposition, stationarity, PELT change points, ITS segmented regression.
  - M4 (Nishanth): NMF topic modeling, Monroe log-odds keyword dynamics.
  - M5 (Adhikkesh): Forecast model selection, backtesting, Diebold-Mariano tests, 26-week classification.

### Speaker Notes (Closing: 3:00 – 3:30)
> *"To conclude, our study provides a rigorous, reproducible, dual-method evaluation of Stack Overflow's evolving role. While generative AI is associated with reduced simple question traffic, developer dependence has shifted toward deeper, more complex integration challenges.*
>
> *All our workflows are transparently managed on Project Board #3, verified by 54 continuous integration tests, and delivered in an interactive dashboard and executed unified notebook. Thank you, and we welcome your questions."*
