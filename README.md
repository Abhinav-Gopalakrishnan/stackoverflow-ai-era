# Stack Overflow in the AI Era

## Summary

This project investigates how Stack Overflow's question-resolution dynamics have evolved in the age of AI-powered coding assistants. Using data from the Stack Exchange API (v2.3, site `stackoverflow`), the team builds a predictive model for the binary target **`target_resolved_7d`** — whether a question receives an accepted answer within 7 days of being posted. The analysis spans data collection, cleaning, exploratory data analysis, feature engineering, modelling, and evaluation, culminating in a comprehensive review of the factors that drive timely resolution on the platform.

## Folder Guide

| Path | Description |
|---|---|
| `src/` | Source code — collection, enrichment, cleaning, feature engineering, modelling |
| `src/collect.py` | Stack Exchange API data-collection module |
| `src/enrich.py` | Post-collection enrichment (e.g. NLP features, user history) |
| `data/raw/` | Raw JSON/CSV pulled from the API (git-ignored; reproducible) |
| `data/processed/` | Cleaned and feature-engineered datasets |
| `logs/` | Run logs and audit trails |
| `logs/collection_log.csv` | Per-run collection metadata (dates, counts, quota usage) |
| `docs/` | Project documentation, rubrics, and work plans |
| `docs/data_dictionary.md` | Field-level definitions for every column in the dataset |
| `docs/dataset_documentation.md` | High-level dataset documentation (provenance, scope, limitations) |
| `docs/Review_1_Work_Plan.pdf` | Review 1 work plan specification (30 pages) |
| `docs/Review_2_Work_Plan.pdf` | Review 2 work plan specification (Unit 3, 28 pages) |
| `docs/Capstone_Project_Rubrics_Updated.docx` | Official project evaluation rubric |
| `notebooks/` | Jupyter notebooks for analysis and deliverables |
| `notebooks/01_collection.ipynb` | Data-collection workflow and API testing |
| `notebooks/review1_main.ipynb` | Main notebook for Review 1 deliverable |
| `notebooks/colab_timeseries_gpu.ipynb` | Time series forecaster (Holt's & PyTorch GPU) |
| `reports/review1/` | Artefacts for Review 1 (charts, speech guides, exported tables) |
| `presentations/Full_PPT_BA_Review_1.pdf` | Final compiled Review 1 presentation deck |
| `requirements.txt` | Python dependencies |
| `.env` | API key (never committed — see setup instructions below) |
| `.env.example` | Template showing required environment variables |

## Stack Apps API Key Setup

### 1. Register on Stack Apps

1. Go to [https://stackapps.com/apps/oauth/register](https://stackapps.com/apps/oauth/register) (log in with your Stack Exchange account).
2. Fill in the form:
   - **Application Name**: `stackoverflow-ai-era` (or any descriptive name)
   - **Description**: University project — predicting accepted answers on Stack Overflow
   - **OAuth Domain**: `localhost` (we only need the API key, not OAuth)
   - **Application Website**: your GitHub repo URL (or `https://localhost`)
3. Click **Register Your Application**.
4. On the next page, copy the **Key** value (this is your API key — *not* the secret).

### 2. Set up `.env`

```bash
# In the project root, copy the example file
cp .env.example .env

# Open .env and replace the placeholders:
# STACK_API_KEY=<your-key-here>
# HASH_SALT=<shared-salt-here>
```

> ⚠️ **Never commit `.env`** — it is listed in `.gitignore`. If `git check-ignore .env` does not print `.env`, something is wrong.
> The `HASH_SALT` is shared out-of-band by Member 2 for SHA-256 user ID pseudonymization and must never be committed.

### 3. Verify

Open `notebooks/01_collection.ipynb` and run the test cell. You should see:
- `HTTP status code : 200`
- `quota_max : 10000`
- `quota_remaining` close to 10 000

## Privacy: What is Stored

This project strictly adheres to privacy and anonymization standards:

1. **Credentials & API Keys**:
   - `STACK_API_KEY` and `HASH_SALT` are stored strictly in the untracked `.env` file.
   - Keys are stripped from all logged URLs, parameter summaries, and cached raw responses before writing to disk.

2. **User Identity & Anonymization**:
   - Stack Overflow user IDs are pseudonymized using SHA-256 combined with `HASH_SALT` (`hashlib.sha256(f"{salt}{int(uid)}".encode()).hexdigest()`).
   - Only hashed user identifiers (`owner_user_hash`, `user_hash`) are committed in processed parquet datasets (`users.parquet`, `test_pull_python_sample.parquet`).
   - Raw user IDs are never committed to the GitHub repository.

3. **Audit Log & Filename Masking**:
   - The shared collection audit log (`logs/collection_log.csv`) masks batched resource ID lists into generic placeholders (`users/{ids}`, `answers/{ids}`, `questions/{ids}/answers`).
   - Batch sizes are recorded as `n_ids` in `params_summary`, ensuring call volume auditability without exposing individual user or post IDs in the committed log.
   - Raw cache file names use masked prefixes (e.g. `users_n2__<hash>.json`), while the deterministic cache hash maintains distinct cache entries per unique ID batch.

4. **Minimal Per-Endpoint API Filters**:
   - API calls use custom minimal filters created with `base="none"`.
   - Personal profile attributes—including `display_name`, `profile_image`, `website_url`, and external profile links—are excluded at the API level and never stored in raw response files.
   - Only essential analytical attributes (`creation_date`, question body/titles, tags, metrics, and wrapper pagination/quota fields) are requested.

5. **Raw & Shared Data Isolation**:
   - All raw API caches (`data/raw/`) and full non-anonymized intermediate datasets (`data/shared/`) are git-ignored and never tracked in source control.

## Processed dataset v1 and how to re-run the cleaning

`data/processed/questions_clean_v1.parquet` is the cleaned, analysis-ready table: **302,026 rows, 39 columns**, built from 309,179 collected rows (13 tags, Jan 2019 to Aug 2026, collection date 2026-10-03). Field definitions are in `docs/data_dictionary.md`. The file is about 316 MB, over GitHub's 100 MB limit, so it is **not committed** (it is in `.gitignore`); it is shared on the team drive. `data/processed/monthly_tag_tables.csv` (weighted monthly rates per tag, with a `low_sample` flag for months under 30 sampled questions) is committed.

To rebuild everything from the raw question files (`data/raw/questions_<tag>.parquet`, from Member 1):

1. Install the environment: `pip install -r requirements.txt`, and put `STACK_API_KEY` and `HASH_SALT` in `.env`.
2. Enrich each tag (answers and asker dates, hashed IDs): `python -m src.enrich data/raw/questions_<tag>.parquet`. Already-enriched questions are skipped, so tags can be run in any order. About 8,500 API calls for all 13 tags.
3. Run `notebooks/02_cleaning.ipynb` top to bottom (about 2 minutes). It writes `data/processed/questions_clean_v1.parquet` once every tag in `config.yaml` is present.
4. `python -m src.aggregate` writes `data/processed/monthly_tag_tables.csv`.

## How to re-run the data collection (M1-13)

All collection parameters—including target tags, study dates (`2019-01-01` to `2026-08-31`), sampling seed (`42`), stratified sampling mode (1 weekday + 1 weekend day pre-2025), and minimal API filters—are centrally defined in `config.yaml`.

### 1. Collect Weekly Population Counts
To re-generate the complete 5,600-row weekly question population dataset across all 14 series (`ALL` plus 13 tags):
```bash
python src/collect_weekly.py --tags ALL python javascript java sql pandas reactjs android excel r docker powerbi fastapi openai-api
```
- Output: `data/processed/weekly_counts.csv` (resumable; checkpoints after every tag).

### 2. Collect Stratified Question Records
To collect or verify stratified question samples for any subset of tags:
```bash
# Re-collect questions for specific tags (e.g. fastapi, docker)
python src/collect_questions.py --tags fastapi docker

# Or run validation checks only (offline, zero API quota used):
python src/collect_questions.py --tags python --check-only
```
- Outputs:
  - `data/shared/questions_<tag>.parquet` (question records with sampling weights).
  - `data/processed/sampling_manifest.csv` (complete sampling manifest with stratum metadata and random seeds).
- **Deterministic Re-run:** Because random day selection uses seed `f"{seed}_{tag}_{month}"`, repeating collection for any tag-month always selects identical calendar dates.


## Review 2: Quasi-Experimental Time Series & Text Mining (Unit 3)

### Overview

In **Review 2**, our investigation shifts from question-level classification to platform-level structural dynamics surrounding the emergence of Generative AI (November 30, 2022). We address two primary research questions:
- **RQ4:** Topics and complexity — what developers still bring to human communities (text mining): how latent technical topics, structural question complexity, asker tone, and distinctive vocabulary evolved between pre-AI and post-AI eras.
- **RQ5:** Technology forecasting — which tags keep declining or stabilise (time series): how weekly question volumes evolved around the 2022 break, and what 26-week forecast trajectories project across technologies.

---

### Review 2 Folder Guide

| Directory / File | Description |
|---|---|
| `notebooks/review2_main.ipynb` | Unified, top-to-bottom executed final notebook covering Sections 0–8 |
| `reports/review2/ts/` | Time-series outputs: STL decomposition, stationarity decisions, PELT changepoints, ITS models, forecast backtests, Diebold-Mariano tests, and 26-week projections |
| `reports/review2/text/` | Text-mining outputs: NMF topic selection ($k=8$), top semantic terms, pre/post share dynamics, VADER tone, complexity bootstrap CIs, Monroe log-odds keywords, and tone validation audit |
| `reports/review2/insight_matrix.csv` | Cross-method synthesis table integrating time-series, topic, tone, and complexity metrics for all 13 tags |
| `reports/review2/recommendations.csv` | 6 stakeholder-aligned policy recommendations with evidence, actions, KPIs, and caveats |
| `reports/review2/board_audit_member1.md` | Read-only audit of Project Board #3 issues, milestones, and metadata |
| `dashboard/` | Multi-page Streamlit analytical application |
| `dashboard/app.py` | Dashboard root entry point (Overview page with 400-week weekly volume series) |
| `dashboard/common.py` | Shared state management, sidebar filters, publication color palette, and cached data loaders |
| `dashboard/pages/` | Interactive pages: `2_Patterns_and_2022_Break`, `3_Forecasts`, `4_Topics`, `5_Tone_and_Complexity`, `6_Recommendations` |
| `dashboard/data/` | Exported data bundle: 27 schema-validated CSV files (1.62 MB total, 0 PII, 0 full bodies) |
| `dashboard/requirements.txt` | Minimal pinned deployment dependencies (`numpy`, `pandas`, `plotly`, `streamlit`) |
| `docs/dashboard_deploy.md` | Streamlit Community Cloud setup, mobile responsive testing, and 2-minute fallback video script |
| `docs/review2_adhi_rishi_handoff.md` | Teammate interface handoff specification between time series and text mining |

---

### How to Rebuild Each Method

All pipeline components are fully reproducible from the root environment (`pip install -r requirements.txt`).

#### Method 1: Time Series (Patterns, Changepoints, ITS, and Forecasting)
```bash
# 1. Decompose trend/seasonality, test stationarity, detect changepoints, and fit ITS regressions
python -m src.ts_patterns

# 2. Benchmark forecasting models (naive, seasonal naive, drift, ETS, SARIMAX), run rolling backtests, and generate 26-week forecasts
python -m src.ts_forecast
```
- **Outputs generated:** `reports/review2/ts/` (all CSV tables and PNG diagnostic charts).

#### Method 2: Text Mining (NMF Topics, Tone, Complexity, and Keywords)
```bash
# 1. Prepare text features, vocabulary dictionaries, and stratified corpus samples
python -m src.text_prep

# 2. Fit NMF topic model grid (k=4..12), extract top terms, compute pre/post shares and 7-day resolution rates
python -m src.topics

# 3. Score VADER sentiment polarity shares, frustration phrases, and politeness flags
python -m src.sentiment

# 4. Measure question structural complexity (prose words, code lines, blocks) with 1,000 bootstrap resamples
python -m src.complexity

# 5. Extract distinctive rising/falling vocabulary via Monroe weighted log-odds
python -m src.keywords
```
- **Outputs generated:** `reports/review2/text/` (all topic, sentiment, complexity, and keyword tables).

#### Cross-Method Synthesis & Dashboard Export
```bash
# 1. Compile cross-method insight matrix and strategic recommendations
python -m src.review2_deliverables

# 2. Validate schemas and export lightweight bundle to dashboard/data/
python src/export_dashboard_data.py
```

---

### Running the Dashboard Locally

Launch the interactive multi-page dashboard:
```bash
streamlit run dashboard/app.py
```
- Automatically opens `http://localhost:8501`.
- All 6 pages share persistent tag, observation window, and event marker filters via `st.session_state`.
- Filtered data slices can be exported on-demand via the sidebar download button.

---

### Running Verification Tests

Run the complete headless AppTest and export validation test suite:
```bash
pytest tests/test_export_dashboard_data.py tests/test_dashboard_pages.py -v
```
- **Coverage:** 54 automated tests verifying file existence, exact column schemas, payload size limits (<50 MB), zero forbidden/PII columns, and render completion under 5 seconds across 4 distinct filter combinations per page.

---

### Hosted Cloud Deployment

- **Live Streamlit App:** `https://stackoverflow-ai-era.streamlit.app` (Placeholder pending manual activation)
- Deployment configuration and mobile responsive audit instructions are located in `docs/dashboard_deploy.md`.

---

### Content Governance & CC BY-SA 4.0 Licence

All Stack Overflow user-contributed content analyzed and displayed within this project is governed by the **Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)** licence:
- Individual questions are referenced exclusively by their post title and linked to canonical URLs: `https://stackoverflow.com/q/<id>`.
- No full question bodies, answers, code blocks, or identifiable user profile information are distributed or hosted.
- All analytical metrics represent aggregated, statistical, and anonymized summaries.
