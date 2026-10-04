# Review 1 Contribution Summary: Member 1 (Abhinav Gopalakrishnan, Register number: CB.SC.U4CSE23___ , fill in)

Role: Data Collection, API Architecture, Sampling Design & Project Management Lead  
Rubric components owned: Dataset documentation and collection (2 marks); GitHub Project Board and repository management; SEDE cross-validation; EDA coverage analysis (part of 3 marks)

---

## Tasks Completed
| Issue | Title | Evidence link | Reviewed by |
|:---|:---|:---|:---:|
| #1 | [M1-00] Rubric and project plan reading | Repository & Project Plan | Self / Team |
| #2 | [M1-01] Repository, folder structure & README | [Commit history](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/commits/main) | Member 4 |
| #3 | [M1-02] GitHub Projects board setup | [Project Board](https://github.com/users/Abhinav-Gopalakrishnan/projects/1) | Member 4 |
| #4 | [M1-03] Stack Apps key & first API call | [PR #4](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/4) | Member 4 |
| #19 | [M1-04] Core API request function | [PR #17](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/17) | Member 4 |
| #35 | [M1-04b] Mask ID lists in log & minimal filters | [PR #40](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/40) | Member 4 |
| #20 | [M1-05] Test pull and volume check | [PR #27](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/27) | Member 4 |
| #21 | [M1-06] Weekly question counts | [PR #64](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/64) | Member 4 |
| #22 | [M1-07] Question records with stratified sampling | [PR #49](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/49) | Member 4 |
| #23 | [M1-08] Collection summary & telemetry audit | [PR #77](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/77) | Member 4 |
| #78 | [M1-09] SEDE cross-check & headline figures | [PR #79](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/79) | Member 4 |
| #80 | [M1-10] Data dictionary | [PR #81](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/81) | Member 4 |
| #82 | [M1-11] Dataset documentation | [PR #83](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/83) | Member 4 |
| #84 | [M1-12] Dataset coverage charts | [PR #85](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/85) | Member 4 |
| #86 | [M1-13] Re-runnable collection & config | [PR #87](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/87) | Member 4 |
| #88 | [M1-14] review1_main.ipynb skeleton | [PR #89](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/89) | Member 4 |
| #90 | [M1-16] Data collection presentation slides | [PR #91](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/91) | Member 4 |
| #93 | [M1-VIVA] Viva questions on collection & sampling | [reports/review1/m1_viva.md](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/reports/review1/m1_viva.md) | Member 4 |

---

## Key Outputs
- **`src/collect.py` & `src/collect_questions.py`**: Robust, authenticated Stack Exchange API v2.3 client with client-side rate limiting ($0.5\text{s}$), deterministic SHA-256 request caching, automatic exponential backoff retry on HTTP 502s, and the critical `has_more=False` page+1 probing fix.
- **`src/collect_weekly.py` & `data/processed/weekly_counts.csv`**: Complete 5,600-row weekly population dataset across 14 series (13 tags + `ALL`) spanning 400 consecutive 7-day non-overlapping weeks from 2019 to 2026.
- **`data/shared/questions_*.parquet` & `data/processed/sampling_manifest.csv`**: 309,179 detailed question records across 13 target ecosystems with deterministic random seed tracking (`42`) and inverse-probability sampling weights.
- **`docs/data_dictionary.md` & `docs/dataset_documentation.md`**: Complete 70+ field dataset catalog (7 categories) and 12-section comprehensive methodology/ethics/limitations document.
- **`notebooks/01_collection.ipynb` & `notebooks/03_eda.ipynb` (Coverage)**: Reconciled offline telemetry audit (19,306 logged calls), SEDE cross-check (0.01% error), and dual coverage visualisations.
- **`notebooks/review1_main.ipynb`**: Review 1 master deliverable skeleton in exact rubric order.

---

