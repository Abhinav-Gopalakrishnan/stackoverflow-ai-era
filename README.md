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
