> Historical handoff/audit snapshot. Current status and corrections evidence: `reports/review2/readiness_checklist.md`, `verification.json` and `board_audit_corrections.json`.

# Review 2: Adhikkesh and Rishiikesh execution and handoff

Publish Rishiikesh's work first on `m2/review2-text-mining`. After his PRs are merged, publish Adhikkesh's work on `m5/review2-forecasting`, created from updated main. No commits or staged changes are created by the implementation scripts; each member's file groups are kept separate.

## Order and dependencies

1. **Adhikkesh/M5:** prepare complete weekly series and masked monthly rates. Give `reports/review2/ts/series_long.csv` and `monthly_rates_masked.csv` to Akshay/M3 immediately.
2. **Rishiikesh/M2:** prepare prose-only corpus and 2,000-question sample. Give the full ignored corpus through Drive and the sample/code to Nishanth/M4 immediately.
3. **Parallel:** M5 validates models, backtests, forecasts, and exports diagnostics; M2 scores tone and measures complexity. M3 patterns and M4 topic models can proceed separately.
4. Give method CSVs, figures, notebook sections, schemas, and one-sentence chart captions to Abhinav/M1. Give findings to Akshay/M3 for the report/combined recommendations.
5. Complete human-dependent checks as independent labels/results arrive. Rebuild figures, notebooks and slides from the result files after these updates.

## Reproduction

Install `requirements-review2-members.txt` in a Python environment; install the spaCy `en_core_web_sm` model and NLTK `cmudict` pronunciation dictionary. The current session installed extra packages temporarily at `/tmp/review2-deps`; that path is a session convenience, not a deployment requirement.

```bash
python -m spacy download en_core_web_sm
python -m nltk.downloader cmudict
python -m src.ts_forecast --prepare-only
python -m src.text_prep --processes 2
python -m src.sentiment
python -m src.complexity
python -m src.ts_forecast
python -m src.review2_deliverables
python -m nbconvert --execute --to notebook --inplace notebooks/07_timeseries.ipynb notebooks/08_text_mining.ipynb
python -m unittest discover -s tests -p 'test_ts_forecast.py' -v
python -m unittest discover -s tests -p 'test_text_review2.py' -v
python -m src.check_review2_handoffs
```

Corpus and readability processing save private checkpoints under `data/processed/.review2_cache/`. Do not run two corpus jobs against the same checkpoint. Corpus checkpoints verify the input question text fingerprint before reuse.

Slides are created from saved `slide_data.json` files with `node src/make_review2_member_slides.js` (requires `pptxgenjs`). Regenerate them after refreshing deliverables. The plotting and notebook scripts run with the pinned Python dependencies; no temporary package path is required in a properly installed project environment.

For a member-only checkout, use `python -m src.review2_deliverables --member m2` and `node src/make_review2_member_slides.js --member m2` (or `m5`). This keeps partial PRs independently reproducible without requiring the other member's result files.

## M5 contracts and interpretation

- `series_long.csv`: `tag, week_start, count, log_count, share_of_all`; 400 Tuesday-start weeks x 14 series. Monthly rate observations remain in a separate monthly file, never falsely upsampled to weekly outcomes.
- SARIMAX orders are selected by AIC on dates before July 2024. The model family is selected using forecast targets in July–December 2024 only; the four horizons are averaged equally. No 2025–26 backtest origin informs these choices.
- An origin denotes the **first predicted week**; every training date is strictly earlier. Origins start 2025-01-07 and advance four weeks. Metrics evaluate the endpoint of each 1/4/13/26-week forecast.
- MASE uses the mean one-step absolute count difference in that origin's training history. sMAPE is in percent; RMSE is on the log1p scale. These are not classification accuracy or `100 - MAPE`.
- `backtest_metrics.csv` retains all successful fits and gives skill against naive on matched origins. `backtest_summary_matched.csv` is the main comparison table: all models are scored on the same successful origin/horizon cells. Fit failures remain visible in `fit_failures.csv`.
- `model_choices.csv` records validation selection. `backtest_winners.csv` is retrospective, not used to choose final models. `diebold_mariano.csv` uses paired scaled absolute errors and HAC uncertainty for overlapping horizons (small-sample t approximation).
- `forecasts_26w.csv` contains every successful model's weekly forecast through 2027-02-23 and 80/95% prediction bands. The point forecast is the back-transformed log median, not the arithmetic count mean. Baseline bands use training residual dispersion; ETS/SARIMAX bands are model-based. Coverage is measured, not assumed to match its nominal level.
- Tag classification uses forecast week 26 relative to the last observed count: below -40% steep decline, -40% through -10% declining, above -10% stabilising. A last count of zero has undefined percent change and is explicitly not classified; 0-to-0 is not a 100% decline.
- Half-life uses the fitted post-2023 log1p slope: strictly it is the half-life of count+1, a descriptive approximation for volume. The load index compares average forecast counts against the 2025 mean.
- Akshay's `its_results.csv` is still required to place ITS slope changes alongside forecast classes. It does not block forecasts. Residual checks and failure tables must accompany any forecast claims.
- GRU is an optional appendix. The baseline/ETS/SARIMAX backtest is the required task; no GRU result is invented.

