# Technical handoff: model and dashboard improvements

Branch: `codex/final-model-dashboard`. This is an implementation handoff, not the
final capstone report. Original Review 1/2 result files remain historical evidence.

## What changed

| Area | Implemented result | Evidence |
|---|---|---|
| Real classifier inference | A saved fitted XGBoost pipeline, training-fitted preprocessing, sigmoid calibration and threshold; input form runs the model and local tree SHAP | `src/predict.py`, `src/train_deployment.py`, `models/resolution_v2/` |
| Missing values and temporal separation | Missing account age restored to missing before fold-fitted median imputation; seven-day boundary gaps; calibration and threshold selection separated | `src/build_features.py`, `src/models.py`, `src/run_models.py` |
| Model evaluation | Separate August retrospective evaluation, confusion matrix, feature importance, subgroup metrics, calibration bins and review-capacity capture | `reports/final_validation/`, Dataset & Classification page |
| Scope and target | Explicit accepted-answer **posting-time** proxy; revision-history and acceptance-event limitations; current-date prediction blocked | Prediction page, metadata, data dictionary, README |
| Forecasts | Corrected sMAPE percentage display; actual-versus-forecast endpoints, stationarity and residual diagnostics, separate forward-period interval calibration diagnostic | Patterns and Forecasts pages; `interval_protocol.json` |
| Text mining | Strongest declining keywords, one complexity unit per chart, low-sample topic gaps, technology-specific linked examples, human-review worksheet and validator | Topics and Tone & Structure pages; `scripts/check_human_review.py` |
| Business use | Expert-routing cost/benefit calculator with lower/base/higher intervention-success assumptions and a same-capacity random-routing comparator | `dashboard/scenarios.py` |
| Dashboard | Eight named pages, reset controls, empty-result messages, explicit fixed versus filtered evidence, real live prediction | `dashboard/app.py` and page modules |
| Reproduction | Pinned runtime, input/model/export checksums, private-input restoration, tests, browser screenshots and run instructions | This document; `reports/final_validation/` |

## Run the application

Verified with Python **3.13.13**. From the repository root:

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install -r dashboard/requirements.txt
.venv/bin/python -m streamlit run dashboard/app.py
```

Open `http://localhost:8501`. The committed model and CSV bundle are sufficient;
API credentials and the full 302,026-row parquet are unnecessary for this demo.
The public application is https://stackoverflow-ai-era.streamlit.app/; see
`docs/dashboard_deploy.md` for deployment evidence. The final public data bundle
now restores the full parquet with `python scripts/submission_data.py --restore`;
see `data/README.md` and `docs/final_submission_guide.md`.

The model path is `models/resolution_v2/pipeline.joblib`. The app verifies its
checksum, caches the loaded model, and recomputes features, probabilities and an
explanation when Predict is clicked. Titles and question bodies entered into the
form are not written to files. Results remain in the browser's Streamlit session.

Historical posting dates must fall between **2019-02-26 and 2026-08-31**. Eight prior
complete weeks supply lagged tag features. New real-time deployment requires fresh
weekly data and a validation release. Forecast, topic and original evaluation
pages intentionally read precomputed analytical outputs; their selectors do not
retrain those methods.

## Revised classifier protocol

The target is positive if the answer accepted in the collected snapshot was
created within 168 hours of the question. This does not establish when the asker
accepted it, or whether the asker was satisfied.

| Stage | Period | Rows |
|---|---|---:|
| Training | Available history through 2024-12-24 | 248,137 |
| Sigmoid calibration | 2025-01-01–2025-03-31 | 17,643 |
| F1 threshold selection | 2025-04-08–2025-06-23 | 8,804 |
| Additional retrospective evaluation | August 2026 | 389 |

XGBoost settings were frozen from the original validation-selected model: depth
5, learning rate 0.0294479, 628 trees. No hyperparameter search used August outcomes.
The calibrated threshold is **0.2971**. August PR-AUC is **0.4892**, ROC-AUC **0.6198**,
F1 **0.5067**, and Brier score **0.2155** (raw probability Brier **0.2218**).

The original July 2025–July 2026 locked-test predictions were not recomputed.
Its PR-AUC of 0.4315 is preserved; comparing it directly with August's 0.4892
would conflate a model change with a different test period. August was previously
examined in Unit 3, so it is **not** a blind prospective holdout. No extra rounds
of tuning should be justified by these August results.

Question IDs are unique and the new periods have no question overlap. Returning
askers are present: 54 known August askers also occur in training. Identifiers are
excluded from features. This evaluates later platform questions, not exclusively
unseen askers. Counts are in `model_data_audit.json`.

Collected titles, text and tags can include later edits. A seven-day purge does
not repair that limitation or recover acceptance-event timestamps. The classifier
is a transparent historical demonstration with modest predictive performance.

## Forecast and business evidence

