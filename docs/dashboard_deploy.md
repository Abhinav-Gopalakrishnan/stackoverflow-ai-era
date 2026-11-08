# Dashboard availability and demonstration

The supported submission mode is a locally runnable Streamlit application; the official Review 2 requirements accept this. No public deployment is verified. The previously suggested `stackoverflow-ai-era.streamlit.app` address returned 404 during the audit and is not a live deliverable.

Run `pip install -r dashboard/requirements.txt` and `streamlit run dashboard/app.py`. A fresh clone needs neither the full parquet nor API credentials. See `docs/final_implementation.md` for the current eight-page app, fitted-model protocol and demonstration sequence. See `docs/review2_submission_guide.md` for page controls, data access, limitations and package instructions.

## Two-minute demonstration

- 0:00–0:20: Overview. Select Python, change pre/post observation period, then toggle log scale. Explain observational scope and overlapping tags.
- 0:20–0:40: Patterns. Show STL and ITS; slope-change units are percent per week. A placebo is a sensitivity check, not causal proof.
- 0:40–1:00: Forecasts. Show the validation-selected model, horizon and uncertainty. State measured undercoverage and undefined zero-baseline classes.
- 1:00–1:20: Topics. Change tag and show prevalence, real comparison table and title-only examples. Names are automatic.
- 1:20–1:40: Tone and recommendations. Show 36% VADER accuracy, one human reference, separate AI–human agreement and a recommendation's caveat.
- 1:40–2:00: Dataset and classification. Show the validated data sample, model comparison and locked test PR-AUC. Close with the source/report/board links.

Current screenshots are in `reports/final_validation/screenshots/`; older screenshots are in `reports/review2/dashboard_screenshots/`. They are visual fallback evidence, not a video or proof of public hosting.

## Optional later hosting

Use repository `Abhinav-Gopalakrishnan/stackoverflow-ai-era`, branch `main`, entry point `dashboard/app.py` and requirements `dashboard/requirements.txt` with a hosting provider that supports Streamlit. Verify the actual resulting URL before advertising it. No provider deployment was created in this corrections task.
