# Using `src/evaluate.py` (notes for Member 4)

Every function takes `y_true` (0/1) and `y_score` (predicted probability that the question is **resolved**). Positive class = resolved. Pass `pos_label=0` to treat unresolved as positive.

```python
from src import evaluate as ev

# 1. Tune the threshold on VALIDATION only
t = ev.tune_threshold(y_val, p_val)

# 2. One metrics row per model (precision, recall, F1, PR-AUC, ROC-AUC, capture rate)
ev.metrics_table(y_val, p_val, threshold=t, name="logreg")

# 3. Compare several models in one table; a third tuple item sets a per-model threshold
ev.compare_models({
    "majority": (y_val, p_majority),
    "logreg":   (y_val, p_logreg, t_logreg),
})

# 4. Plots
ev.plot_confusion_matrix(y_val, p_val, threshold=t)
ev.plot_pr_curves({"logreg": (y_val, p_logreg)})
ev.plot_roc_curves({"logreg": (y_val, p_logreg)})

# 5. Business metric on its own
ev.capture_rate(y_val, p_val)   # share of unresolved questions in the lowest-scored 20%
```

Notes
- `sample_weight=` is optional. Use `sampling_weight` for periods before 2025; validation and test are fully collected, so use none there.
- Accuracy is intentionally not computed (see `docs/evaluation_plan.md`).
- The majority-class baseline is just a constant score, e.g. `np.full(len(y), y_train.mean())`.
- Tests: `python tests/test_evaluate.py`. Example outputs: `python -m src.evaluate` (writes to `reports/review1/evaluation_examples/`).
