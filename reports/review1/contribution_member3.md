# Review 1 Contribution Summary: Member 3 (Akshay Krishna, Register number: CB.SC.U4CSE23403)

Role: Problem framing, background research, exploratory data analysis, and business findings
Rubric components owned: Exploratory data analysis (3 marks); problem statement, business objectives and research questions; the EDA and framing sections of the Review 1 presentation deck; business findings integration

---

## Tasks Completed

| Issue | Title | Evidence link | Reviewed by |
|:---|:---|:---|:---:|
| #15 | [M3-01] Problem statement, business objectives and research questions | [PR #17](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/17), [docs/problem_statement.md](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/docs/problem_statement.md) | Member 1 |
| #16 | [M3-02] Background sources and dated event list | [PR #28](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/28), [docs/background_sources.md](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/docs/background_sources.md) | Member 2 |
| #29 | [M3-03] EDA plan (chart-to-research-question mapping) | [PR #34](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/34), [PR #41](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/41), [docs/eda_plan.md](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/docs/eda_plan.md) | Member 2 |
| #38 | [M3-05] First look at the test-pull data | [PR #39](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/39), [03_eda.ipynb](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/notebooks/03_eda.ipynb) (section `[M3-05]`) | Member 2 |
| #42 | [M3-06] Weekly question volume trends with milestone overlays | [PR #95](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/95), [03_eda.ipynb](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/notebooks/03_eda.ipynb) (volume-trends charts) | Member 2 |
| #43 | [M3-07] Target analysis and class balance | [PR #103](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/103), [03_eda.ipynb](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/notebooks/03_eda.ipynb) (`[M3-07] Target analysis`) | Member 5 |
| #44 | [M3-08] Time to answer distributions | [PR #107](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/107), [03_eda.ipynb](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/notebooks/03_eda.ipynb) (`[M3-08] Time to answer`) | Member 2 |
| #45 | [M3-09] Resolution by question characteristics | [PR #107](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/107), [03_eda.ipynb](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/notebooks/03_eda.ipynb) (`[M3-09] Question characteristics and resolution`) | Member 2 |
| #46 | [M3-10] Asker account age, weekday and hour patterns | [PR #107](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/107), [03_eda.ipynb](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/notebooks/03_eda.ipynb) (`[M3-10] Asker and timing patterns`) | Member 2 |
| #47 | [M3-11] Statistical checks and effect sizes | [PR #107](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/107), [03_eda.ipynb](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/notebooks/03_eda.ipynb) (`[M3-11] Statistical checks`) | Member 2 |
| #48 | [M3-12] EDA summary and feature recommendations | [PR #107](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/107), [03_eda.ipynb](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/notebooks/03_eda.ipynb) (`[M3-12] EDA summary and feature recommendations`) | Member 2 |
| #109 | [M3-13] Initial business findings (with Member 5) | [PR #110](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/110), [initial_findings.md](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/reports/review1/initial_findings.md) | Member 2 |
| #112 | [M3-14] Member 3 contribution summary, EDA slides and viva sheet | this document, [m3_eda_slides.md](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/reports/review1/m3_eda_slides.md), [m3_viva.md](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/reports/review1/m3_viva.md) | Member 1 |

### How to trace the commits

Every row above is authored by me (git author `Akshay Krishna <akshaypskrishna@gmail.com>`) and merged by a teammate, so `git log --author="Akshay Krishna" --oneline` reproduces the whole list. Two entries need explaining so the trail does not look incomplete:

* **#15 (problem statement)** was the repository's first documentation PR, so it was pushed on Member 1's `m1/problem-statement` branch and merged as PR #17. The file `docs/problem_statement.md` is entirely my work.
* **#45, #46, #47 and #48** were developed on their own `m3/question-characteristics`, `m3/asker-and-timing-patterns` and `m3/statistical-checks` branches, which were then stacked and pushed together on `m3/time-to-answer-new`. They therefore share PR #107, which added 1,009 lines to `notebooks/03_eda.ipynb`. There is no separate PR number for those four issues.