## M2 contracts and interpretation

- Corpus columns: `question_id, created_at, period, tags, sampling_weight, target_resolved_7d, clean_text, n_tokens`. Title HTML entities are unescaped; code is excluded; technology tokens are protected; prose is lemmatised with spaCy. Stopwords and technical replacements are written to JSON.
- Periods: pre through October 2022; transition November–December 2022; post from January 2023. Transition is excluded from the pre/post contrast.
- Corpus statistics retain and report empty documents. M4 should omit empty documents from fitting while reporting them; maintain ID alignment when transforming topic weights.
- Tone uses original title + prose with punctuation, not stopword-stripped corpus or code. Technical words receive explicit neutral scores. VADER is exploratory until the independent human validation is complete.
- Per-question tone and complexity are saved locally as ignored parquet files. These are the inputs M4/M5 need for the optional text-feature classifier experiment; aggregate monthly tables are not sufficient.
- All study-tag membership uses full tags, restricted to the 13 study tags. ALL includes each question once. Aggregate shares/medians preserve sampling weights. Monthly rows with fewer than 30 questions are flagged `low_sample`.
- Complexity confidence intervals use 1,000 question resamples, retaining original sampling weights. Compressing identical value/weight cells gives the same bootstrap distribution without duplicating millions of rows.
- `tone_resolution_association.csv` is exploratory weighted logistic regression with full study-tag indicators and year controls, robust standard errors, and neutral tone as the reference. Associations are not causal effects.
- Topic example titles and time-to-first-answer metadata are not in the corpus. M4 should join the existing cleaned dataset by `question_id`; use `question_metadata_for_topics.parquet` for this join.

## Human and other-member inputs still needed

1. **Tone validation (M2 + M3):** fill `tone_validation_sample.csv` independently: `label_m2`, `label_m3`, then `agreed_tone`. There are 100 pre and 100 post questions. Read linked original prose, ignoring code. The written rule is in `tone_method.json`. No AI predictions are presented as human labels. Once all 200 are labelled, run:

   ```bash
   python -m src.sentiment --validate reports/review2/text/tone_validation_sample.csv
   python -m src.review2_deliverables
   ```

2. **Topic naming (M2 + M4):** Nishanth must produce each topic's top words and linked titles before Rishiikesh names the topics independently. That task cannot be completed before the topic model exists.
3. **Integrated tag interpretation (M3 + M5):** Akshay supplies ITS level/slope estimates and confidence intervals. M5 forecasts are already independent of this input.
4. **Optional classifier feature check:** requires training-only fitted topic features from M4 as well as per-question tone/complexity. Fitting NMF on the full 2019–2026 corpus and using it in the Review 1 classifier would leak later text into training. Fit the classifier's vectorizer/topic model on its training period only. Its already examined test period is not used to tune new features.
5. Dashboard deployment, final combined notebook/report and the team deck are M1/M3 tasks, not claimed as completed by M2/M5.

## Files to commit under each identity later

**Rishiikesh:** `src/text_prep.py`, `src/sentiment.py`, `src/complexity.py`, `tests/test_text_review2.py`; text result files, text development sample, `notebooks/08_text_mining.ipynb` Part A; M2 slides/findings/contribution/viva files. Full corpus and per-question features are ignored and go through Drive.

**Adhikkesh:** `src/ts_forecast.py`, `tests/test_ts_forecast.py`; time-series result files, `notebooks/07_timeseries.ipynb` Part B; Review 1 superseded-results note; M5 slides/findings/contribution/viva files.

**Shared infrastructure:** `src/review2_common.py`, `src/review2_deliverables.py`, `src/check_review2_handoffs.py`, `src/make_review2_member_slides.js`, `.gitignore`, this handoff guide and `requirements-review2-members.txt`. The publication helper assigns each file once: corpus utilities go with Rishiikesh first, presentation-generation utilities with his final PR, and combined verification/publication notes with Adhikkesh's final PR. See `docs/review2_git_commands.md`. Do not stage the entire working tree under one identity accidentally.
