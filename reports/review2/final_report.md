# Stack Overflow in the AI Era: Review 2 final report

**Team:** Abhinav (M1), Rishiikesh (M2), Akshay (M3), Nishanth (M4), Adhikkesh (M5). **Scope:** RQ4 (topics and complexity) and RQ5 (technology forecasting). All numbers are generated from `reports/review2/` by `src/review2_final_report.py`.

## 1. Executive summary

- **Patterns and the 2022 break.** Trend dominates every series. On the log scale, all 14 series show a significant negative change in weekly growth after 2022-11-30 (ITS slope change -3.89% to -1.60% per week, 95% CI excluding zero), and the real break exceeds the 2021-11-30 placebo in 13 of 14 series.
- **Forecasts.** The 26-week site total is forecast to fall from 215 to 134 questions per week by February 2027 (-37.6%), with 6 tags classed steep decline and 5 declining under the fixed thresholds.
- **Topics.** NMF k=10 wins the pre-registered rule (coherence 0.2175, diversity 0.80, stability 1.00). Routine programming topics lose share while harder runtime and tooling topics gain: Python Execution & Runtime Errors rises +1.9 pp while Core Syntax, Arrays & Data Structures falls -3.5 pp.
- **Tone and complexity.** Questions are longer (+13 prose words) and more code-heavy (+4 code lines) after the break. Tone measures are exploratory: the frustration lexicon moves only -0.2 pp.
- **Recommendations.** Six combined recommendations follow, each citing one time-series and one text-mining number; the headline is to move moderation effort to the steep-decline tags and to route rising low-resolution topics to experts.

## 2. Data recap

- **Volume series.** 302,026 cleaned questions back a weekly series of 14 groups (ALL plus 13 study tags) x 400 complete Tuesday-start weeks, 2019-01-01 to 2026-08-25, with no missing weeks. The time-series method uses these complete counts, never the sampled records.
- **Rate series.** `data/processed/monthly_tag_tables.csv` holds the weighted monthly resolved rate, answered rate and median hours per tag. Months flagged `low_sample` are excluded from conclusions.
- **Text.** 302,026 questions; 165,887 distinct terms after cleaning; code removed from the prose field.
- **Weighting.** Before 2025 every question carries a sampling weight; any share, rate or count built before 2025 is weighted. From 2025 the weight is 1.
- **Periods.** Pre-AI 2019-01 to 2022-10, transition 2022-11 to 2022-12, post-AI 2023-01 to 2026-08. Event markers: GitHub Copilot GA (2022-06-21); ChatGPT Launch (2022-11-30); Stack Overflow ChatGPT Ban (2022-12-05); Stack Overflow Moderator Strike (2023-06-05).

## 3. Method 1: time series

**Preparation and implementation.** STL (robust, period 52) was fit to each log1p weekly count; the additive components satisfy trend + seasonal + residual = log count. Stationarity was tested with ADF (regression c, AIC) and KPSS on the level and the first difference, under a written verdict rule. Change points were found with `ruptures` PELT (l2 cost, minimum segment 26 weeks) and a BIC penalty fixed in advance, then compared with the four dated events. Interrupted time series were fit per series as segmented regressions of log count on week, a step at 2022-11-30 and a post-break slope, with two Fourier pairs, using OLS with Newey-West HAC errors (lag 4) and a 2021-11-30 placebo.

**Evaluation and interpretation.**

- **Seasonality is secondary.** Trend strength runs 0.86 to 1.00; seasonal strength runs 0.00 to 0.57. Yearly dips cluster in the late-December/January holiday weeks.
- **One difference is justified.** All 14 level series are non-stationary (ADF cannot reject a unit root, KPSS rejects stationarity), so every series is first-differenced (`d=1`), consistent with the M5 SARIMAX backtest. The first-difference tests conflict for 12 series and are reported as such, not hidden.
- **A genuine 2022 break.** The 134 detected breaks are mostly routine noise: 6 fall within four weeks of a dated event, across 4 series (`java`, `r`, `openai-api`, `sql`). The interrupted time series is sharper: all 14 series show a significant negative post-break slope, -3.89% to -1.60% per week, and the real effect exceeds the placebo in 13 of 14 series. 10 series also show a significant immediate level change, most extreme for `openai-api` (+1645%), which is a step, not a stable trend.
- **Forecast skill is earned at long horizons, not short.** On the 2025-26 rolling-origin backtest, SARIMAX's mean 26-week skill against naive is 55.9% while true 95% coverage is 52.0% (intervals too narrow). At one week ahead the best model reaches 15.7% skill and drift only 0.4%, so the naive baseline remains hard to beat over a single week, as expected.
- **Classes and business reading.** Under the fixed thresholds (5 declining, 2 not classifiable: zero baseline, 6 steep decline), the site total is forecast from 215 to 134 questions per week by February 2027 (-37.6%). `tag_classes.csv` adds a half-life and a 2025 index; zero-baseline tags cannot support a percentage class and are labelled as such.

