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
| `docs/` | Project documentation |
| `docs/data_dictionary.md` | Field-level definitions for every column in the dataset |
| `docs/dataset_documentation.md` | High-level dataset documentation (provenance, scope, limitations) |
| `notebooks/` | Jupyter notebooks for analysis and deliverables |
| `notebooks/01_collection.ipynb` | Data-collection workflow and API testing |
| `notebooks/review1_main.ipynb` | Main notebook for Review 1 deliverable |
| `reports/review1/` | Artefacts for Review 1 (charts, slides, exported tables) |
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

