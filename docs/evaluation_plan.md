# Evaluation Plan (Review 1)

Owner: Member 5. Reviewer: Member 3. Rolling-origin design agreed jointly with Member 4 (see [M4-01], `docs/split_strategy.md`).

## 1. What is being predicted

| Target | Definition | Role |
|---|---|---|
| `target_resolved_7d` | Question has an accepted answer within 168 hours of posting | Main target |
| `target_answered_7d` | Question has any answer within 168 hours of posting | Secondary target (robustness check) |

The positive class for all headline metrics is **1 = resolved** (the target as defined). The model outputs a predicted probability of resolution, `p_resolved`.

## 2. Metrics

| Metric | Why it is reported |
|---|---|
| Precision | Of questions predicted resolved, how many truly were |
| Recall | Of questions that were resolved, how many the model found |
| F1 | Single number balancing precision and recall at the chosen threshold; used to tune the threshold |
| PR-AUC (average precision) | Threshold-free; the primary model-selection metric because it is sensitive to class imbalance |
| ROC-AUC | Threshold-free ranking quality; reported for comparison with other work |
| Confusion matrix | Shows the actual error counts (TP, FP, FN, TN) behind the other numbers |

**Accuracy is never used alone.** If one class dominates, a model that always predicts that class scores high accuracy while being useless. Accuracy may appear only next to the majority-class baseline and the metrics above.

Every model, including the majority-class baseline and Member 4's logistic regression, is scored with the same functions in `src/evaluate.py`, so results are directly comparable.

### Sampling weights

Before January 2025 the data is a weighted sample; from January 2025 it is complete (weight 1). The validation (Jan–Jun 2025) and test (Jul 2025–Jul 2026) periods are therefore fully collected and are scored **unweighted**. Rolling-origin test windows before 2025 are sampled, so their metrics are computed **with `sampling_weight`** so that weekday/weekend mix matches reality. Training may use the weights as well; this is decided and noted in the modelling notebook.

## 3. Business metric: capture rate

Scenario: a support-forum manager can give extra attention (route to an expert, prompt the asker to add code or error text) to only 20% of questions.

- Flag the 20% of questions with the **lowest** `p_resolved`.
- **Capture rate** = (unresolved questions among the flagged) / (all unresolved questions).
- **Lift** = capture rate / 0.20. Flagging 20% of questions at random gives a capture rate of about 0.20 (lift 1.0), so this is the baseline to beat.

The flagged set is defined by rank, not by the tuned threshold, so the metric does not depend on threshold choice. Ties are broken by row order (stable sort) so results are reproducible.

Limits to state with the number: acceptance within 7 days is only a proxy for "resolved" (it depends on the asker returning), and the recent period has less data than the sampled early years.

## 4. Data discipline

1. **Training:** January 2019 to December 2024. Hyperparameters are tuned with time-series cross-validation folds inside this period (never shuffled, never a random split).
2. **Validation:** January to June 2025. Used for model comparison, early stopping, and choosing the decision threshold.
3. **Test:** July 2025 to July 2026. **Used exactly once**, after the model, its hyperparameters and the threshold are frozen. No tuning of any kind happens after the test evaluation. If the test result is disappointing, it is reported as is.
4. **Threshold:** chosen on the validation period only, by maximising F1 for the positive class (`tune_threshold` in `src/evaluate.py`). The same frozen threshold is then applied to the test period.
5. Preprocessing (scaling, TF-IDF, SVD) is fitted on training data only, inside the pipeline.

## 5. Model comparison

One validation table with the same columns for each model:

1. Majority-class baseline
2. Logistic regression with class weights (Member 4)
3. Random Forest (Member 5)
4. XGBoost or LightGBM (Member 5)

The best model is chosen mainly on validation PR-AUC, with F1 at the tuned threshold as a tiebreaker. A one-paragraph written reason accompanies the choice. A model that does not beat logistic regression is reported honestly, not hidden.

## 6. Rolling-origin evaluation (pre- vs post-AI)

The single test period is entirely after November 2022, so it cannot show how performance changed across the break. The rolling-origin evaluation fixes this:

- For each half-year window from **2021 H1 to 2026 H1** (11 windows): train on **all data before the window starts**, test on **that half-year**.
- Same model settings for every window (the chosen model's final hyperparameters, no per-window tuning). Threshold-free metrics (PR-AUC, ROC-AUC) are the main comparison; F1 uses a threshold tuned on the last 6 months of the window's training data, never on the test half-year.
- Plot PR-AUC and F1 per half-year with a marker at 30 November 2022.
- Compare the top SHAP features of one pre-AI window (e.g. 2021 H2) and one post-AI window (e.g. 2025 H2).
- Wording: results are "associated with" or "consistent with" a change, never "caused by AI".

The pipeline must refit cleanly inside each window (Member 4's preprocessing pipeline, [M4-09]). Window boundaries are the same as in `docs/split_strategy.md`.

Note: the exact leakage guard for lagged tag volume applies in every window: only weeks before the question's posting week are used.

## 7. Secondary-target check

Retrain the chosen model on `target_answered_7d` and compare with the main target:

- the same metric table (validation and test),
- the top features (SHAP) for each target,
- written explanation of any difference in conclusions, for example changed acceptance habits (`accepted_given_answered` over time in Member 3's EDA).

## 8. Interpretation and error analysis

- **SHAP:** summary plot and dependence plots for the top 5 features, each explained in one plain sentence, compared with Member 4's logistic regression coefficients ([M5-11]).
- **Error analysis:** 30 confident wrong predictions, 15 false positives and 15 false negatives, sampled by the method in [M5-04].

## 9. Deliverables and where they live

| Output | Location |
|---|---|
| Metrics, plots, capture rate code | `src/evaluate.py` |
| Model comparison and tuning | `notebooks/05_models.ipynb` |
| Final test evaluation, rolling-origin, secondary-target check, SHAP, error analysis | `notebooks/06_evaluation.ipynb` |
| Business findings | `reports/review1/initial_findings.md` (with Member 3) |

## 10. Checklist before the review

- [ ] Accuracy never reported alone
- [ ] Threshold tuned on validation only
- [ ] Test set evaluated once, after all tuning
- [ ] Capture rate reported with its limits
- [ ] Rolling-origin results (2021 H1 to 2026 H1) with the November 2022 marker
- [ ] Secondary-target check included
- [ ] AI-related wording is "associated with" / "consistent with"