## Decisions I Made and Why
1. **Stratified Day Sampling vs Simple Random Sampling**: Rather than sampling questions uniformly, we sampled full 24-hour days (1 weekday + 1 weekend day per month pre-2025). This avoids within-day diurnal bias, preserves temporal burstiness, and allows exact inverse-probability weighting ($w = \text{days of type in month} / \text{days sampled}$).
2. **Exhaustive 100% Census from 2025 Onward**: Switched from day sampling to full-census collection starting January 2025. Because site-wide volume had dropped by ~90%, capturing 100% of days was feasible within daily API quotas and eliminates sampling variance during the critical post-AI holdout evaluation window.
3. **Paging Bug Probe Rule**: Discovered that the Stack Exchange API returns `has_more=False` on page 1 of high-volume days even when more pages exist. Implemented an unconditional `page+1` probe rule until a genuinely empty response ($0\text{ items}$) is received, successfully recovering 3,222 missing questions for `reactjs` and 393 for `docker`.
4. **Strict User Privacy & Parameter Masking**: Hashed all user IDs with SHA-256 + secret salt before committing intermediate files, masked batched IDs in `logs/collection_log.csv` (`users/{ids}`), and applied custom minimal API filters (`base="none"`) to avoid collecting display names or profile images.
5. **Fixed Tuesday-Start 7-Day Weekly Windows**: Defined weekly counts as 400 fixed 7-day windows starting on Tuesday (2019-01-01), dividing the 2,800-day window ($400 \times 7$) without calendar fragmentation or partial week artifacts.

---

## Reviews I Gave
- **Member 2 (#5, #7, #8, #51–#58, #61, #69, #71)**: Reviewed and approved all PRs for the enrichment pipeline, cleaning notebook, monthly tag tables, and sampling robustness analyses, verifying 0 raw user ID leaks and clean top-to-bottom notebook execution.
- **Member 4 (#32, #33)**: Reviewed split strategy and candidate feature specification, ensuring strict leakage compliance and proper integration with lagged weekly volume counts.

---

## Problems Faced and How I Solved Them
- **Stack Exchange API Paging Bug (`has_more=False`)**: High-volume queries silently stopped after page 1. Diagnosed via population mismatch against `monthly_counts.csv`; resolved by probing `page+1` past `has_more=False`, ensuring complete pagination.
- **Docker Platform Gap**: Fully collected Docker 2025 months showed 6–19% fewer records than `filter=total`. Identified that `filter=total` counts locked/deleted questions that the paged API endpoint never returns; verified code correctness and documented as an inherent platform limitation.
- **Daily API Quota Constraints**: Full weekly counts across 14 series required 5,600 calls. Engineered a resumable checkpointing system with `--key-env` supporting secondary key rotation (`STACK_API_KEY_BACKUP`) without downtime or rate-limit violations.
- **Merge Conflicts in Shared Audit Log (`logs/collection_log.csv`)**: As parallel branches logged API activity, Git merge conflicts arose. Built automated deduplication scripts that reconciled and merged logs chronologically by `timestamp_utc`, preserving full audit trails.

---

## What I Can Explain in the Viva
- **API Collection Architecture**: Backoff handling, rate limiting ($0.5\text{s}$), SHA-256 response caching, retry mechanisms, and minimal custom filter design.
- **Sampling Methodology**: Stratified random day selection (seed 42), inverse-probability weighting, 2025 exhaustive census switch, and mathematical equivalence to population volume within 0.01%.
- **SEDE Cross-Validation**: T-SQL queries on SEDE, reason for minor snapshot timing differences ($<0.5\%$), and verified headline metrics (2014 peak: 207k; 2022: 1.33M; 2025: 108k; July 2026: 1.4k).
- **Privacy Architecture**: SHA-256 HMAC pseudonymization with secret `HASH_SALT`, URL parameter masking in committed logs, and CC BY-SA 4.0 license compliance.
- **Another Member's Area**: Member 2's target definitions (`target_resolved_7d`, `target_answered_7d`), maturity cutoff rule ($>30\text{ days}$), and Member 4's lagged tag volume leakage safeguard.
