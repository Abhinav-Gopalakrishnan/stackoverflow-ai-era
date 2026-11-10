# Review 2 submission and demonstration

> Historical Review 2 guide. For the final 2026 submission, use
> [the final submission guide](final_submission_guide.md), the root
> `Final_Project_Report.pdf` and `Final_Project_Presentation.pptx`.
> Full public data now ship in `data/original/` and `data/cleaned/`;
> restore the released parquet using `python scripts/submission_data.py --restore`.
> The current public dashboard has eight pages; see [deployment evidence](dashboard_deploy.md).

## Start here

1. Open `notebooks/review2_main.ipynb` for the complete Units 1–3 results. It reads the included saved evidence and needs no API key or full-data mount.
2. Submit the expanded academic report in `submission/academic_report/output/Team_7_Review_2_Academic_Report.pdf` (editable Word copy alongside it). The compact `reports/review2/final_report.pdf` remains an earlier evidence summary.
3. Open the public app at https://stackoverflow-ai-era.streamlit.app/ (all seven pages inspected on 19 October 2026). Deploy the current dashboard changes before the presentation; that inspection does not claim the new local changes are already online. Keep the local launch below as a fallback. Kaggle publication is not claimed.
4. Keep the team's coauthored presentation. Insert the two new slides from `submission/final_handoff/output/Team_7_Review_2_Additional_Slides.pptx`: comparison immediately after the title, public demo immediately after the existing dashboard slide. Archived topic slides contain superseded results.

## Local dashboard (no full dataset or API credentials needed)

```bash
python3 -m venv .venv-dashboard
source .venv-dashboard/bin/activate
python -m pip install -r dashboard/requirements.txt
python -m streamlit run dashboard/app.py
```

Open the local address printed by Streamlit (normally `http://localhost:8501`). All app inputs are lightweight CSVs in `dashboard/data/`. No heavy model runs occur inside the app.

- Overview: tags, observation period, date window, event markers and log scale.
- Patterns: filtered STL/PELT charts; ITS statistics retain the full 400-week fitting period.
- Forecasts: selected tag, model, horizon and intervals. Historical observation filters are disabled because they do not refit saved forecasts. Trajectory classes always use the validation-selected model.
- Topics: actual per-tag prevalence/pre/post outcomes, terms, source examples and measured model comparison. Names are automatic descriptions.
- Tone: filtered monthly charts; fixed pre/post comparisons and transparent one-human-reference validation.
- Recommendations: choose a technology and stakeholder to see proposed actions with tag-specific numerical evidence, owners and prospective KPIs. Download the selected action plan. Global recommendations retain their explicitly labelled scope. Comparison periods are fixed.
- Dataset/classification: 40 title-only examples, full schema/validation and locked model comparisons.

Resolution is a proxy: the answer accepted in the collected record was **posted** within 168 hours of its question. The API data used here do not record when the asker clicked Accept. The delay KPI uses accepted-answer creation time and compares medians of monthly medians.

## Deployment and presentation handoff

Streamlit entrypoint: `dashboard/app.py`. Requirements: `dashboard/requirements.txt`. The app reads only the tracked `dashboard/data/` CSVs, without secrets or the full parquet. Publish all dashboard code changes, including `dashboard/decision_support.py`, before redeploying. `submission/` is ignored by Git: upload the finished report and new slides separately.

After deployment, select Docker in Recommendations and confirm the suggested actions mention Docker and its -56.9% saved forecast. In Forecasts, select Docker with drift, then change the horizon and confirm the scenario text changes. A 26-week Docker median of 0.43 should remain visible. In Overview, confirm the accepted-answer posting-delay label. Keep the disclosed validation and interval limits visible.

Record a 90–120 second backup after deployment: change an Overview tag/period, explore a forecast, inspect a topic/source post, then show a suggested action with its evidence and KPI. The rubric requires meaningful live interaction; the recording is a fallback. Rehearse the whole team within 15 minutes, including these additions.

## Dataset handoff

The full final cleaned dataset is `data/processed/questions_clean_v1.parquet`, 302,026 rows × 39 columns, approximately 302 MiB. It is deliberately excluded from Git. Its byte count and SHA-256 are in `reports/review2/dataset/dataset_validation.json`. The public sample is `reports/review2/dataset/final_dataset_sample.csv`.

Supply the full parquet separately to the evaluator (for example a restricted Drive upload). A Git clone already contains enough data for the result notebooks and local app. Re-running topic training requires the local generated `text_corpus_v1.parquet` and `question_metadata_for_topics.parquet`; rebuild using the original cleaning/corpus pipeline if absent. Do not claim those ignored files are present in a fresh clone.

To create a local source/results ZIP and an optional separate full-dataset ZIP:

```bash
python scripts/package_review2.py --include-dataset
```

Outputs go under ignored `submission/`. Check the generated manifest before uploading. The report, notebooks, code, app, schema, sample, evidence and requirements are included; old archived outputs are excluded from the evaluator package.

## Reproduce heavy analyses

Use Python 3.12 for the full pipeline and the pinned root requirements. The current corrections were run with the versions recorded in the topic manifest; do not assume bitwise identity across numerical-library versions.

```bash
python -m pip install -r requirements.txt
python -m src.ts_patterns --task all
python -m src.ts_forecast
python -m src.topics
python -m src.keywords
python -m src.review2_validation
python -m src.review2_dataset
python -m src.review2_m3_insights
python -m src.review2_refresh_evidence
python -m src.export_dashboard_data
python -m src.review2_notebooks
python -m src.review2_final_report
```

Corpus/tone/complexity regeneration uses the original `src.text_prep`, `src.sentiment` and `src.complexity` modules and their documented local inputs; do not overwrite the preserved original human label sheet. `src.review2_notebooks` builds notebook sources; execute them with Jupyter to refresh saved outputs. The classifier's locked test results are retained; do not retune after inspecting them.

## Explicit limitations and deviations

- No evidence of causal AI substitution. Topic/rate summaries describe the weighted question sample; weekly volumes come from separate API totals (ALL is site-wide).
- VADER has weak performance against one human reference; AI annotations are disclosed and cannot meet the original two-human protocol.
- Current topic descriptions are automatic; original names cannot be transferred by topic ID after refitting.
- Topic comparison uses exact document-cooccurrence NPMI rather than sliding-window c_npmi. The protocol, real seed runs, split IDs and cache fingerprints are retained.
- Forecast bands under-cover on the backtest. Zero-baseline percentage classes remain undefined.
- Optional GRU, BERTopic and classifier what-if features are not required for the two-method rubric and are not claimed.
- A walkthrough script is not a recorded video. Use the actual app and captured screenshots for fallback demonstration.
