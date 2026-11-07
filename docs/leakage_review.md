# Feature Spec and Leakage Review (M5-05)

> Historical Review 1 design/evidence. The implemented v2 model protocol and remaining snapshot limitations are documented in [the current technical handoff](final_implementation.md). Original locked results have not been regenerated.

Reviewer: Member 5. Reviewed: `docs/feature_spec.md` against `src/cleaning.py` (the columns that will be in `questions_clean_v1`), `src/features.py`, and `m4/split-module`.

**Verdict: changes requested.** Sign-off once A, C and D1-D2 are fixed. The final column-by-column check of the real feature matrix is M4-08.

## A. Fields missing from the forbidden list (leakage)
1. `hours_to_accept`, `hours_to_first_answer`, `accepted_at`, `first_answer_at`, `accepted_answer_id` contain the outcome itself.
2. `target_answered_7d` leaks `target_resolved_7d` (and the reverse); `accepted_given_answered` is a function of both.
3. `last_activity_date` / `last_activity_at` is recorded after posting.
4. `sampling_weight` and `collected_tags` are collection artifacts. `sampling_weight` is a proxy for the time period (1 from 2025, larger before); use it only as a sample weight, never as a feature.
5. `user_hash`, `question_id` and the raw `creation_date` / `created_at` are identifiers or time proxies. Use only the derived hour, weekday and month.

## B. Spec and code disagree
1. `has_error_text`: spec says `plain_body` only; cleaning uses `plain_body` + `code_text`.
2. `code_ratio`: spec uses raw `body`; cleaning uses `code_len / (plain_len + code_len)`.
3. `new_account`: undefined when account age is imputed. The imputation median is computed over all of 2019-2024, so it slightly leaks into early rolling-origin windows.

## C. Lagged tag volume needs a precise definition
1. State that the posting week is excluded, which weekday weeks start on, and that complete weekly counts are used, not sampled data.
2. Questions in early 2019 have no 4-week history before January 2019: drop them or add a flag.
3. Questions with two selected tags: say how double counting is handled.

## D. Split (`m4/split-module`)
1. Time-series folds are cut by row count, not by date.
2. No 7-day gap between train and validation: a question posted 28 Dec 2024 has a label only known on 4 Jan 2025. Drop the last 7 days before each boundary.
3. `report_split_stats` uses `is_answered` (a forbidden field) as a placeholder target.
4. `create_splits` modifies the input dataframe.

## E. Note (non-blocking)
Before 2025 the weekday mix in the sample is distorted by design; train with `sampling_weight` as the sample weight.

## Tools to automate the checks
- `src/leakage.py`: `assert_no_leakage(columns)` fails on any forbidden column; `unexpected_columns(columns)` lists columns not in the spec; `expected_lagged_volume(...)` is an independent implementation to check Member 4's lagged volume on hand-picked questions.
- `src/timecv.py`: `time_series_folds` cuts by date with a 7-day gap (usable as a reference for D1-D2).