The forecast page shows the original saved bands and explicitly discloses their
undercoverage. The added inflation diagnostic uses only outcomes before January
2026 to estimate a factor, then evaluates origins from January 2026 onward.
For pooled SARIMAX 26-week endpoints, coverage is 58.5% before adjustment and 100%
after adjustment across **41** evaluation endpoints, with factor **3.594**. This
small, dependent retrospective evaluation is not a guarantee of future 95%
coverage, and the original future bands are not silently replaced.

At approximately 20% review capacity, the model ranked 58 proxy-negative cases
within 78 reviewed August questions; random routing expects about 50.93 at that
capacity. Identifying a proxy-negative case is not an intervention success.
The scenario calculator exposes success, review time, hourly cost, value and
model-operation cost as assumptions. Both policies use the same review capacity;
their shared review costs cancel in the incremental comparison. Poorer ranking
can produce a negative incremental value. No measured business savings are claimed.

## Reproduction and checks

For all analysis and tests, install `requirements-dev.txt`. The exact local
environment is recorded in `reports/final_validation/runtime_freeze.txt`.

```bash
.venv/bin/python -m pip install -r requirements-dev.txt
M5_DEVICE=cpu .venv/bin/python -m pytest tests -q
.venv/bin/python -m src.final_assets
```

The tests use synthetic data or committed evidence, mocked API requests and dummy
credentials. They require no live Stack Exchange access. The export tests refresh
their CSV destinations; use an isolated checkout/copy for verification if preserving
file timestamps matters. The completed run used a copy without `.env` or private
question data. See `verification.json` for final outcomes.

To intentionally train a new version from the separate full cleaned parquet:

```bash
# Refuses to overwrite the existing release; --replace is an intentional rebuild.
M5_DEVICE=cpu .venv/bin/python -m src.train_deployment
.venv/bin/python scripts/check_model_data.py
.venv/bin/python -m src.final_assets
```

The original notebook/model results are not regenerated by these commands. Keep a
copy of a released model and its metadata before intentionally replacing it.

Private text-model inputs have also been restored locally. Reproduce them from
the full cleaned parquet with the following commands; NLP resources require an
initial download:

```bash
.venv/bin/python -m spacy download en_core_web_sm
.venv/bin/python -m nltk.downloader -d .review2_nltk cmudict
.venv/bin/python scripts/restore_private_inputs.py corpus
.venv/bin/python scripts/restore_private_inputs.py tone
NLTK_DATA="$PWD/.review2_nltk" .venv/bin/python scripts/restore_private_inputs.py complexity
.venv/bin/python scripts/restore_private_inputs.py topics
.venv/bin/python scripts/check_topic_corrections.py
.venv/bin/python -m src.final_assets
```

Use spaCy model `en_core_web_sm==3.8.0` to match this restoration. The selected
seed-42 NMF model was reconstructed; the corpus fingerprint and every published
top-term list matched. The original 36-fit comparison was retained. Private
question-level files and caches remain gitignored. The source corpus is necessary
for a full topic-grid rerun, but not for the dashboard.

## Remaining work requiring people or new evidence

1. **Human topic review:** the worksheet contains 75 linked examples (five per
   topic). Read the source questions, record reviewer, judgement, reason and
   self-attestation, and validate the completed copy:

   ```bash
   .venv/bin/python scripts/check_human_review.py completed_review.csv --output review_status.json
   ```

   A valid worksheet is not proof of independent authorship. Human names or
   agreement results have not been invented. Topic names remain provisional.
2. **Tone validation:** the existing 200-question human reference still gives
   VADER accuracy 36%. A second independent human reviewer and adjudication are
   still absent. Tone stays exploratory and should not justify operational actions.
3. **Real-world claims:** predictive quality, forecast coverage and intervention
   benefit need prospective evaluation/pilots before operational use. Automated
   tests establish software behaviour, not scientific validity or business benefit.
4. **Viva and individual evidence:** each member must explain their actual work,
   verify their contribution records and rehearse the local app. No board tasks,
   contribution claims, signatures or external communications were fabricated.

The faculty format accepts a locally runnable Streamlit application, requires two
appropriate Unit 3 methods, and asks for explicit validation and limitations.
Time series and text mining already supply those two methods; association-rule
mining, a different dashboard framework, a new unrelated model and production
hosting are not necessary additions to this scope. Report authoring remains deferred.

## Demonstration sequence

1. Overview: distinguish API weekly totals from the weighted question sample;
   change pre/post period and comparison technology, then reset.
2. Dataset & Classification: explain the proxy, original comparison, separate v2
   evaluation, confusion matrix, subgroups and calibration.
3. Predict a Question: submit the example, change the title/tags and resubmit;
   explain probability, threshold and SHAP without calling them causal effects.
4. Forecasts: show an observed backtest and uncertainty diagnostics.
5. Topics: change technology and topic; show matched examples and pending review.
6. Actions & Scenarios: change intervention success/cost, distinguish hypothetical
   benefit from observed ranking performance. State the tone and temporal limits.

Original presentations and reports have not been rewritten. Existing superseded
wording in historical deliverables must not be treated as the current target
definition; use this handoff and the updated app when preparing the later report.
The implementation assistance in this change was AI-generated and automatically
tested; the team must personally inspect and understand it before submission.
