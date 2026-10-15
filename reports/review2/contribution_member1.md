# Review 2 Contribution Summary: Member 1 (Abhinav Gopalakrishnan)

- **Role:** System Architecture, Data Export Pipeline & Schema Validation, Multi-Page Streamlit Dashboard, Unified Executed Notebook, Deployment Preparation, and Review 2 Documentation.
- **Rubric Components Owned:** Interactive Dashboard / Deployment (Unit 3 deliverable), Master Deliverable Notebook (`review2_main.ipynb`), Schema Verification & Test Automation, Repository Governance, and Presentation Synthesis.
- **GitHub Project Board:** [Project Board #3 (Review 2 Phase)](https://github.com/users/Abhinav-Gopalakrishnan/projects/3)

---

## Tasks Completed (Review 2)

| Issue | Title | Plan Code | Evidence Link | Reviewed By |
|---|---|---|---|:---:|
| [#151](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/issues/151) | Repo ready for Review 2: commit Review 1 leftovers, pin packages, clean directories | `M1-20` | [PR #161](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/161) | NISHANTH-KONCHADA (Approved) |
| [#152](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/issues/152) | Project Board: Review 2 audit across all five members | `M1-21` | [PR #165](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/165), [reports/review2/board_audit_member1.md](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/reports/review2/board_audit_member1.md) | NISHANTH-KONCHADA |
| [#153](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/issues/153) | Dashboard skeleton: multi-page Streamlit app, shared sidebar in `st.session_state`, palette, Overview page | `M1-22` | [PR #163](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/163) | NISHANTH-KONCHADA (Approved) |
| [#154](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/issues/154) | Export dashboard data script (`src/export_dashboard_data.py`) and schema verification test | `M1-23` | [PR #162](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/162), [tests/test_export_dashboard_data.py](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/tests/test_export_dashboard_data.py) | NISHANTH-KONCHADA (Approved) |
| [#155](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/issues/155) | Wire dashboard pages 2 to 6 to real outputs with owners' takeaway captions | `M1-24` | [PR #164](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/164), [tests/test_dashboard_pages.py](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/tests/test_dashboard_pages.py) | NISHANTH-KONCHADA |
| [#156](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/issues/156) | Deploy preparation: fresh-clone isolated test, mobile testing guide, and fallback video script | `M1-25` | [PR #166](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/166), [docs/dashboard_deploy.md](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/docs/dashboard_deploy.md) | smallworldsdev |
| [#157](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/issues/157) | Final notebook: top-to-bottom executed unified deliverable (`notebooks/review2_main.ipynb`) | `M1-26` | [PR #167](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/167), [notebooks/review2_main.ipynb](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/notebooks/review2_main.ipynb) | Rishiikesh-20 |
| [#158](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/issues/158) | README Review 2 documentation: folder map, reproduction commands, test suite, licence | `M1-27` | [PR #168](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/168), [README.md](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/README.md) | Rishiikesh-20 |
| [#159](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/issues/159) | Opening slides, dashboard demo script, contribution summary, and viva guide | `M1-28` | this document, [presentations/member1_slides.md](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/presentations/member1_slides.md), [reports/review2/viva_member1.md](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/reports/review2/viva_member1.md) | smallworldsdev |

---

## Commit Traceability

Every task above is authored by me (git author `Abhinav-Gopalakrishnan`) and verified against GitHub PRs. Running `git log --author="Abhinav" --oneline` confirms the commit lineage:

- `375c83c`, `0692345`, `5ead42e`, `37113da`: `#151` Review 1 leftovers, deck movements to `presentations/`, work plan to `docs/`, and package pinning in `requirements.txt`.
- `dafb8c8`: `#152` Comprehensive read-only Project Board #3 audit recorded in `reports/review2/board_audit_member1.md`.
- `4aaf8ca`, `c5e57a5`, `abcac82`: `#153` Multi-page dashboard skeleton, shared `common.py` state management, academic palette (`TAG_COLORS`), and headless AppTest suite.
- `6493a72`, `d0957fe`, `a86eb8b`: `#154` / `#155` Data export pipeline (`src/export_dashboard_data.py`), caption integration, and 30 automated schema tests.
- `a5c4fb4`, `317d30d`, `732778c`, `28687e2`: `#155` Complete interactive page wiring for Pages 2 through 6, with multi-filter test suite expansion (24 test combinations).
- `0b48377`: `#156` Pre-deploy fresh-clone verification in isolated virtualenv, AppTest execution, headless Streamlit run, and `docs/dashboard_deploy.md`.
- `ba0d6e8`: `#157` Unified final notebook (`notebooks/review2_main.ipynb`) generated with `nbformat` and executed top-to-bottom with `jupyter nbconvert` in <10 seconds.
- `fa1cfc5`: `#158` Comprehensive Review 2 documentation section added to `README.md`.

---

## Key Outputs Delivered

1. **`dashboard/` Multi-Page Streamlit Application:**
   - **`dashboard/app.py`:** Root entry point displaying the 400-week macro series across 13 technologies with logarithmic/linear scaling and milestone overlays.
   - **`dashboard/common.py`:** Centralized state engine managing `st.session_state["selected_tags"]`, date windows, and observation period radio buttons. Features cached data loaders (`@st.cache_data`) and the standardized 14-color palette.
   - **`dashboard/pages/2_Patterns_and_2022_Break.py`:** 3-panel STL decomposition, Pelt unsupervised changepoints, and segmented ITS regression with an interactive 2021 placebo counterfactual toggle.
   - **`dashboard/pages/3_Forecasts.py`:** 26-week horizon fan charts with 80% and 95% prediction intervals, 5-model selector, backtest metrics table, and tag trajectory badges.
   - **`dashboard/pages/4_Topics.py`:** NMF topic share dynamics, top-term horizontal bars, forest chart with 95% bootstrap CIs, 7-day resolution rates, and canonical question links.
   - **`dashboard/pages/5_Tone_and_Complexity.py`:** VADER monthly sentiment shares with `low_sample` greying, frustration rate metrics, honest tone validation audit (`awaiting_independent_human_labels`), and structural complexity bootstrap intervals.
   - **`dashboard/pages/6_Recommendations.py`:** Stakeholder-filtered policy cards linked to underlying evidence and the integrated 13-tag cross-method matrix.
2. **`src/export_dashboard_data.py` Data Pipeline:**
   - Automatically sanitizes, validates, and packages 27 CSV artifacts from `reports/review2/ts/` and `reports/review2/text/` into `dashboard/data/`.
   - Restricts bundle payload to **1.62 MB** (well below the 50 MB Streamlit limit).
   - Enforces CC BY-SA 4.0 compliance: 0 full bodies, 0 PII, titles-only with canonical links.
3. **Automated Headless Test Suite (`tests/`):**
   - **`tests/test_export_dashboard_data.py` (30 tests):** Enforces column name schemas, non-empty files, forbidden column absence, and payload size bounds.
   - **`tests/test_dashboard_pages.py` (24 tests):** Tests all 6 pages under 4 filter permutations (default, one tag, post-period only, log scale) using Streamlit's headless `AppTest`, guaranteeing 0 exceptions and execution < 5s per page.
4. **`notebooks/review2_main.ipynb` Executed Master Notebook:**
   - 67 cells spanning all 9 required sections (0 through 8).
   - Loads precomputed outputs and prints one-sentence takeaways under every table and figure.
   - Executed cleanly via `jupyter nbconvert` in under 10 seconds with 0 errors.
5. **`docs/dashboard_deploy.md` & `README.md` Documentation:**
   - Exact Streamlit Community Cloud settings, mobile responsive test steps, and a 2-minute fallback screen-recording script.

---

## Architectural Decisions & Rationale

1. **Decoupled Architecture with Lightweight Export Pipeline:**
   - Heavy training (ARIMA grid search, STL loess, NMF factorization, 1,000-resample bootstrapping) is performed offline and saved to `reports/review2/`.
   - The dashboard never re-runs heavy ML models; it reads precomputed, schema-validated artifacts via `src/export_dashboard_data.py`. This ensures instant cold-starts (<3s) and zero runtime memory exhaustion on free-tier hosting.
2. **Synchronized Global State via `st.session_state`:**
   - Cross-page analytical continuity is preserved: selecting `python` on Page 2 or Page 3 automatically updates `st.session_state["selected_tags"]`, allowing seamless transitions into Page 4 (Topics) and Page 6 (Recommendations).
3. **Honest Validation Audit without Synthetic Metrics:**
   - Rather than fabricating an artificial confusion matrix or pseudo-accuracy score for tone scoring, Page 5 and the final notebook explicitly display `status: awaiting_independent_human_labels` and `labelled_rows: 0`. This preserves academic honesty and highlights the heuristic nature of lexicon-based sentiment.
4. **Privacy-Preserving CC BY-SA 4.0 Compliance:**
   - To respect Stack Overflow's licensing and user privacy, the dashboard retains zero raw question bodies and zero user hashes. Questions are presented by title only and link directly to canonical web URLs (`https://stackoverflow.com/q/<id>`).