![STL small multiples](ts/stl_small_multiples.png)

![Interrupted time series forest plot](ts/its_forest.png)

![Site-total forecast](ts/forecast_ALL.png)

## 4. Method 2: text mining

**Preparation and implementation.** The corpus of 302,026 questions was lowercased, lemmatised with spaCy and stripped of code, with technical words protected and stopwords and VADER overrides written down. Topics were fit by TF-IDF (unigrams and bigrams) on a stratified sample, with NMF and LDA compared across k under a rule fixed in advance (highest coherence among candidates with diversity at least 0.7 and stability at least 0.6). Tone used VADER plus a frustration and politeness lexicon; complexity measured prose length, code lines, code blocks, reading ease and structural flags. Shares and rates before 2025 are weighted.

**Evaluation and interpretation.**

- **NMF k=10 wins.** Coherence 0.2175, diversity 0.80, stability 1.00. LDA failed the rule on every k (coherence -0.381 to -0.206, stability at or below 0.28).
- **What moved to AI tools.** The largest falling topics are Core Syntax, Arrays & Data Structures (-3.5 pp), Pandas Dataframe & Data Manipulation (-1.1 pp), Web Frontend, DOM & User Events (-0.5 pp): routine syntax and dataframe lookups.
- **What people still bring to humans.** The largest rising topics are Python Execution & Runtime Errors (+1.9 pp), Docker Containers & Cloud Deployment (+1.5 pp), Android Mobile App & Gradle Build (+1.1 pp); the top rising topic resolves only 33.2% within seven days, the resolution bottleneck behind the expert-routing recommendation.
- **Vocabulary shift.** Rising terms include nextjs (z=127), encounter (z=122), vite (z=115), version (z=102), compose (z=95); falling terms include array (z=-129), list (z=-97), object (z=-95), dataframe (z=-82), like (z=-81) (Monroe log-odds with a Dirichlet prior).
- **Tone and complexity.** Negative tone share changed +2.7 pp and positive share -2.0 pp; the frustration flag changed -0.2 pp and is a lexicon measure, not verified emotion. Weighted median prose length changed +13 words and code lines +4, while questions spanning two or more study tags changed -3.4 pp.

![Topic model selection](text/topic_model_selection.png)

![Rising and falling words](text/keywords_shift_all.png)

![Tone and complexity](text/tone_complexity.png)

