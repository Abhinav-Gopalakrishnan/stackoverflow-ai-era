# Review 1 Contribution Summary: Member 2 (Rishiikesh, Register number: CB.SC.U4CSE23___ , fill in)

Role: data enrichment, cleaning and preprocessing
Rubric components owned: Data cleaning and preprocessing (3 marks); second half of data collection (answers and users); sampling robustness

## Tasks completed
| Issue | Title | Evidence link | Reviewed by |
| --- | --- | --- | --- |
| #5 | [M2-01] Shared Python environment | [PR #9](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/9) | Member 1 |
| #6 | [M2-02] Enrichment design | [design note](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/issues/6#issuecomment-5938338308) | Member 1 |
| #7 | [M2-03] Enrichment script | [PR #10](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/10), [PR #26](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/26) | Member 1 |
| #8 | [M2-04] Enrichment run for all tags | [PR #60](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/60), [PR #50](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/50), [PR #63](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/63), [PR #67](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/67) | Member 1 |
| #51 | [M2-05] Merge and deduplication | [PR #59](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/59), [notebook](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/notebooks/02_cleaning.ipynb) | Member 1 |
| #52 | [M2-06] Timestamp conversion and checks | [PR #59](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/59), [notebook](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/notebooks/02_cleaning.ipynb) | Member 1 |
| #53 | [M2-07] HTML cleaning and code extraction | [PR #59](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/59), [notebook](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/notebooks/02_cleaning.ipynb) | Member 1 |
| #54 | [M2-08] Missing values | [PR #59](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/59), [notebook](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/notebooks/02_cleaning.ipynb) | Member 1 |
| #55 | [M2-09] Both targets | [PR #59](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/59), [notebook](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/notebooks/02_cleaning.ipynb) | Member 1 |
| #56 | [M2-10] Invalid and extreme records | [PR #59](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/59), [notebook](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/notebooks/02_cleaning.ipynb) | Member 1 |
| #57 | [M2-11] Before/after cleaning summary | [PR #68](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/68), [notebook](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/notebooks/02_cleaning.ipynb) | Member 1 |
| #58 | [M2-12] Processed dataset v1 and handoff | [PR #68](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/68), handoff comments on #42, #43, #37 | Member 1 |
| #61 | [M2-13] Aggregated tables for EDA | [PR #62](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/62), [monthly_tag_tables.csv](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/data/processed/monthly_tag_tables.csv) | Member 1 |
| #69 | [M2-14] Sampling robustness check | [PR #72](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/72), [notebook](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/notebooks/02b_sampling_robustness.ipynb) | Member 1 |
| #70 | [M2-15] Cleaning section for the main notebook | [fresh-clone check](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/issues/70) | Member 1 |
| #71 | [M2-16] Cleaning slides and rehearsal | [PR #73](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/73) | Member 1 |
| #74 | [M2-VIVA] Viva questions | [m2_viva.md](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/reports/review1/m2_viva.md) | Member 1 |

## Key outputs
- [src/enrich.py](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/src/enrich.py): batched, hashed, resumable enrichment (answers.parquet 302,032 rows, users.parquet 220,943 rows; 8,462 API calls, none failed).
- [src/cleaning.py](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/src/cleaning.py) and [notebooks/02_cleaning.ipynb](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/notebooks/02_cleaning.ipynb): 309,179 collected rows to 302,026 cleaned rows, 39 columns (questions_clean_v1.parquet, shared on the team drive).
- [monthly_tag_tables.csv](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/data/processed/monthly_tag_tables.csv): 1,168 weighted tag-months, 137 flagged low-sample.
- [notebooks/02b_sampling_robustness.ipynb](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/notebooks/02b_sampling_robustness.ipynb) and [docs/sampling_limitations.md](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/docs/sampling_limitations.md).
- [Cleaning slides](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/reports/review1/m2_cleaning_slides.md), [requirements.txt](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/requirements.txt), derived-field list for the data dictionary ([comment on #22](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/issues/22)).

## Decisions I made and why
- No accepted answer means target 0, not missing: it is a real outcome, and dropping them would remove every unresolved question.
- Missing account age is imputed with the pre-2025 median plus a flag: uses training-period data only, so nothing leaks from the test period.
- Cross-tag duplicates keep the smaller sampling weight: the more conservative estimate of how many real questions the row represents.
- No row is removed based on a target; only empty, mostly non-English or spam posts are removed, and long bodies are capped rather than dropped.
- Raw HTML body is dropped from v1 (plain_body and code_text kept) and v1 is shared on the drive: it is 316 MB, over GitHub's 100 MB file limit.
- Second-seed check ran in a scratch folder with a window ending 2024-12: leaves Member 1's files untouched and avoids re-collecting the fully collected years.

## Reviews I gave
- #15 ([M3-01] problem statement), #38 ([M3-05] first look at the test-pull data): checked the files and re-ran the audit independently; the review comments list what was verified.

## Problems faced and how I solved them
- The new minimal API filters broke the first-answer call (/questions/{ids}/answers used the questions filter): passed the answers filter explicitly (PR #50) and reported the cause to Member 1, who fixed `_pick_filter`.
- A clean install of main failed because collect.py imports yaml but requirements.txt did not list it: pinned pyyaml in PR #26.
- Enrichment crashed when a batch returned nothing (empty frames had the wrong dtype): typed the empty frames and added a test (PR #63).
- Overlapping tags would have repeated API calls: the run now skips questions and askers already enriched, which cut the run to 6,024 calls for 12 tags.
- The API quota is counted per IP, so a second key gave no extra calls: planned the run to fit the single daily quota.
- Account age came out negative for 92 askers whose account is newer than their question: clipped at 0 and documented.

## What I can explain in the viva
- How each cleaning step works and why (merge and weights, UTC checks, HTML and code extraction, missing values, both targets, maturity rule, invalid records).
- Why unresolved questions are target 0 and why acceptance is only a proxy for resolution.
- How the sampling is weighted and how the robustness check shows trends are not distorted (yearly volume within 2%, second seed within 0.3 to 0.7 points).
- How enrichment protects privacy: IDs hashed with SHA-256 and a secret salt immediately after fetching; only the hash is stored.
- Another member's area: the request function in collect.py (backoff, retries, caching, minimal per-endpoint filters) and the leakage rule for features.