---

## Key Outputs

- **[docs/problem_statement.md](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/docs/problem_statement.md)**: the framing document for the whole project — problem statement, business objective, stakeholder matrix (Q&A platform product team, company developer-forum managers, DevRel teams) and five research questions, of which RQ1-RQ3 are the Review 1 scope and define the two targets (`target_resolved_7d`, `target_answered_7d`).
- **[docs/background_sources.md](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/docs/background_sources.md) and [docs/event_list.csv](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/docs/event_list.csv)**: three credible external sources with the exact figures used (1,336,266 questions in 2022 to 108,981 in 2025; 1,442 in July 2026 against a 207,204 March 2014 peak; a 12% drop in daily visits attributed to ChatGPT in the ACM study) plus a machine-readable list of the four dated milestones that are overlaid on every time-series chart: GitHub Copilot GA (2022-06-21), ChatGPT launch (2022-11-30), Stack Overflow ChatGPT ban (2022-12-05), moderator strike (2023-06-05).
- **[docs/eda_plan.md](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/docs/eda_plan.md)**: the EDA contract agreed with the team before any chart was drawn — eight chart IDs (EDA-01 to EDA-08), each tied to a target research question, a named data asset, a visualisation type and a task owner. EDA-01 to EDA-07 are mine, EDA-08 is Member 1's coverage analysis. It also sets the rule that every chart title states the analytical takeaway and milestone dates are overlaid.
- **[notebooks/03_eda.ipynb](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/notebooks/03_eda.ipynb)** (`[M3-05]` to `[M3-12]`): the executed EDA notebook — 14 charts across my six analysis sections, each followed by a written takeaway, plus the executed test-pull audit and the `[M3-12]` insight synthesis. Inputs are `questions_clean_v1.parquet` (Member 2), `monthly_tag_tables.csv` (Member 2), `weekly_counts.csv` and `monthly_counts.csv` (Member 1), `sampling_manifest.csv` (Member 1) and `docs/event_list.csv` (mine).
  * *`[M3-05]` test-pull audit*: 200-row, 21-column sample checked for missingness (125 missing `accepted_answer_id` confirmed to be genuine unresolved questions, not lost data), fully null fields (`protected_date`, `posted_by_collectives`, `migrated_from`), clean UTC timestamp conversion with zero `NaT`, and body-length outliers confirmed as genuine technical questions rather than spam. This produced two concrete recommendations for Member 2's cleaning pipeline: target logic for missing `accepted_answer_id`, and the one missing `owner_user_hash` to investigate.
  * *volume trends (#42)*: weekly volume per tag on a log scale with milestone overlays, site-wide share lines and an `openai-api` contrast line, showing the post-2022 collapse and the short-lived AI-API surge.
  * *`[M3-07]` target analysis*: class balance for both targets, monthly weighted resolution rate per tag with low-sample months greyed out, the weighted pre/post-November-2022 comparison table (resolved, answered, median hours to accept, `accepted_given_answered`), and the acceptance-habit trend line across 92 months.
  * *`[M3-08]` time to answer*: log-scale violin and box plots of hours to first answer versus hours to accepted answer, overall and per tag, plus monthly weighted median trendlines either side of the cutoff.
  * *`[M3-09]` question characteristics*: resolution rate against code blocks, error text, body-length bands, tag count and leading question word, with absolute counts printed on each bar.
  * *`[M3-10]` asker and timing patterns*: resolution rate by account-tenure bracket, new-versus-established accounts, and a weighted 7x24 UTC weekday-by-hour heatmap.
  * *`[M3-11]` statistical checks*: chi-square with Cramér's V, Mann-Whitney U with rank-biserial effect size, a Spearman correlation heatmap, and a p-value table for every feature.
  * *`[M3-12]` summary*: top-5 insights, each mapped to the Member 4 task that must implement it (`M4-05`, `M4-06`, `M4-07`) and to rows in `docs/feature_spec.md`.
- **[notebooks/review1_main.ipynb](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/notebooks/review1_main.ipynb)**: section 1 *Problem Formulation & Business Objectives* and section 4 *Exploratory Data Analysis* are written and owned by me (both are labelled *Lead: Member 3* in the notebook), with the loader stubs that pull the verified artefacts into the master deliverable.
- **[reports/review1/initial_findings.md](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/reports/review1/initial_findings.md)**: four business findings written from the EDA (code-inclusive posts, post-2022 delay and acceptance decline, new-account friction and timing, structural volume shift), each with a supporting metric, a named stakeholder and a suggested action, plus Member 5's model findings integrated underneath.
- **[reports/review1/m3_eda_slides.md](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/reports/review1/m3_eda_slides.md)**: the five slides I present in the team deck — I am the first speaker, covering the problem statement before Member 1's collection slides.
- **[reports/review1/m3_viva.md](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/blob/main/reports/review1/m3_viva.md)**: nine anticipated examiner questions with model answers for the framing and EDA sections.

---

## Decisions I Made and Why

1. **November 2022 is a cutoff, not a cause.** I fixed the pre/post boundary at the ChatGPT launch date recorded in `docs/event_list.csv` and drew it as a labelled vertical annotation on every time series. Nothing in the EDA claims AI adoption caused the decline: our own background source (Pragmatic Engineer, in `docs/background_sources.md`) shows volume already falling well before 2022, and the external studies are correlational. All findings are worded as *associated with* or *consistent with*.
2. **An accepted answer within 7 days is the primary target, and I report the secondary target next to it everywhere.** 76.0% of questions get at least one answer within 7 days but only 42.7% are accepted. Reporting only the primary number would hide that acceptance depends on the asker returning, so the pair is always shown together and `accepted_given_answered` is tracked as a separate KPI (57.0% pre-cutoff to 50.1% after).
3. **Monthly rates are weighted, not raw counts.** Because Member 1 sampled roughly 6.5-7.5% of days before 2025 and switched to a 100% census in 2025, raw monthly counts are not comparable across the boundary. Every monthly trend uses the sampling weights from `monthly_tag_tables.csv`, which reproduce population volume with under 1% annualised error, so the 2025 point is not inflated purely by collection intensity.
4. **Low-sample months are flagged, not deleted.** Months with fewer than 30 sampled questions are drawn in grey and marked using Member 2's `low_sample` flag rather than dropped, so the gap stays visible instead of being silently smoothed away.
5. **Log scales where the effect is multiplicative.** Weekly volume charts are log-scaled (the collapse spans orders of magnitude and a linear axis hides the early years) and time-to-answer violins use $\ln(1 + \text{hours})$ (the distributions are heavily right-skewed).
6. **The headline volume claim comes from the population series, not our sample.** Weekly volume is read from the site-wide `ALL` series in `weekly_counts.csv`, which Member 1 collected with `filter=total`, so the ~90% decline cannot be an artefact of which tags or which days we happened to sample.
7. **Report effect sizes next to p-values, never p-values alone.** With 302,026 rows every feature is significant at $p < 0.001$, so significance carries no information. The useful output is the size: Cramér's V below 0.11 for the categorical features and absolute Spearman correlations below 0.12 for the numeric ones, which honestly tells Member 4 that these features are weak on their own.
8. **`answer_count` is the strongest correlate and must still be excluded.** It has the largest effect size found anywhere in the EDA (rank-biserial $-0.35$, Spearman $0.33$ against the primary target and $0.65$ against the secondary target), but it is only known after answers arrive, so it is a forbidden field in `docs/feature_spec.md`. I flagged this explicitly so nobody "improves" the model with it later.
9. **The two targets are strongly intercorrelated (Spearman 0.48)**, which is why the secondary-target check in evaluation is reported separately: the two targets are not independent confirmations of each other.
10. **The EDA hands over named features, not vague advice.** Each of the top-5 insights points at a specific feature and a specific Member 4 task: code blocks and error text into `n_code_blocks`/`has_error_text`, account maturity into `new_account`/`account_age_days`/`missing_account_age`, timing into `hour_posted`/`weekday_posted`/`month_posted`, tag shifts into **lagged** `lagged_tag_volume` (4 full weeks before posting, so no future information enters the feature), and title semantics into `title_tfidf_svd_*` fitted on training data only.
11. **The first thing I did with the data was an audit, not a chart.** The `[M3-05]` test-pull pass ran before any visualisation so that Member 2's target logic was confirmed against real missingness patterns instead of being assumed.

---

## Reviews I Gave

- **#109 (initial business findings, with Member 5)** — PR #110: I authored the four EDA findings and reviewed Member 5's model section in the same document. My check was that every finding carries a metric traceable to `notebooks/03_eda.ipynb`, a named stakeholder and a suggested action, and that the AI-related wording stays associational.

---

## Problems Faced and How I Solved Them

- **The AI adoption story is confounded by a collection change.** The 2025 census makes raw counts jump for reasons that have nothing to do with behaviour. Fixed by using sampling-weighted rates throughout and by sourcing the headline decline from the site-wide population series.
- **The EDA notebook is 2.8 MB because every chart is stored as an embedded PNG.** That makes diffs unreviewable, so each chart was added in its own commit tied to its issue, which keeps the merge readable even though the file itself is large.
- **Stacked branches collapsed four issues into one PR.** The `m3/question-characteristics`, `m3/asker-and-timing-patterns` and `m3/statistical-checks` branches were developed in parallel and pushed together, so #45-#48 all landed in PR #107. Recorded explicitly above rather than leaving four issues looking unmerged.
- **Feature suggestions can silently introduce leakage.** The most attractive EDA finding (answer count) and the most attractive time feature (current tag volume) are both unavailable or unsafe at posting time; both were routed to lagged or forbidden lists before Member 4 built the pipeline.
- **The first pass of the target and time-to-answer charts was built on sample data, not the full cleaned table.** The early commits on `m3/time-to-answer` are marked "Sample Data", so both sections were rebuilt against `questions_clean_v1.parquet` and pushed on `m3/time-to-answer-new`; only the rebuilt versions were merged. Related: scratch output during that work is why `data/testing/` was added to `.gitignore` in PR #95.

---

## What I Can Explain in the Viva

- **Why the target is an accepted answer within 7 days (168 hours) and how it differs from `target_answered_7d`**, with the 76.0% versus 42.7% figures and why acceptance is only a proxy for resolution.
- **Why November 2022 is the cutoff, where the date comes from, and why the whole analysis is correlational** — including the evidence that decline predates ChatGPT and the moderator-strike confound.
- **How sampling weights enter the EDA** and why weighted monthly rates are the only comparable series across the 2025 census switch.
- **How the EDA is structured against the research questions**: the `docs/eda_plan.md` matrix, EDA-01 to EDA-07, and why every chart carries a written takeaway.
- **Which features actually matter and which are noise**: effect sizes versus p-values, why every feature is significant at $n \approx 302{,}026$ and what that does and does not prove.
- **The `answer_count` trap**: strongest correlation in the data, forbidden as a feature, and how I convinced the team to keep it out.
- **How the EDA drove the feature specification**, including the lagged 4-week tag volume and TF-IDF fitted on training splits only.
- **Reading the time-to-answer violins**: why the log transform, why first answers cluster at zero while acceptances have a long tail, and which tags are slowest.
- **(Another member's area) Member 1's stratified day sampling and inverse-probability weights and SEDE cross-check; Member 2's cleaning and label-maturity rule; Member 4's chronological split and lagged features; Member 5's PR-AUC choice and rolling-origin evaluation.**