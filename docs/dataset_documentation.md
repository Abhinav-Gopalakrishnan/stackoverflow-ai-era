# Dataset Documentation

> **Project:** Stack Overflow in the AI Era — Predicting Question Resolution  
> **Version:** 1.0 (2026-10-04)  
> **Maintainer:** Member 1 (M1)  
> **Companion:** See [Data Dictionary](data_dictionary.md) for field-level specifications.

---

## 1. Research Objective

Investigate how the emergence of large language models (particularly ChatGPT, released November 2022) has affected Stack Overflow question volume, community response behaviour, and the likelihood of question resolution across 13 programming technology tags, from January 2019 to August 2026.

---

## 2. Data Source

- **Platform:** Stack Overflow (stackoverflow.com)
- **API:** Stack Exchange API v2.3 (`api.stackexchange.com`)
  - Authenticated via registered Stack Apps application keys.
  - Rate-limited to 10,000 requests/day per application key.
- **Supplementary Validation:** Stack Exchange Data Explorer (SEDE, `data.stackexchange.com`) for cross-checking headline figures.
- **No scraping:** All data obtained through the official public API.

---

## 3. Study Window

| Parameter | Value |
|:----------|:------|
| **Start date** | 2019-01-01 00:00:00 UTC |
| **End date** | 2026-08-31 23:59:59 UTC |
| **Duration** | 2,800 days (7 years, 8 months) |
| **Calendar months** | 92 (2019-01 through 2026-08) |
| **Weekly windows** | 400 non-overlapping 7-day periods starting on Tuesday |

---

## 4. Tag Selection

Thirteen technology tags were selected to represent a diversity of programming ecosystems, popularity tiers, and expected AI-impact profiles:

| Category | Tags |
|:---------|:-----|
| **High-volume general-purpose** | `python`, `javascript`, `java` |
| **Data & analytics** | `sql`, `pandas`, `r`, `excel`, `powerbi` |
| **Web & mobile frameworks** | `reactjs`, `android` |
| **Infrastructure** | `docker` |
| **AI-era entrants** | `fastapi` (newer framework), `openai-api` (direct AI tooling) |

Tags were chosen to enable cross-tag comparisons between technologies with strong LLM training coverage (e.g. `python`) versus those with weaker coverage (e.g. `powerbi`), and to include at least one tag (`openai-api`) that emerged alongside the AI transition itself.

---

## 5. Sampling Methodology

### 5.1 Population Counts

Complete monthly and weekly question counts were obtained using the API's `filter=total` parameter, which returns the total number of matching questions without transferring individual records. These counts form the population baseline for all volume analyses.

- **Monthly counts:** 13 tags × 92 months = 1,196 tag-month population counts.
- **Weekly counts:** 14 series (13 tags + site-wide `ALL`) × 400 weeks = 5,600 weekly population counts.

### 5.2 Stratified Day-Level Sampling (Question Records)

To collect individual question records within API quota limits, a stratified sampling design was used:

| Period | Sampling Mode | Days per Tag-Month | Description |
|:-------|:-------------|:-------------------|:------------|
| **2019-01 to 2024-12** | Stratified sample | 1 weekday + 1 weekend day | Random day selection within each stratum, seed 42 per tag-month. |
| **2025-01 to 2026-08** | Exhaustive | All days | Every day fully collected to maximise resolution in the post-AI period. |

**Exception:** Tag-months with estimated population below 300 questions are collected exhaustively regardless of period.

### 5.3 Sampling Weights

Each sampled question carries an inverse-probability weight:

$$w = \frac{\text{days of same type (weekday/weekend) in the month}}{\text{days actually sampled}}$$

- For exhaustively collected months, $w = 1$.
- Weighted estimates of monthly totals, resolution rates, and other proportions use these weights.

### 5.4 Final Sample Size

| Metric | Value |
|:-------|:------|
| **Total question records collected** | 309,179 |
| **Tags covered** | 13 |
| **Tag-months in sampling manifest** | 2,392 strata |

