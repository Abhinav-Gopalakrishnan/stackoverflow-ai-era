# Sampling and cleaning limitations (M2-14)

For inclusion in the limitations section of `docs/dataset_documentation.md`. Evidence: `notebooks/02b_sampling_robustness.ipynb`.

## How the data was sampled
- Before January 2025, each tag-month is a sample of **one random weekday and one random weekend day** (seed 42); tag-months with fewer than 300 questions and every month from January 2025 are collected in full.
- Each sampled question carries `sampling_weight` (days of that type in the month divided by days sampled; 1 for fully collected months). Monthly figures must use the weights.

## What the robustness check found
1. **No overall bias.** Estimated yearly volume is within about 2% of the complete counts (2019: +0.4%, 2022: -1.4%, 2024: -2.2%).
2. **Monthly volume from the sample is noisy.** Across 912 sampled tag-months the mean absolute error is 7.1% (median 5.2%, 90th percentile 16.9%, worst 67%). Volume charts should use the complete weekly counts, not the sampled estimate.
3. **Weights matter little by year, more by tag-month.** Weighted and unweighted resolution rates differ by under 1 percentage point per year, by 0.75 points on average per tag-month, and by up to 14 points in the worst tag-month.
4. **A second random seed gives the same overall class balance.** For `sql` and `excel` (2019 to 2024, seed 7 against seed 42) the weighted resolved rate differs by 0.2 to 0.3 percentage points overall and the answered rate by 0.3 to 0.7. By single year the difference reaches about 3 to 5 points. Changes between years smaller than that in a small tag should not be read as real.
5. **Platform gap.** Fully collected months should match the complete counts. Docker in January to March 2025 is 24% to 43% below, and a few other small months 3% to 12% below, because the API's `filter=total` counts locked or deleted questions that the paged endpoint never returns.
6. **Sparse tags.** 137 of 1,168 tag-months have fewer than 30 sampled questions (flagged `low_sample`; mostly `openai-api`, which has only a handful of questions per month before 2023, and `fastapi`).

## Cleaning limitations
- 6,319 askers (2.1%) have no account creation date (deleted accounts); their account age is imputed with the training-period median and flagged `missing_account_age`.
- 1 first answer is dated before its question and 92 askers have an account newer than their question; the cause is unknown. They are kept, and account age is clipped at 0.
- 303 very long question bodies are capped at the 99.9th percentile of prose length (`body_truncated`); 6 mostly non-English posts were removed.
- `accepted_answer_id` is empty for questions without an accepted answer; these count as not resolved (target 0), which mixes "no good answer" with "asker never returned to accept".
