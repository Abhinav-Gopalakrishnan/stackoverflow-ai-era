# Data Dictionary

> **Project:** Stack Overflow in the AI Era  
> **Version:** 1.0 (2026-10-04)  
> **Maintainer:** Member 1 (M1)

This document catalogues every field across all project datasets — raw collection, enrichment, cleaning, aggregation, and feature engineering — with types, sources, and descriptions.

---

## 1. Raw Question Records (`data/shared/questions_<tag>.parquet`)

One file per study tag (13 tags). Collected via Stack Exchange API `/questions` endpoint with stratified day-level sampling (M1-07, PR #49).

| # | Field | Type | Source | Description |
|:--|:------|:-----|:-------|:------------|
| 1 | `question_id` | `int64` | API `question_id` | Unique Stack Overflow question identifier. |
| 2 | `accepted_answer_id` | `float64` | API `accepted_answer_id` | ID of the accepted answer; `NaN` if none accepted. |
| 3 | `owner_user_id` | `float64` | API `owner.user_id` | Numeric user ID of the question author; `NaN` for deleted/anonymous users. **Not committed raw — hashed in enrichment.** |
| 4 | `answer_count` | `int64` | API `answer_count` | Number of answers at time of collection. ⚠️ **Forbidden feature** (post-hoc). |
| 5 | `creation_date` | `int64` | API `creation_date` | Question posting timestamp (Unix epoch seconds, UTC). |
| 6 | `tags` | `str` | API `tags` | Semicolon-separated list of tags applied to the question. |
| 7 | `title` | `str` | API `title` | Question title text (HTML-encoded). |
| 8 | `body` | `str` | API `body` | Full question body (HTML). |
| 9 | `sampling_weight` | `float64` | Computed | Inverse-probability weight reflecting the stratified sampling design: `days_of_type_in_month / days_sampled` for the tag-month-day_type stratum. |
| 10 | `score` | `int64` | API `score` | Net votes (upvotes minus downvotes) at time of collection. ⚠️ **Forbidden feature** (post-hoc). |
| 11 | `view_count` | `int64` | API `view_count` | Number of views at time of collection. ⚠️ **Forbidden feature** (post-hoc). |
| 12 | `is_answered` | `bool` | API `is_answered` | Whether the question has an answer with score > 0 or an accepted answer. ⚠️ **Forbidden feature** (post-hoc). |
| 13 | `last_activity_date` | `int64` | API `last_activity_date` | Timestamp of most recent activity (Unix epoch seconds, UTC). ⚠️ **Forbidden feature** (post-hoc). |
| 14 | `closed_date` | `float64` | API `closed_date` | Timestamp when the question was closed; `NaN` if still open. ⚠️ **Forbidden feature** (post-hoc). |
| 15 | `collected_tag` | `str` | Collection metadata | The study tag used in the API `tagged` parameter to collect this question. |
| 16 | `month` | `str` | Computed | Year-month string (`YYYY-MM`) derived from `creation_date`. |
| 17 | `day_type` | `str` | Computed | `"weekday"` or `"weekend"` based on the UTC date of `creation_date`. |

---

## 2. Enrichment Outputs (Member 2, `src/enrich.py`)

### 2a. `data/processed/answers.parquet`

Accepted-answer and first-answer timestamps fetched via `/questions/{ids}/answers` and `/answers/{ids}`.

| # | Field | Type | Source | Description |
|:--|:------|:-----|:-------|:------------|
| 1 | `question_id` | `int64` | Join key | Foreign key to raw question records. |
| 2 | `accepted_answer_creation_date` | `float64` | API | Unix epoch seconds (UTC) when the accepted answer was posted; `NaN` if no accepted answer. |
| 3 | `first_answer_creation_date` | `float64` | API | Unix epoch seconds (UTC) when the earliest answer was posted; `NaN` if unanswered. |

### 2b. `data/processed/users.parquet`

User account metadata fetched via `/users/{ids}`, with privacy masking.

| # | Field | Type | Source | Description |
|:--|:------|:-----|:-------|:------------|
| 1 | `user_hash` | `str` | Computed | SHA-256 HMAC of the raw `user_id` salted with `HASH_SALT`. Irreversible pseudonym. |
| 2 | `account_creation_date` | `int64` | API `creation_date` | Unix epoch seconds (UTC) when the user account was created. |

---

## 3. Cleaning-Derived Fields (`notebooks/02_cleaning.ipynb`, Member 2)

These fields are computed during the cleaning pipeline and appear in the cleaned dataset.

| # | Field | Type | Source | Description |
|:--|:------|:-----|:-------|:------------|
| 1 | `hours_to_accept` | `float64` | `(accepted_answer_creation_date - creation_date) / 3600` | Hours from question posting to creation of the answer accepted in the collected record. This is answer-posting delay, not the time the asker clicked Accept. `NaN` if no accepted answer. |
| 2 | `hours_to_first_answer` | `float64` | `(first_answer_creation_date - creation_date) / 3600` | Hours between question posting and the first answer. `NaN` if unanswered. |
| 3 | `target_resolved_7d` | `bool` / `int` | `hours_to_accept <= 168` | **Target variable 1.** Resolution proxy: the answer accepted in the collected record was posted within 168 hours of the question. Acceptance-event time and satisfaction are not observed. |
| 4 | `target_answered_7d` | `bool` / `int` | `hours_to_first_answer <= 168` | **Target variable 2.** Whether the question received any answer within 7 days (168 hours). |
| 5 | `plain_body` | `str` | HTML-stripped `body` | Plain-text question body with HTML tags removed. |
| 6 | `code_text` | `str` | Extracted `<code>` blocks | Concatenated text from all `<code>` / `<pre>` blocks in the body. |
| 7 | `n_code_blocks` | `int` | `count(<code> blocks)` | Number of code blocks in the question body. |
| 8 | `code_ratio` | `float64` | `len(code_text) / len(body)` | Ratio of code text length to total body length. 0 if no body. |
| 9 | `has_error_text` | `bool` / `int` | Regex on `plain_body` | Whether the body contains error-like patterns (`Traceback`, `Error:`, `Exception`, stack trace signatures). |
| 10 | `account_age_days` | `float64` | `(creation_date - account_creation_date) / 86400` | Days between user account creation and question posting. `NaN` if user account is missing/deleted. |
| 11 | `new_account` | `bool` / `int` | `account_age_days <= 7` | Whether the question author's account was created within 7 days of posting. |
| 12 | `missing_account_age` | `bool` / `int` | `account_age_days.isna()` | Indicator for missing account age (deleted or anonymous users). |

---

## 4. Feature Engineering Fields (`docs/feature_spec.md`, Member 4)

Candidate features for predictive modelling. All are available at question posting time (no leakage).

| # | Field | Type | Source | Description |
|:--|:------|:-----|:-------|:------------|
| 1 | `title_length` | `int` | `len(title)` | Number of characters in the question title. |
| 2 | `body_length` | `int` | `len(plain_body)` | Number of characters in the plain-text body. |
| 3 | `n_code_blocks` | `int` | Cleaning | Count of code blocks (same as §3.7). |
| 4 | `code_ratio` | `float64` | Cleaning | Code-to-body length ratio (same as §3.8). |
| 5 | `has_error_text` | `bool` | Cleaning | Error pattern indicator (same as §3.9). |
| 6 | `question_word` | `str` | Regex on `title` | Leading question word extracted from the title (How, Why, What, etc.). |
| 7 | `tag_count` | `int` | `len(tags.split(';'))` | Number of tags applied to the question. |
| 8 | `hour_posted` | `int` | `creation_date` | Hour of the day (0–23, UTC) the question was posted. |
| 9 | `weekday_posted` | `int` | `creation_date` | Day of the week (0=Mon … 6=Sun) the question was posted. |
| 10 | `month_posted` | `int` | `creation_date` | Month (1–12) the question was posted. |
| 11 | `account_age_days` | `float64` | Cleaning | Same as §3.10. |
| 12 | `missing_account_age` | `bool` | Cleaning | Same as §3.12. |
| 13 | `new_account` | `bool` | Cleaning | Same as §3.11. |
| 14 | `lagged_tag_volume` | `int` | `weekly_counts.csv` | Total questions posted in the same tag during the 4 full weeks (28 days) immediately prior to the question's posting week. |
| 15 | `lagged_tag_change` | `int` | `weekly_counts.csv` | Difference in tag volume between the 4 weeks prior to posting and the 4 weeks before that (weeks −8 to −5). |
| 16 | `title_tfidf_svd_0` … `title_tfidf_svd_99` | `float64` | TF-IDF + TruncatedSVD on `title` | 100 latent semantic components from TF-IDF vectorization of question titles, reduced via truncated SVD. |
| 17 | `tag_<name>` | `int` (0/1) | `tags` | Multi-hot encoded indicator columns for each of the 13 study tags. |
| 18 | `other_tags_count` | `int` | `tags` | Count of tags on the question that are not among the 13 study tags. |

### Forbidden Fields (Leakage Rule)

The following fields contain information about events *after* question posting and are **excluded from the feature matrix**:

- `score`, `view_count`, `answer_count`, `is_answered`, `closed_date`, `last_activity_date`
- Current user `reputation` (not collected)

### Excluded by Design

- `post_ai`: Indicates whether the question was posted after November 2022 (ChatGPT release). Constant for the entire test period (Jul 2025–Jul 2026), so unusable as a feature. Reserved for analysis and rolling-origin comparisons only.

---

## 5. Aggregate Tables (`data/processed/`)

### 5a. `weekly_counts.csv` (M1-06, Issue #21)

| # | Field | Type | Description |
|:--|:------|:-----|:------------|
| 1 | `tag` | `str` | Study tag name, or `"ALL"` for site-wide total. |
| 2 | `week_start` | `str` (`YYYY-MM-DD`) | UTC start date of the 7-day window. |
| 3 | `count` | `int` | Total questions posted during the 7-day period (from API `filter=total`). |

**Week definition:** 400 non-overlapping 7-day windows from `2019-01-01` (Tuesday) to `2026-08-31`. 14 series (13 tags + ALL). 5,600 total rows.

### 5b. `monthly_counts.csv` (M1-05)

| # | Field | Type | Description |
|:--|:------|:-----|:------------|
| 1 | `tag` | `str` | Study tag name. |
| 2 | `month` | `str` (`YYYY-MM`) | Calendar month. |
| 3 | `count` | `int` | Total questions posted in the calendar month (from API `filter=total`). |

**Scope:** 13 tags × 92 months (2019-01 to 2026-08). 1,196 total rows.

### 5c. `monthly_tag_tables.csv` (M2-13)

| # | Field | Type | Description |
|:--|:------|:-----|:------------|
| 1 | `tag` | `str` | Study tag name. |
| 2 | `month` | `str` (`YYYY-MM`) | Calendar month. |
| 3 | `n_sampled` | `int` | Number of sampled questions in this tag-month. |
| 4 | `est_questions` | `float64` | Estimated population questions (weighted). |
| 5 | `resolved_rate_7d` | `float64` | Weighted proportion meeting the seven-day accepted-answer posting-time proxy defined above. |
| 6 | `answered_rate_7d` | `float64` | Weighted proportion of questions answered within 7 days. |
| 7 | `accepted_given_answered` | `float64` | Weighted resolution-proxy proportion conditional on receiving a first answer within 168 hours. |
| 8 | `median_hours_to_accept` | `float64` | Weighted median delay from question posting to posting of its accepted answer, among records with that delay available. |
| 9 | `median_hours_to_first_answer` | `float64` | Weighted median hours to first answer. |
| 10 | `low_sample` | `bool` | Flag indicating the tag-month has fewer than 30 sampled questions. |

### 5d. `sampling_manifest.csv` (M1-07)

| # | Field | Type | Description |
|:--|:------|:-----|:------------|
| 1 | `tag` | `str` | Study tag (or `"ALL"` for global sampling). |
| 2 | `month` | `str` (`YYYY-MM`) | Calendar month. |
| 3 | `mode` | `str` | Sampling mode: `"sampled"` (pre-2025 stratified) or `"full"` (2025+ exhaustive). |
| 4 | `day_type` | `str` | `"weekday"` or `"weekend"`. |
| 5 | `sampled_date` | `str` (`YYYY-MM-DD`) | The specific UTC date collected. |
| 6 | `days_of_type_in_month` | `int` | Total weekdays or weekend days in the calendar month. |
| 7 | `days_sampled` | `int` | Number of days of this type actually sampled. |
| 8 | `weight` | `float64` | Inverse-probability sampling weight: `days_of_type_in_month / days_sampled`. |
| 9 | `n_questions` | `int` | Number of questions collected for this sampled date. |
| 10 | `collection_date` | `str` | UTC date when the API call was made. |

---

## 6. Telemetry & Audit (`logs/collection_log.csv`)

| # | Field | Type | Description |
|:--|:------|:-----|:------------|
| 1 | `timestamp_utc` | `str` (ISO 8601) | UTC timestamp of the API request. |
| 2 | `member` | `str` | Team member who initiated the call (`M1` or `M2`). |
| 3 | `endpoint` | `str` | API endpoint called (e.g. `questions`, `answers/{ids}`). |
| 4 | `params_summary` | `str` (JSON) | Serialized non-key request parameters. |
| 5 | `page` | `int` | Page number requested. |
| 6 | `http_status` | `str` / `int` | HTTP response code (`200`, `502`) or `CACHED` for cache hits. |
| 7 | `items` | `int` | Number of items returned in the response. |
| 8 | `has_more` | `bool` | API's `has_more` pagination flag (unreliable — see M1-07 paging fix). |
| 9 | `quota_remaining` | `float64` | Remaining API quota after the call. |
| 10 | `backoff` | `float64` | Backoff seconds requested by the API, if any. |
| 11 | `retry_count` | `int` | Number of retries performed for this request (0 = first attempt succeeded). |
| 12 | `raw_file` | `str` | Relative path to the cached raw JSON response file. |

---

## 7. Configuration (`config.yaml`)

| Key | Value | Description |
|:----|:------|:------------|
| `study_window.start` | `2019-01-01` | First date of the study period (UTC). |
| `study_window.end` | `2026-08-31` | Last date of the study period (UTC). |
| `tags` | 13 tags | `python`, `javascript`, `java`, `sql`, `pandas`, `reactjs`, `android`, `excel`, `r`, `docker`, `powerbi`, `fastapi`, `openai-api`. |
| `newer_tag` | `fastapi` | Tag that entered the study window later than others. |
| `sampling.seed` | `42` | Random seed for reproducible stratified sampling. |
| `sampling.pre2025_mode` | `sampled` | 1 weekday + 1 weekend day per tag-month before 2025. |
| `sampling.post2025_mode` | `full` | All days collected exhaustively from 2025 onward. |