See `data/processed/sampling_manifest.csv` for the complete stratum-level manifest.

---

## 6. Data Collection Pipeline

### 6.1 Collection Phases

1. **Test Pull (M1-05):** Small-scale pilot on `python` March 2024 to validate API integration, caching, and logging.
2. **Monthly Population Counts (M1-05):** `filter=total` counts for all 13 tags across 92 months.
3. **Stratified Question Collection (M1-07):** Full question records for all 13 tags via day-level stratified sampling. Paging fix applied mid-collection (see §6.2).
4. **Weekly Population Counts (M1-06):** 400 weekly counts per series for volume trend analysis.

### 6.2 Known Issues and Fixes

| Issue | Impact | Fix |
|:------|:-------|:----|
| **`has_more=False` paging bug** | API prematurely reports no more pages on high-volume days. Affected `reactjs` (lost 3,222 questions) and `docker` (lost 393 questions). | Modified `iter_questions()` to always probe `page+1` after `has_more=False`; stop only on a genuinely empty page. |
| **Docker platform gap** | `filter=total` counts locked/deleted questions that paged results never return. Docker 2025 months show 6–19% fewer collected records than `filter=total` population. | Documented as a known SE API platform limitation. Not fixable from client side. |
| **HTTP 502 transient errors** | 2 occurrences across 19,306 requests. | Automatic exponential backoff retry (up to 3 attempts). Both recovered on retry. |
| **Dual API key quota** | Weekly counts Batch 2 used a secondary registered key (`STACK_API_KEY_BACKUP`). | Quota counter in `logs/collection_log.csv` resets partway through; documented in telemetry audit. |

### 6.3 Telemetry

All API interactions are logged to `logs/collection_log.csv` (19,306 rows) with timestamp, endpoint, HTTP status, items returned, quota remaining, retry count, and cached response file path. See the [Data Dictionary §6](data_dictionary.md#6-telemetry--audit-logscollection_logcsv) for field descriptions.

---

## 7. Enrichment

Member 2 enriched the raw question records with answer timing and user account metadata:

- **Accepted answer dates:** Fetched via `/questions/{ids}/answers` to compute `hours_to_accept`.
- **First answer dates:** Fetched via `/questions/{ids}/answers` to compute `hours_to_first_answer`.
- **User account creation dates:** Fetched via `/users/{ids}` to compute `account_age_days`.

All enrichment is performed by `src/enrich.py` (maintained by Member 2; not edited by Member 1).

---

## 8. Target Variables

Two binary classification targets are defined:

| Target | Definition | Threshold |
|:-------|:-----------|:----------|
| `target_resolved_7d` | Question received an **accepted answer** within 7 days (168 hours) of posting. | `hours_to_accept ≤ 168` |
| `target_answered_7d` | Question received **any answer** within 7 days (168 hours) of posting. | `hours_to_first_answer ≤ 168` |

These targets are computed during cleaning (`notebooks/02_cleaning.ipynb`, Member 2). Questions without an accepted answer are coded as not resolved (target = 0), which conflates "no good answer" with "asker never returned to accept."

---

## 9. Privacy and Ethics

### 9.1 Data Source Terms

- Stack Overflow user-contributed content is licensed under **Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)**.
- The Stack Exchange API Terms of Service permit authenticated access for research purposes.
- No terms-of-service violations: all data obtained through the public API with registered application keys, within daily rate limits.

### 9.2 Privacy Measures

| Measure | Implementation |
|:--------|:---------------|
| **User ID hashing** | All `owner_user_id` values are replaced with irreversible SHA-256 HMAC hashes salted with a secret `HASH_SALT` environment variable before any data leaves the collection pipeline. |
| **No display names** | User display names are never requested, stored, or committed. |
| **No personal data in logs** | The telemetry log (`collection_log.csv`) masks user ID batch parameters in `params_summary`. |
| **API keys excluded from repo** | `.env` is in `.gitignore`; keys are never printed, logged, or committed. Verified by automated prefix scan across `logs/`, `data/`, `notebooks/`, and `git diff`. |
| **HASH_SALT excluded from repo** | Only a placeholder exists in `.env.example`. |

