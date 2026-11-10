# Dashboard availability and demonstration

Public application: https://stackoverflow-ai-era.streamlit.app/

Verified on 8 November 2026: the public application serves the current eight-page dashboard and its fitted XGBoost prediction pipeline. The example prediction returned 46.8%; changing the title returned 48.0%, with updated tree SHAP contributions. All eight public pages were smoke-tested. GitHub main includes the implementation through PR #176 (merge commit d447635). The URL was already serving the updated application when checked; no new app or hosting configuration was created during this verification. Earlier availability failures are historical.

The local application remains a supported fallback. Public verification details and screenshots are in reports/final_validation/public_deployment.json and reports/final_validation/screenshots/.

Run `pip install -r dashboard/requirements.txt` and `streamlit run dashboard/app.py`. A fresh clone needs neither the full parquet nor API credentials. See `docs/final_implementation.md` for the current eight-page app, fitted-model protocol and demonstration sequence. See `docs/review2_submission_guide.md` for page controls, data access, limitations and package instructions.

## Two-minute demonstration

- 0:00–0:20: Overview. Select Python, change pre/post observation period, then toggle log scale. Explain observational scope and overlapping tags.
- 0:20–0:40: Patterns. Show STL and ITS; slope-change units are percent per week. A placebo is a sensitivity check, not causal proof.
- 0:40–1:00: Forecasts. Show the validation-selected model, horizon and uncertainty. State measured undercoverage and undefined zero-baseline classes.
- 1:00–1:20: Topics. Change tag and show prevalence, real comparison table and title-only examples. Names are automatic.
- 1:20–1:40: Tone and recommendations. Show 36% VADER accuracy, one human reference, separate AI–human agreement and a recommendation's caveat.
- 1:40–2:00: Dataset and classification. Show the validated data sample, model comparison and locked test PR-AUC. Close with the source/report/board links.

Current screenshots are in `reports/final_validation/screenshots/`; older screenshots are in `reports/review2/dashboard_screenshots/`. They are visual fallback evidence, not a video or proof of public hosting.

## Hosting configuration and updates

The source repository is `Abhinav-Gopalakrishnan/stackoverflow-ai-era`; use branch `main`, entry point `dashboard/app.py` and dependencies in `dashboard/requirements.txt`. The saved pipeline and metadata under `models/resolution_v2/` must remain in the deployed revision. The recorded model runtime is Python 3.13.13. Model inference is a historical demonstration covering 26 February 2019 through 31 August 2026. Refresh data and validate a new release before accepting current posting dates.