**Disclosed AI-assisted validation:** VADER was scored against all 200 existing M3 human labels: accuracy 36.0%, macro-F1 0.344. Separately, Codex AI annotations agreed with M3 on 58.0% of posts (human–AI Cohen's kappa 0.214). This is one human plus an AI, not two independent human raters or an adjudicated gold standard. VADER is weak against this reference; frustration flags remain the primary exploratory tone proxy. Ten disclosed AI topic-name proposals and qualitative comparisons are in topic_naming_comparison.csv; topic 2 is mixed. The original human M2 labels, two-human kappa and human topic-naming agreement remain unavailable.

## 5. Combined insights and recommendations

Each recommendation below needs both methods at once and cites at least one time-series and one text-mining number. Every number is read from `reports/review2/`; the machine-readable matrix is `insight_matrix.csv`.

**1. Moderate the tags that are still falling fastest, and stop staffing the slower-declining ones.**

- *Time series:* ITS post-slope declines are steepest for fastapi -3.89%/wk, reactjs -3.28%/wk, pandas -2.90%/wk; the mildest are excel -1.92%/wk, java -1.74%/wk, android -1.60%/wk (its_results.csv). 6 of 13 tags are classed steep decline by the 26-week forecast.
- *Text mining:* Site-wide frustration share changed -0.2pp after the break (tone_prepost.csv).
- *Action:* Reallocate moderation hours from stabilising tags to the steep-decline tags, and refresh the forecast each quarter.
- *Stakeholder:* Q&A platform product team  |  *KPI:* Moderation hours per 1,000 questions on steep-decline tags
- *Caveat:* The break is associated with, not caused by, AI adoption; slope ranks are model-based.

**2. Turn rising setup, version and migration language into a documentation backlog.**

- *Time series:* The tags with rising version/setup keywords are still declining: python -2.34%/wk; javascript -2.46%/wk (its_results.csv).
- *Text mining:* Rising per-tag keywords include python: version (rank 7), toml (rank 19), pyproject (rank 25), pyproject toml (rank 27); javascript: version (rank 16) (keywords_prepost.csv).
- *Action:* Promote these rising version/setup keywords into the DevRel guide backlog for the tags that show them.
- *Stakeholder:* DevRel teams  |  *KPI:* Guides shipped against the rising-keyword backlog
- *Caveat:* Keyword frequency is a proxy for demand, not a direct measure of documentation need.

**3. Route topics that gain share but resolve poorly to an expert queue.**

- *Time series:* The Python Execution & Runtime Errors topic rises +1.85pp site-wide (topic_prepost.csv) while python post-slope is -2.34%/wk (its_results.csv).
- *Text mining:* Python Execution & Runtime Errors resolves at 33.2% within 7 days (topic_outcomes.csv).
- *Action:* Send rising, low-resolution topics to an expert routing queue with topic tags.
- *Stakeholder:* developer-forum managers  |  *KPI:* 7-day resolved rate and time-to-first-answer on routed topics
- *Caveat:* NMF topics are coarse; a question can span several topics.

**4. Give first-time askers a guided template where frustration is rising and new accounts resolve less.**

- *Time series:* Frustration share rose only for reactjs +0.5pp, openai-api +0.5pp, pandas +0.2pp and fell slightly site-wide (-0.2pp, tone_prepost.csv); python and javascript still decline (-2.34 and -2.46%/wk, its_results.csv).
- *Text mining:* Review 1 SHAP ranks account_age_days second of all features (mean |SHAP| 0.125), so account age matters almost as much as tag volume (shap_top.csv).
- *Action:* Add a guided question template for first posts, prompted when the frustration flag is set.
- *Stakeholder:* Q&A platform product team  |  *KPI:* 7-day resolved rate for first posts
- *Caveat:* The template is a UX intervention; its effect is not identified by the pre/post analysis.

**5. Trigger a review when weekly volume leaves the forecast band.**

- *Time series:* The 26-week forecast carries a 95% band; for ALL the week-26 band is 89-201 around 134 (forecasts_26w.csv).
- *Text mining:* Falling topics such as Core Syntax, Arrays & Data Structures signal where traffic is moving (topic_prepost.csv).
- *Action:* Alert the analytics lead when a tag closes a week outside its 95% forecast band.
- *Stakeholder:* Q&A platform product team  |  *KPI:* Shares flagged and reviewed per quarter
- *Caveat:* Bands are wide for volatile tags, so alerts are a prompt to look, not a conclusion.

**6. Treat openai-api as an emerging tag: a step change without a stable trend.**

- *Time series:* openai-api shows a +1645% level change but a -2.56%/wk post-slope, with a 33-week half-life and no classifiable 26-week change (its_results.csv, tag_classes.csv).
- *Text mining:* Docker and Android topics also gained share site-wide (topic_prepost.csv), the same emerging-stack pattern.
- *Action:* Monitor openai-api monthly and review routing and tagging once a baseline exists.
- *Stakeholder:* developer-forum managers  |  *KPI:* Weekly openai-api volume versus its forecast band
- *Caveat:* A single level jump does not imply a lasting slope change.


## 6. Dashboard guide

The interactive dashboard (Streamlit with Plotly, owned by M1) has seven pages, all responding to shared sidebar filters (tag, date range, period, event markers, linear/log). Pages 2, 3, 4, 5 and 6 read the method outputs directly; page 1 shows the overview and page 7 the question-triage what-if.

| Page | Owner | Reads |
|---|---|---|
| 1. Overview | M1 | `ts/series_long.csv`, `data/processed/monthly_tag_tables.csv` |
| 2. Patterns and the 2022 break | M3 | `ts/stl_components.csv`, `ts/changepoints.csv`, `ts/its_results.csv` |
| 3. Forecasts | M5 | `ts/forecasts_26w.csv`, `ts/backtest_*.csv`, `ts/tag_classes.csv` |
| 4. Topics | M4 | `text/topics_top_terms.csv`, `text/topic_monthly_share.csv`, `text/topic_prepost.csv`, `text/topic_outcomes.csv` |
| 5. Tone and complexity | M2 | `text/tone_*.csv`, `text/complexity_*.csv`, `text/keywords_prepost.csv` |
| 6. Recommendations | M3 | `recommendations.csv` |
| 7. Question triage (stretch) | M5 + M1 | saved model, title and error-text inputs |

- **Public link:** TODO(M1): public Streamlit URL
- **Screenshots:** TODO(M1): screenshots of the seven dashboard pages

Questions show titles only, each linked to `https://stackoverflow.com/q/<id>`, with a CC BY-SA 4.0 licence notice. No bodies and no user hashes are shown.

## 7. Limitations

1. **Weights before 2025.** Sampling weights apply only before 2025; later counts are unweighted.
2. **Thirteen tags.** Only the 13 study tags plus ALL are covered, so the picture is not the whole site.
3. **Acceptance is a proxy.** Resolution means an accepted answer within seven days, not a satisfied asker.
4. **VADER is general purpose.** The tone model is a general lexicon with overrides; the frustration flag is exploratory and its validation is pending.
5. **Topics are English prose.** Topic modelling uses cleaned English prose only; code and non-English text are excluded.
6. **Forecasts during a steep decline are uncertain.** SARIMAX 95% intervals covered only 52.0% of endpoints, and 10 fits failed.
7. **Association, not cause.** Every result is associated with or consistent with AI-adoption timing; nothing is caused by it. The pre/post boundary is a comparison date, and the placebo break is included for honesty.
8. **Pending human checks.** Independent tone labels and topic-naming agreement are not yet available and are not claimed.

## 8. How to reproduce

```bash
pip install -r requirements.txt
python -m src.ts_patterns --task all          # STL, stationarity, change points, ITS   -> reports/review2/ts/
python -m src.ts_forecast                     # baselines, backtest, forecasts          -> reports/review2/ts/
python -m src.topics                          # topics, keyword shift                   -> reports/review2/text/
python -m src.sentiment && python -m src.complexity   # tone and complexity             -> reports/review2/text/
python -m src.review2_m3_insights             # insight_matrix.csv, recommendations.csv
python -m src.review2_final_report            # final_report.md and final_report.pdf
jupyter nbconvert --execute --to notebook --inplace notebooks/07_timeseries.ipynb
jupyter nbconvert --execute --to notebook --inplace notebooks/08_text_mining.ipynb
```

Every heavy step writes to `reports/review2/`; the notebook, dashboard and this report read those files, so a changed CSV changes every downstream number. The final notebook for the submission is `notebooks/review2_main.ipynb` (M1).

## 9. Contributions and board link

| Member | Role | Summary |
|---|---|---|
| M1 Abhinav | Dashboard, final notebook, repo and board | `reports/review2/contribution_member1.md` (TODO) |
| M2 Rishiikesh | Corpus, tone, complexity | `reports/review2/contribution_member2.md` |
| M3 Akshay | Patterns, ITS, combined insights, final report, deck | `reports/review2/contribution_member3.md` (TODO) |
| M4 Nishanth | Topics, keyword shift, evaluation | `reports/review2/contribution_member4.md` |
| M5 Adhikkesh | Forecasts, backtest, tag classes | `reports/review2/contribution_member5.md` |

- **Board:** TODO: GitHub project board link
- **Repository:** TODO: repository link
- **Kaggle notebook:** TODO: Kaggle notebook link
