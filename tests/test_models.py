"""Tests for src/timecv.py, models.py, rolling.py, interpret.py. Run: python tests/test_models.py"""

import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import evaluate as ev  # noqa: E402
from src import interpret, models, rolling, timecv  # noqa: E402

DF = models.make_synthetic_data(3000)
FEATURES, TARGET = models.FEATURES, "target_resolved_7d"


def test_time_series_folds_by_date_with_gap():
    d = DF["created_at"]
    folds = timecv.time_series_folds(d, n_splits=5, gap_days=7)
    assert len(folds) == 5
    prev_end = None
    for train, test in folds:
        assert len(set(train) & set(test)) == 0
        assert d.iloc[train].max() < d.iloc[test].min() - pd.Timedelta(days=7)
        assert prev_end is None or d.iloc[test].min() >= prev_end  # test chunks move forward
        prev_end = d.iloc[test].min()


def test_half_year_windows():
    w = timecv.half_year_windows()
    assert len(w) == 11 and w[0][0] == "2021 H1" and w[-1][0] == "2026 H1"
    assert w[0][1] == pd.Timestamp("2021-01-01", tz="UTC") and w[1][1] == pd.Timestamp("2021-07-01", tz="UTC")


def test_pipelines_fit_and_score():
    train, val = DF[DF["created_at"] < "2025-01-01"], DF[DF["created_at"] >= "2025-01-01"]
    assert models.scale_pos_weight([1, 1, 1, 0]) == 1 / 3
    for kind in models.KINDS:
        pipe = models.build_pipeline(kind, train[TARGET], n_estimators=40)
        models.fit_pipeline(pipe, train[FEATURES], train[TARGET], train["sampling_weight"])
        p = models.predict_score(pipe, val[FEATURES])
        assert p.shape == (len(val),) and ((p >= 0) & (p <= 1)).all()
        assert ev.metrics_table(val[TARGET], p).iloc[0]["roc_auc"] > 0.55  # learns the signal
    base = models.majority_scores(train[TARGET], len(val))
    assert abs(ev.metrics_table(val[TARGET], base).iloc[0]["roc_auc"] - 0.5) < 1e-9


def test_tune_uses_time_series_folds():
    train = DF[DF["created_at"] < "2025-01-01"]
    for kind in ("rf", "xgb"):
        search = models.tune(kind, train[FEATURES], train[TARGET], train["created_at"],
                             n_iter=2, n_splits=3, sample_weight=train["sampling_weight"])
        assert set(search.best_params_) == set(models.SEARCH_SPACES[kind])
        assert 0 < search.best_score_ <= 1


def test_early_stopping_stops_before_max_trees():
    train, val = DF[DF["created_at"] < "2025-01-01"], DF[DF["created_at"] >= "2025-01-01"]
    for kind in ("xgb", "lgbm"):
        pipe, best = models.fit_with_early_stopping(kind, train[FEATURES], train[TARGET],
                                                    val[FEATURES], val[TARGET], rounds=10,
                                                    n_estimators=500)
        assert 1 <= best < 500
        assert models.predict_score(pipe, val[FEATURES]).shape == (len(val),)


def test_rolling_origin_windows_and_no_future_in_training():
    make = lambda y: models.build_pipeline("rf", y, n_estimators=30)  # noqa: E731
    result, fitted = rolling.rolling_origin(DF, make, FEATURES, weight_col="sampling_weight",
                                            keep_models=True)
    assert 8 <= len(result) <= 11 and result.index[0] == "2021 H1"
    assert (result["n_train"].diff().dropna() > 0).all()  # more history each window
    assert result["pr_auc"].between(0, 1).all() and set(fitted) == set(result.index)
    rolling.plot_rolling(result)


def test_summarise_rolling_reports_base_rate():
    import matplotlib

    matplotlib.use("Agg")
    table = pd.DataFrame({"pr_auc": [0.6, 0.6, 0.5, 0.5], "roc_auc": [0.65] * 4, "f1": [0.6, 0.6, 0.5, 0.5],
                          "positive_rate": [0.45, 0.45, 0.35, 0.35]}, index=["2022 H1", "2022 H2", "2023 H1", "2023 H2"])
    out = rolling.summarise_rolling(table)
    assert out["pr_auc_pre"] == 0.6 and out["pr_auc_post"] == 0.5 and out["positive_rate_post"] == 0.35
    assert abs(out["pr_auc_lift_pre"] - 0.15) < 1e-9 and abs(out["pr_auc_lift_post"] - 0.15) < 1e-9  # same skill
    assert out["roc_auc_pre"] == out["roc_auc_post"] == 0.65
    rolling.plot_rolling(table)


def test_shap_top_features():
    import matplotlib

    matplotlib.use("Agg")
    train = DF[DF["created_at"] < "2025-01-01"]
    pipe = models.fit_pipeline(models.build_pipeline("rf", train[TARGET], n_estimators=30),
                               train[FEATURES], train[TARGET])
    shap_df, feats = interpret.shap_frame(pipe, train[FEATURES], max_rows=300)
    top = interpret.top_features(shap_df, 5)
    assert len(top) == 5 and top.is_monotonic_decreasing
    assert {"has_error_text", "code_ratio", "new_account"} & set(top.index)  # the true drivers
    ranks = interpret.compare_top_features({"a": shap_df, "b": shap_df}, 5)
    assert (ranks["a"].dropna() == ranks["b"].dropna()).all()
    with tempfile.TemporaryDirectory() as tmp:
        interpret.plot_summary(shap_df, feats, f"{tmp}/s.png")
        interpret.plot_dependence(shap_df, feats, list(top.index[:2]), f"{tmp}/d.png")
        assert Path(f"{tmp}/s.png").exists() and Path(f"{tmp}/d.png").exists()


def test_final_test_evaluation_runs_once():
    y, s = np.array([0, 1, 1, 0, 1]), np.array([0.2, 0.9, 0.6, 0.4, 0.7])
    with tempfile.TemporaryDirectory() as tmp:
        lock = f"{tmp}/.test_evaluated"
        table = ev.final_test_evaluation(y, s, 0.5, lock_path=lock)
        assert table.iloc[0]["recall"] == 1.0
        try:
            ev.final_test_evaluation(y, s, 0.5, lock_path=lock)
        except RuntimeError:
            return
        raise AssertionError("second test evaluation should be refused")


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print("ok", t.__name__)
    print(f"{len(tests)} tests passed")
