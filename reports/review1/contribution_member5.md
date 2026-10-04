# Review 1 Contribution Summary: Member 5 (Adhikkesh, <register number>)

Role: advanced models, evaluation and business findings

Rubric components owned: model development (shared with Member 4, 2 of 4 marks) and model evaluation and interpretation (3 marks)

## Tasks completed
| Issue | Title | Evidence link | Reviewed by |
| --- | --- | --- | --- |
| #11 | [M5-00] Rubric and project plan reading | issue comment | Member 3 |
| #12 | [M5-01] Evaluation plan | `docs/evaluation_plan.md` | Member 3 |
| #14 | [M5-03] Evaluation module | `src/evaluate.py`, `tests/test_evaluate.py`, `docs/evaluate_usage.md` | Member 3 |
| #13 | [M5-02] Modelling skeleton | `src/models.py`, `src/timecv.py`, `tests/test_models.py` | Member 3 |
| #66 | [M5-05] Feature spec and leakage review | `docs/leakage_review.md`, `src/leakage.py` | Member 3 |
| # | [M5-04] Error analysis design | `docs/error_analysis_design.md`, `src/error_analysis.py` | Member 3 |
| # | [M5-07], [M5-08] Random Forest and gradient boosting | `notebooks/05_models.ipynb`, `src/run_models.py` | Member 3 |
| # | [M5-09], [M5-10] Model comparison, threshold, final test evaluation | `reports/review1/m5/model_comparison_val.csv`, `test_metrics.csv` | Member 3 |
| # | [M5-11] SHAP interpretation | `reports/review1/m5/shap_summary.png`, `src/interpret.py` | Member 3 |
| # | [M5-12] Rolling-origin evaluation | `reports/review1/m5/rolling_origin.csv`, `src/rolling.py` | Member 3 |
| # | [M5-13] Secondary target check | `reports/review1/m5/secondary_target.csv` | Member 3 |
| # | [M5-14] Error analysis | `reports/review1/m5/error_annotation_sheet.csv` | Member 3 |
| # | [M5-15] Initial business findings (with Member 3) | `reports/review1/m5_findings.md` | Member 3 |
| # | [M5-16] Model and evaluation sections for the main notebook | `notebooks/05_models.ipynb`, `notebooks/06_evaluation.ipynb` | Member 1 |
| # | [M5-17] Models, evaluation and findings slides | `reports/review1/m5_slides.pptx` | Member 3 |

(Fill the `#` issue numbers and replace file paths with PR links before submitting.)

## Key results
- XGBoost chosen on validation PR-AUC (0.482; logistic regression 0.471, Random Forest 0.473). Test, evaluated once: PR-AUC 0.431 against 0.297 for no skill, ROC-AUC 0.655, capture rate 24.1% (1.21x random).
- Rolling-origin (11 half-year windows): ranking quality stable across November 2022 (ROC-AUC 0.64 before, 0.65 after); PR-AUC fell with the share resolved (42% to 33%).
- Error analysis of 30 confident errors: false positives are mostly answered-but-not-accepted questions, false negatives mostly brand-new accounts that returned quickly.

## Key outputs
- `docs/evaluation_plan.md`: metrics, capture-rate business metric, validation/test rules, rolling-origin design.
- `src/evaluate.py`: metrics table, threshold tuning, confusion matrix, PR/ROC curves, capture rate, single-use test evaluation.
- `src/models.py`, `src/rolling.py`, `src/interpret.py`, `src/error_analysis.py`, `src/leakage.py`: modelling, rolling-origin, SHAP, error analysis and leakage checks, all with tests.
- `src/run_models.py`: one command that runs baselines, tuning, comparison, the single test evaluation, SHAP, rolling-origin, the secondary-target check and error analysis.
- `reports/review1/m5/`: all tables and figures (including `error_analysis_summary.md`); `reports/review1/m5_slides.pptx`; `reports/review1/m5_findings.md`.
- Training was run on Google Colab (T4 GPU for XGBoost) with `notebooks/colab_run_models.ipynb`.

## Decisions I made and why
- Positive class is "resolved within 7 days": it matches the target definition.
- Model chosen on validation PR-AUC: threshold-free and sensitive to class balance.
- Threshold tuned on validation only and the test period evaluated once: no tuning after seeing test results; the code enforces it with a lock file.
- `sampling_weight` used as a sample weight, never as a feature: it is a proxy for the time period.
- 7-day gap between training and test in every fold and rolling window: a label is only known 7 days after posting.
- Title TF-IDF and SVD fitted inside the pipeline: guarantees training-only fitting in every fold and window.

## Reviews I gave
- Member 4's feature specification and split strategy (leakage review in `docs/leakage_review.md`).

## Problems faced and how I solved them
- Member 1's weekly counts are anchored on 2019-01-01 (a Tuesday), not on Mondays: the lagged-volume code and its independent checker use the table's own 7-day weeks.
- XGBoost with all CPU threads was about 50 times slower on this data size than with 4: thread count is capped.
- The cleaned dataset is too large for Git and lives on the team drive: the run script reads it from `data/processed/` and rebuilds everything from it.
- Reading the rolling-origin PR-AUC: it fell after November 2022 only because the share of resolved questions fell; I added the base rate and ROC-AUC to the analysis so the comparison is fair.
- Member 4's baseline had no PR-AUC or class weights and 64% accuracy against 66% for always predicting unresolved; I scored it with the shared evaluation functions and showed it in the comparison table.

## What I can explain in the viva
- Why PR-AUC, how the threshold was tuned without the test set, and what the capture rate means.
- How rolling-origin evaluation gives pre- and post-November-2022 results.
- How leakage is prevented (forbidden fields, title text fitted on training data only, lagged volume from past weeks only).
- How SHAP shows which features drive predictions and how it compares with the logistic regression coefficients.
- (Other area) Member 2's targets and label-maturity rule, and Member 4's chronological split.
