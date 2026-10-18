# Review 2 submission and demonstration

## Start here

1. Open `notebooks/review2_main.ipynb` for the complete Units 1–3 results. It reads the included saved evidence and needs no API key or full-data mount.
2. Read `reports/review2/final_report.pdf` and `reports/review2/readiness_checklist.md`.
3. Run the seven-page local application with the commands below. Public deployment and Kaggle publication are not claimed. The official Review 2 requirements allow a locally runnable application.
4. Prepare the new final presentation separately using the supplied official template. Existing member decks are reference material; archived topic slides contain superseded results.

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
- Recommendations: stakeholder selector and tag-specific insight matrix; fixed comparison periods.
- Dataset/classification: 40 title-only examples, full schema/validation and locked model comparisons.

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
