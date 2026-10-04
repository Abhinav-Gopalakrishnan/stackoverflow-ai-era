# Processed Data Artifacts

This directory contains processed tabular summaries and manifests used across analysis, modeling, and evaluation phases.

## Datasets

### 1. `weekly_counts.csv` (Task M1-06, Issue #21)
- **Granularity & Scope**: Complete question counts from `/questions` with `filter=total` for each of the 13 target tags plus site-wide total (`tag="ALL"`).
- **Date Range**: `2019-01-01 00:00:00` to `2026-08-31 23:59:59` UTC ($2,800$ days).
- **Week Definition**:
  - Exactly **400 non-overlapping 7-day calendar weeks** spanning the study window ($2,800 \div 7 = 400$).
  - **Start Weekday**: Weeks start on **Tuesday** (`2019-01-01` was a Tuesday).
  - **First `week_start`**: `2019-01-01` (`2019-01-01 00:00:00` to `2019-01-07 23:59:59` UTC).
  - **Last `week_start`**: `2026-08-25` (`2026-08-25 00:00:00` to `2026-08-31 23:59:59` UTC).
  - **Total Series**: 14 series (13 tags + `ALL`).
  - **Total Rows**: Exactly 5,600 rows ($14 \times 400$).
  - **Missing Weeks**: 0 missing weeks across all series.
- **Columns**:
  - `tag` (str): Target tag name, or `"ALL"` for site-wide questions.
  - `week_start` (str, `YYYY-MM-DD`): UTC start date of the 7-day period.
  - `count` (int): Total questions posted during the 7-day period.

### 2. `monthly_counts.csv` (Task M1-05)
- Monthly question population counts per tag from `2019-01` to `2026-08` (92 months per tag).

### 3. `sampling_manifest.csv` (Task M1-07)
- Stratified sampling manifest (2,392 rows) defining sampled days, weekday/weekend distribution, and sampling weights.
