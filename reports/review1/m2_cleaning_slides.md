# Member 2: cleaning slides (M2-16)

Paste into the team deck (BA Final Project - Review 1). Numbers come from `notebooks/02_cleaning.ipynb` (all 13 tags) and `notebooks/02b_sampling_robustness.ipynb`.

---

## Slide 1: Data cleaning and preprocessing
**Title (states the finding):** 302,032 questions from 309,179 rows, with no row removed for its outcome

- **Missing values:** No accepted answer is not missing data: it means unresolved, so the target is 0 (171,932 questions). Deleted askers (6,319, 2.1%) have no account date: account age is imputed with the median of questions posted before 2025 (543 days) and flagged `missing_account_age`.
- **Duplicates and outliers:** 7,147 questions carried two selected tags: merged to one row each, keeping the smaller sampling weight. 303 very long bodies capped at the 99.9th percentile of text length (kept). 6 mostly non-English posts removed. 0 empty or spam posts.
- **Encoding and scaling:** HTML split into `plain_body` and `code_text` (BeautifulSoup); added `n_code_blocks`, `code_ratio`, `has_error_text`; Unix times to UTC; user IDs hashed (SHA-256 + salt). Scaling is left to the feature stage.
- **Before and after:** 309,179 rows collected -> 302,032 distinct questions -> **302,026 final rows**, 39 columns, 13 tags, Jan 2019 to Aug 2026.

**Visual:** one before/after table (rows collected, duplicates removed, missing imputed, invalid removed, final rows). Source: last table of `02_cleaning.ipynb`.

---

## Slide 2: Targets and label maturity
**Title (states the finding):** 41% of questions get an accepted answer within 7 days, and 75% get any answer

- **Main target** `target_resolved_7d`: accepted answer within 168 hours. **40.8%** positive (42.6% weighted).
- **Secondary target** `target_answered_7d`: any answer within 168 hours. **75.0%** positive (75.9% weighted).
- **Acceptance habit** `accepted_given_answered`: of questions answered within 7 days, 54.4% also have an accepted answer within 7 days.
- **Label maturity rule:** questions posted fewer than 30 days before the collection date (3 Oct 2026) are dropped so every label has had time to form. **0 dropped**: the newest question (31 Aug 2026) is 33 days old.
- **Weights:** before 2025 each tag-month is sampled (1 weekday + 1 weekend day), so every question carries `sampling_weight`. Yearly volume matches the complete counts within about 2%; a second random seed changes the overall resolved rate by only 0.2 to 0.3 points.

**Visual:** class-balance bar for both targets (unweighted and weighted). Source: M2-09 section of `02_cleaning.ipynb`.

---

## Speaker notes (about 1 minute each)
1. "We kept every decision independent of the outcome. An unresolved question is a real answer (target 0), not missing data, so none were dropped. The only imputation is the asker's account age, with a flag, using only pre-2025 data."
2. "The main target is balanced enough to model: 41% positive. The secondary target is easier and more common, 75%, and we use it as a robustness check. The 30-day rule removed nothing because collection ended more than 30 days after the newest question."
