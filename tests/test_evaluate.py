"""Toy-data tests for src/evaluate.py. Run: python tests/test_evaluate.py (or pytest)."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import evaluate as ev  # noqa: E402

# 10 hand-checked rows: 6 resolved (1), 4 unresolved (0).
Y = np.array([1, 1, 1, 1, 1, 1, 0, 0, 0, 0])
S = np.array([0.9, 0.8, 0.7, 0.6, 0.55, 0.3, 0.5, 0.4, 0.2, 0.1])


def test_metrics_at_threshold_half():
    # predicted resolved (score >= 0.5): rows 0-4 and row 6 -> TP=5, FP=1, FN=1, TN=3
    row = ev.metrics_table(Y, S, threshold=0.5).iloc[0]
    assert abs(row["precision"] - 5 / 6) < 1e-9
    assert abs(row["recall"] - 5 / 6) < 1e-9
    assert abs(row["f1"] - 5 / 6) < 1e-9
    assert row["n"] == 10 and abs(row["positive_rate"] - 0.6) < 1e-9
    assert "accuracy" not in row.index


def test_capture_rate():
    # flag ceil(0.2 * 10) = 2 lowest scores: 0.1 and 0.2, both unresolved.
    assert ev.capture_rate(Y, S) == 2 / 4
    # flag 5 lowest (0.1, 0.2, 0.3, 0.4, 0.5): unresolved among them = 4 of 4
    assert ev.capture_rate(Y, S, flag_fraction=0.5) == 1.0


def test_capture_rate_weighted():
    w = np.ones(10)
    w[9] = 3.0  # the lowest-scored (unresolved) row counts three times
    # unresolved weight total = 1+1+1+3 = 6; flagged (rows 8, 9) = 1 + 3 = 4
    assert abs(ev.capture_rate(Y, S, sample_weight=w) - 4 / 6) < 1e-9


def test_perfect_and_random_scores():
    perfect = ev.metrics_table(Y, Y.astype(float)).iloc[0]
    assert perfect["pr_auc"] == 1.0 and perfect["roc_auc"] == 1.0
    assert perfect["capture_rate_20"] == 0.5  # capped: only 2 of 4 unresolved fit in 20%
    rng = np.random.default_rng(0)
    y = rng.binomial(1, 0.5, 20000)
    rand = ev.metrics_table(y, rng.random(20000)).iloc[0]
    assert abs(rand["roc_auc"] - 0.5) < 0.02
    assert abs(rand["capture_rate_20"] - 0.2) < 0.02  # random flagging ~ flag fraction


def test_majority_baseline_has_no_skill():
    row = ev.metrics_table(Y, np.full(10, 0.6), threshold=0.5).iloc[0]
    assert row["recall"] == 1.0 and abs(row["precision"] - 0.6) < 1e-9
    assert abs(row["roc_auc"] - 0.5) < 1e-9


def test_tune_threshold_beats_default():
    t = ev.tune_threshold(Y, S)
    f_tuned = ev.metrics_table(Y, S, threshold=t).iloc[0]["f1"]
    f_half = ev.metrics_table(Y, S, threshold=0.5).iloc[0]["f1"]
    assert f_tuned >= f_half
    # best F1 on this toy data is at threshold 0.55: TP=5, FP=0, FN=1 -> 10/11
    assert abs(t - 0.55) < 1e-9 and abs(f_tuned - 10 / 11) < 1e-9


def test_pos_label_zero_mirrors_capture_view():
    row = ev.metrics_table(Y, S, threshold=0.45, pos_label=0).iloc[0]
    # predicted unresolved: score < 0.45 -> rows 5, 7, 8, 9: TP=3, FP=1, FN=1
    assert abs(row["precision"] - 3 / 4) < 1e-9
    assert abs(row["recall"] - 3 / 4) < 1e-9


def test_compare_models_and_plots():
    import matplotlib

    matplotlib.use("Agg")
    results = {"a": (Y, S), "b": (Y, np.full(10, 0.6), 0.5)}
    table = ev.compare_models(results)
    assert list(table.index) == ["a", "b"]
    ev.plot_confusion_matrix(Y, S)
    ev.plot_pr_curves(results)
    ev.plot_roc_curves(results)


def test_bad_inputs_raise():
    for bad in (lambda: ev.metrics_table([0, 2], [0.1, 0.2]),
                lambda: ev.metrics_table([0, 1], [0.1]),
                lambda: ev.metrics_table([0, 1], [0.1, np.nan])):
        try:
            bad()
        except ValueError:
            continue
        raise AssertionError("expected ValueError")


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print("ok", t.__name__)
    print(f"{len(tests)} tests passed")