### 9.3 Ethical Considerations

- **No individual profiling:** The analysis focuses on aggregate tag-level and temporal trends, not individual user behaviour.
- **Publicly posted content:** All question titles, bodies, and tags were voluntarily posted on a public platform by their authors under CC BY-SA 4.0.
- **Minimal data collection:** Only fields required for the research questions are collected (no comments, no user profiles, no voting history).

---

## 10. Limitations

### 10.1 Sampling Limitations

- **Pre-2025 coverage:** Before January 2025, each tag-month is represented by only 1 weekday and 1 weekend day. Monthly estimates from sampled records are noisy (mean absolute error ~7.1%, worst ~67% for a single tag-month). Volume analyses should use the complete weekly/monthly population counts, not sampled estimates.
- **Sparse tags:** 137 of 1,168 tag-months have fewer than 30 sampled questions (flagged `low_sample`), concentrated in `openai-api` (pre-2023) and `fastapi`. Conclusions for these tag-months should be stated with caution.
- **Second-seed robustness:** A second random seed (7) on `sql` and `excel` (2019–2024) shows overall weighted resolution rates differ by 0.2–0.3 percentage points, but single-year differences can reach 3–5 points for small tags.

### 10.2 Platform Limitations

- **Docker gap:** The API's `filter=total` counts include locked/deleted questions that paged results never return. Docker 2025 months show 6–19% fewer collected records than the population count. This affects record-level analysis but not population volume trends.
- **`has_more` paging bug:** Fixed during collection via page+1 probing, but any earlier research using the raw SE API without this fix may have systematically undercounted high-volume tag-days.
- **SEDE lag:** SEDE database dumps update weekly; minor discrepancies ($<0.5\%$) between API and SEDE counts are expected from timing differences.

### 10.3 Measurement Limitations

- **"Resolved" conflation:** `target_resolved_7d = 0` mixes questions that received no good answer with questions where the asker never returned to accept an existing answer.
- **Deleted accounts:** 6,319 askers (2.1%) have no account creation date. Their `account_age_days` is imputed with the training-period median and flagged with `missing_account_age = 1`.
- **Body truncation:** 303 very long question bodies are capped at the 99.9th percentile of prose length; 6 non-English posts were removed during cleaning.
- **Tag overlap:** Questions may carry multiple study tags; they appear in multiple tag-specific files but are deduplicated during cleaning (M2-05).

### 10.4 Temporal Scope

- The study window (2019–2026) does not include Stack Overflow's peak years (2013–2015). Pre-2019 decline trends are documented from published sources but not directly measured.
- The 2026 portion ends at August 31; subsequent months are excluded.

---

## 11. Reproducibility

| Artifact | Purpose |
|:---------|:--------|
| `config.yaml` | Tag list, study window, sampling parameters, random seed. |
| `data/processed/sampling_manifest.csv` | Exact dates sampled per tag-month-day_type stratum. |
| `logs/collection_log.csv` | Complete API request audit trail (19,306 rows). |
| `data/raw/collect/` | Cached raw JSON responses (not committed to repo due to size; regenerable from manifest + API). |
| `src/collect.py` | Core API request function with caching, logging, and retry logic. |
| `src/collect_questions.py` | Stratified question collection orchestrator. |
| `src/collect_weekly.py` | Weekly count collection script with resumable checkpointing. |
| `src/enrich.py` | Enrichment pipeline (Member 2). |
| `.env.example` | Template for API keys and HASH_SALT (values not committed). |

---

## 12. License

All Stack Overflow user-contributed content in this dataset is subject to:

> **Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)**  
> https://creativecommons.org/licenses/by-sa/4.0/

Any derivative works, analyses, or publications using this data must provide attribution to Stack Overflow and its contributors, and must be shared under the same or a compatible license.

The project's own code and documentation are available under the repository's license terms.
