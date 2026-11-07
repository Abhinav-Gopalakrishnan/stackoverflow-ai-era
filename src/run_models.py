"""Member 5 modelling run: baselines, Random Forest, XGBoost, evaluation, SHAP,
rolling-origin, secondary-target check and error analysis (M5-07 to M5-14).

Usage (needs data/processed/questions_clean_v1.parquet from Member 2):

    python -m src.run_models                       # default settings, writes reports/review1/m5/
    python -m src.run_models --full                # larger search (slower)
    python -m src.run_models --no-rolling          # everything except the slow rolling-origin step
    python -m src.run_models --rolling-only        # then add rolling-origin to that finished run
    python -m src.run_models --weekly path.csv     # weekly counts for lagged tag volume

The test period is evaluated exactly once: a lock file in the output folder stops a
second run from touching it (see ``evaluate.final_test_evaluation``). Delete the output
folder only if you really want to start over, and say so in the report.
"""

from __future__ import annotations

import argparse
import json
import tempfile
import time
from pathlib import Path

import numpy as np
import pandas as pd

from src import error_analysis as ea
from src import evaluate as ev
from src import interpret, leakage, models, rolling
from src.build_features import META, build_features
from src.timecv import GAP_DAYS

TARGET, TARGET2, WEIGHT = "target_resolved_7d", "target_answered_7d", "sampling_weight"
TRAIN_END, VAL_END = pd.Timestamp("2025-01-01", tz="UTC"), pd.Timestamp("2025-07-01", tz="UTC")
TEST_END = pd.Timestamp("2026-08-01", tz="UTC")
OUT_DIR = Path("reports/review1/m5")
SEED = 42
SHAP_ROWS = {"rf": 600, "xgb": 2000}   # deep forests are slow to explain


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def split_by_date(df):
    """Chronological split from docs/split_strategy.md: train 2019-2024, val 2025 H1, test Jul 2025 - Jul 2026."""
    t = df["created_at"]
    gap = pd.Timedelta(days=GAP_DAYS)
    return (df[t < TRAIN_END - gap].reset_index(drop=True),
            df[(t >= TRAIN_END) & (t < VAL_END - gap)].reset_index(drop=True),
            df[(t >= VAL_END) & (t < TEST_END)].reset_index(drop=True))


def _prep(df, text=True, svd_components=100, max_features=5000):
    numeric, binary, categorical = models.feature_lists(df)
    return models.build_preprocessor(numeric, binary, categorical,
                                     text=models.TEXT_COLUMN if text else None,
                                     svd_components=svd_components, max_features=max_features)


def _columns(df):
    numeric, binary, categorical = models.feature_lists(df)
    return numeric + binary + categorical + [models.TEXT_COLUMN]


def _strip(params):
    return {k.split("__", 1)[1]: (v.item() if hasattr(v, "item") else v) for k, v in params.items()}


def _save_fig(fig, path):
    import matplotlib.pyplot as plt

    fig.savefig(path, dpi=130, bbox_inches="tight")
    plt.close(fig)


def auto_hints(sheet, test):
    """Rule-based starting guess for ``likely_reason``; to be confirmed by reading each question."""
    t = test.set_index("question_id")
    hints = []
    for qid in sheet["question_id"]:
        r, h = t.loc[qid], []
        if r["title_length"] < 30:
            h.append("very short title")
        if r["n_code_blocks"] == 0 and not r["has_error_text"]:
            h.append("no code or error text")
        if r["body_length"] < 200:
            h.append("very short body")
        if r["new_account"] or r["missing_account_age"]:
            h.append("new or deleted asker account")
        rare = [c[4:] for c in t.columns if c in ("tag_openai-api", "tag_fastapi", "tag_docker")
                and r[c] == 1]
        if rare:
            h.append("low-volume tag: " + "/".join(rare))
        hints.append("; ".join(h))
    return hints


def _factory(feat, kind, params, svd_components, max_features):
    """``make_model(y)`` for rolling-origin and the secondary target: a fresh model, chosen settings."""
    def factory(y):
        return models.build_pipeline(kind, y, _prep(feat, True, svd_components, max_features), **params)
    return factory


def run_rolling(feat, kind, params, out, R, svd_components=100, max_features=5000,
                rolling_models=("2021 H2", "2025 H2")):
    """Rolling-origin evaluation (M5-12) with the chosen model's final settings; updates ``R``."""
    cols = _columns(feat)
    t0 = time.time()
    roll, fitted = rolling.rolling_origin(feat, _factory(feat, kind, params, svd_components, max_features),
                                          cols, TARGET, weight_col=WEIGHT, keep_models=True)
    roll_out = roll.drop(columns=["window_start"]).round(4)
    roll_out.to_csv(out / "rolling_origin.csv")
    _save_fig(rolling.plot_rolling(roll_out), out / "rolling_origin.png")
    R["rolling"] = {**rolling.summarise_rolling(roll_out), "table": roll_out.reset_index().to_dict("records")}
    r = R["rolling"]
    log(f"rolling-origin: {len(roll)} windows ({time.time() - t0:.0f}s); before/after Nov 2022: PR-AUC {r['pr_auc_pre']:.3f}/{r['pr_auc_post']:.3f}, "
        f"ROC-AUC {r['roc_auc_pre']:.3f}/{r['roc_auc_post']:.3f}, share resolved {r['positive_rate_pre']:.3f}/{r['positive_rate_post']:.3f}")
    if kind in ("rf", "xgb") and all(w in fitted for w in rolling_models):
        tables = {}
        for w in rolling_models:
            start = roll.loc[w, "window_start"]
            rows = feat[(feat["created_at"] >= start) & (feat["created_at"] < start + pd.DateOffset(months=6))]
            tables[w] = interpret.shap_frame(fitted[w], rows[cols], max_rows=SHAP_ROWS[kind], seed=SEED)[0]
        ranks = interpret.compare_top_features(tables, 5)
        ranks.to_csv(out / "shap_pre_post.csv")
        R["shap_pre_post"] = ranks.reset_index().astype(object).where(ranks.reset_index().notna(), None).to_dict("records")
    return R


def rolling_only(feat, out_dir=OUT_DIR):
    """Run only the rolling-origin step on a finished main run, using its saved settings.

    Reads ``results.json`` (chosen model and tuned parameters), so it needs no tuning and
    does not touch the test period.
    """
    out = Path(out_dir)
    R = json.loads((out / "results.json").read_text())
    kind = {"random forest": "rf", "xgboost": "xgb", "logistic regression": "logreg"}[R["chosen"]["model"]]
    params = R["tuning"].get(kind, {}).get("best_params", {})
    s = R["settings"]
    run_rolling(feat, kind, params, out, R, s["svd_components"], s["max_features"])
    (out / "results.json").write_text(json.dumps(R, indent=2, default=str))
    log(f"rolling results added to {out}/results.json")
    return R


def run_all(feat, out_dir=OUT_DIR, n_iter=8, n_splits=3, tune_rows=50000, svd_components=100,
            max_features=5000, do_rolling=True, rolling_models=("2021 H2", "2025 H2")):
    """Run every stage on a feature frame from ``build_features``; returns the results dict."""
    out = Path(out_dir)
    lock = out / ".test_evaluated"
    if lock.exists():
        raise RuntimeError(f"{lock} exists: the test period was already evaluated. "
                           "Use a new output folder only if starting over on purpose.")
    out.mkdir(parents=True, exist_ok=True)
    R = {"settings": dict(n_iter=n_iter, n_splits=n_splits, tune_rows=tune_rows,
                          svd_components=svd_components, max_features=max_features, seed=SEED),
         "dropped_no_history": feat.attrs.get("dropped_no_history", 0)}

    # ---- leakage guard on the model inputs
    cols = _columns(feat)
    log(f"XGBoost device: {models.xgb_device()} (set M5_DEVICE=cpu or cuda to force)")
    leakage.assert_no_leakage(cols)
    R["unexpected_columns"] = leakage.unexpected_columns([c for c in cols if c != models.TEXT_COLUMN])
    log(f"{len(cols)} model inputs, no forbidden columns; unexpected: {R['unexpected_columns']}")

    train, val, test = split_by_date(feat)
    split = pd.DataFrame({name: {"rows": len(d), TARGET + " share": round(d[TARGET].mean(), 3),
                                 TARGET2 + " share": round(d[TARGET2].mean(), 3)}
                          for name, d in (("train", train), ("validation", val), ("test", test))}).T
    split.to_csv(out / "split_report.csv")
    R["split"] = split.to_dict("index")
    assert not (set(train.question_id) & set(val.question_id)) and not (
        set(train.question_id) & set(test.question_id)) and not (
        set(val.question_id) & set(test.question_id)), "a question appears in two splits"
    log("split:\n" + split.to_string())

    X_tr, X_va, X_te = train[cols], val[cols], test[cols]
    y_tr, y_va, y_te = train[TARGET], val[TARGET], test[TARGET]
    w_tr = train[WEIGHT]
    cache = tempfile.mkdtemp(prefix="m5_cache_")

    # ---- baselines and the feature-gain experiment (M4-10 / M4-11 stand-ins)
    scores = {"majority class": models.majority_scores(y_tr, len(val))}
    lr_struct = models.fit_pipeline(models.build_pipeline("logreg", y_tr, _prep(train, text=False)),
                                    X_tr, y_tr, w_tr)
    lr_text = models.fit_pipeline(models.build_pipeline("logreg", y_tr, _prep(train, True, svd_components, max_features)),
                                  X_tr, y_tr, w_tr)
    p_struct, scores["logistic regression"] = (models.predict_score(lr_struct, X_va),
                                               models.predict_score(lr_text, X_va))
    gain = pd.concat([ev.metrics_table(y_va, p_struct, tune := ev.tune_threshold(y_va, p_struct),
                                       "structured only"),
                      ev.metrics_table(y_va, scores["logistic regression"],
                                       ev.tune_threshold(y_va, scores["logistic regression"]),
                                       "structured + title text")])
    gain.round(4).to_csv(out / "feature_gain.csv")
    log("feature gain (validation):\n" + gain[["f1", "pr_auc", "roc_auc"]].round(4).to_string())

    # coefficients of the text+structured logistic regression (M4-12 stand-in)
    names = lr_text[:-1].get_feature_names_out()
    coef = pd.Series(lr_text.steps[-1][1].coef_[0], index=names).sort_values()
    pd.concat([coef.head(15).rename("coefficient").to_frame().assign(direction="negative"),
               coef.tail(15)[::-1].rename("coefficient").to_frame().assign(direction="positive")]
              ).round(4).to_csv(out / "logreg_coefficients.csv")

    # ---- Random Forest and XGBoost: tuning on a date-ordered sample of the training period
    sub = train.sample(min(tune_rows, len(train)), random_state=SEED).sort_values("created_at")
    best = {}
    for kind, label in (("rf", "random forest"), ("xgb", "xgboost")):
        t0 = time.time()
        search = models.tune(kind, sub[cols], sub[TARGET], sub["created_at"], n_iter=n_iter,
                             n_splits=n_splits, sample_weight=sub[WEIGHT],
                             preprocessor=_prep(sub, True, svd_components, max_features),
                             random_state=SEED, memory=cache)
        best[kind] = _strip(search.best_params_)
        R.setdefault("tuning", {})[kind] = {"best_params": best[kind],
                                            "cv_pr_auc": round(float(search.best_score_), 4)}
        log(f"{label}: best CV PR-AUC {search.best_score_:.4f} with {best[kind]} ({time.time() - t0:.0f}s)")

    # Random Forest on the full training period with the tuned settings
    rf = models.fit_pipeline(models.build_pipeline("rf", y_tr, _prep(train, True, svd_components, max_features),
                                                   **best["rf"]), X_tr, y_tr, w_tr)
    # XGBoost: tuned learning rate and depth, number of trees by early stopping on validation
    xgb_params = {k: v for k, v in best["xgb"].items() if k != "n_estimators"}
    xgb, n_trees = models.fit_with_early_stopping(
        "xgb", X_tr, y_tr, X_va, y_va, _prep(train, True, svd_components, max_features), rounds=50,
        sample_weight=w_tr, n_estimators=2000, **xgb_params)
    best["xgb"]["n_estimators"] = n_trees
    R["tuning"]["xgb"]["trees_after_early_stopping"] = n_trees
    scores["random forest"], scores["xgboost"] = models.predict_score(rf, X_va), models.predict_score(xgb, X_va)

    # ---- validation comparison, best model, threshold
    thresholds = {name: ev.tune_threshold(y_va, s) for name, s in scores.items()}
    thresholds["majority class"] = 0.5
    comparison = ev.compare_models({n: (y_va, s, thresholds[n]) for n, s in scores.items()})
    comparison.round(4).to_csv(out / "model_comparison_val.csv")
    log("validation comparison:\n" + comparison[["precision", "recall", "f1", "pr_auc", "roc_auc",
                                               "capture_rate_20"]].round(4).to_string())
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    ev.plot_pr_curves({n: (y_va, s) for n, s in scores.items()}, ax=axes[0])
    ev.plot_roc_curves({n: (y_va, s) for n, s in scores.items()}, ax=axes[1])
    _save_fig(fig, out / "val_pr_roc.png")

    candidates = comparison.drop(index="majority class")
    chosen = candidates["pr_auc"].idxmax()
    threshold = thresholds[chosen]
    pipes = {"logistic regression": lr_text, "random forest": rf, "xgboost": xgb}
    chosen_pipe = pipes[chosen]
    kind = {"random forest": "rf", "xgboost": "xgb", "logistic regression": "logreg"}[chosen]
    R["chosen"] = {"model": chosen, "threshold": round(float(threshold), 4),
                   "validation_pr_auc": round(float(candidates.loc[chosen, "pr_auc"]), 4),
                   "reason": f"highest validation PR-AUC among the trained models ({', '.join(f'{n} {v:.3f}' for n, v in candidates['pr_auc'].items())}); threshold tuned for F1 on validation only"}
    R["validation"] = comparison.round(4).reset_index().to_dict("records")
    log(f"chosen: {chosen} (threshold {threshold:.3f})")

    # ---- final test evaluation: once
    p_te = models.predict_score(chosen_pipe, X_te)
    test_table = ev.final_test_evaluation(y_te, p_te, threshold, chosen, lock_path=str(lock))
    test_table.round(4).to_csv(out / "test_metrics.csv")
    R["test"] = test_table.round(4).reset_index().iloc[0].to_dict()
    R["test"]["n_unresolved"] = int((y_te == 0).sum())
    R["test"]["lift_20"] = round(float(test_table.iloc[0]["capture_rate_20"] / ev.FLAG_FRACTION), 3)
    fig, ax = plt.subplots(figsize=(4.2, 3.8))
    ev.plot_confusion_matrix(y_te, p_te, threshold, ax=ax, title=f"{chosen}: test period")
    _save_fig(fig, out / "test_confusion.png")
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    ev.plot_pr_curves({chosen: (y_te, p_te)}, ax=axes[0])
    ev.plot_roc_curves({chosen: (y_te, p_te)}, ax=axes[1])
    _save_fig(fig, out / "test_pr_roc.png")
    log("TEST (once):\n" + test_table.round(4).T.to_string())

    # ---- SHAP (tree models) on a sample of the test period
    if kind in ("rf", "xgb"):
        shap_df, feats = interpret.shap_frame(chosen_pipe, X_te, max_rows=SHAP_ROWS[kind], seed=SEED)
        top = interpret.top_features(shap_df, 10)
        top.rename("mean_abs_shap").round(5).to_csv(out / "shap_top.csv")
        R["shap_top"] = top.head(5).round(4).to_dict()
        _save_fig(interpret.plot_summary(shap_df, feats), out / "shap_summary.png")
        _save_fig(interpret.plot_dependence(shap_df, feats, list(top.index[:5])), out / "shap_dependence.png")
        # direction of each top feature (positive = pushes towards resolved)
        corr = {f: float(np.corrcoef(feats[f], shap_df[f])[0, 1]) for f in top.index[:5]}
        R["shap_direction"] = {f: ("higher value -> more likely resolved" if c > 0.1 else
                                   "higher value -> less likely resolved" if c < -0.1 else "mixed")
                               for f, c in corr.items()}
        log("top SHAP features: " + ", ".join(top.index[:5]))

    # ---- rolling-origin (needs a factory that builds a fresh model with the chosen settings)
    factory = _factory(feat, kind, best[kind], svd_components, max_features)

    if do_rolling:
        run_rolling(feat, kind, best[kind], out, R, svd_components, max_features, rolling_models)

    # ---- secondary target: same settings, retrained on target_answered_7d
    t2 = models.fit_pipeline(factory(train[TARGET2]), X_tr, train[TARGET2], w_tr)
    p2_va, p2_te = models.predict_score(t2, X_va), models.predict_score(t2, X_te)
    thr2 = ev.tune_threshold(val[TARGET2], p2_va)
    both = pd.concat([ev.metrics_table(y_te, p_te, threshold, "main: accepted within 7 days"),
                      ev.metrics_table(test[TARGET2], p2_te, thr2, "secondary: any answer within 7 days")])
    both.round(4).to_csv(out / "secondary_target.csv")
    R["secondary"] = both.round(4).reset_index().to_dict("records")
    if kind in ("rf", "xgb"):
        s2 = interpret.shap_frame(t2, X_te, max_rows=SHAP_ROWS[kind], seed=SEED)[0]
        interpret.compare_top_features({"accepted (main)": shap_df, "any answer (secondary)": s2}, 5).to_csv(
            out / "shap_secondary.csv")
        R["secondary_top"] = interpret.top_features(s2, 5).round(4).to_dict()
    log("secondary target (test):\n" + both[["precision", "recall", "f1", "pr_auc", "roc_auc"]].round(4).to_string())

    # ---- error analysis on the test period
    sheet = ea.sample_confident_errors(test, y_te, p_te, threshold)
    sheet.insert(len(sheet.columns) - 1, "auto_hint", auto_hints(sheet, test))
    sheet.to_csv(out / "error_annotation_sheet.csv", index=False)
    rates = []
    for column, bins in (("title_length", [0, 30, 60, 100, 1000]), ("body_length", [0, 200, 600, 1500, 10**6]),
                         ("n_code_blocks", [-1, 0, 2, 100]), ("tag_count", [0, 1, 2, 10]),
                         ("has_error_text", None), ("new_account", None)):
        t = ea.error_rate_by(test, y_te, p_te, threshold, column, bins).reset_index()
        t.columns = ["group", "n", "errors", "error_rate"]
        rates.append(t.assign(feature=column, group=t["group"].astype(str)))
    pd.concat(rates)[["feature", "group", "n", "errors", "error_rate"]].to_csv(out / "error_rates.csv", index=False)
    R["errors"] = {"overall_error_rate": round(float(((p_te >= threshold).astype(int) != y_te).mean()), 4),
                   "hint_counts": pd.Series("; ".join(sheet["auto_hint"]).split("; ")).replace("", np.nan)
                   .dropna().value_counts().head(6).to_dict()}

    (out / "results.json").write_text(json.dumps(R, indent=2, default=str))
    log(f"done: results in {out}/results.json")
    return R


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default="data/processed/questions_clean_v1.parquet")
    ap.add_argument("--weekly", default=None,
                    help="Member 1's complete weekly counts (lagged tag volume); default: "
                         "data/processed/weekly_counts.csv, else data/shared/weekly_counts.csv")
    ap.add_argument("--out", default=str(OUT_DIR))
    ap.add_argument("--full", action="store_true", help="larger search: 20 candidates, 5 folds, 100k rows")
    ap.add_argument("--no-rolling", action="store_true", help="skip the (slow) rolling-origin step")
    ap.add_argument("--rolling-only", action="store_true",
                    help="run only the rolling-origin step on a finished run (uses its results.json)")
    a = ap.parse_args()

    q = pd.read_parquet(a.data)
    log(f"loaded {len(q):,} rows from {a.data}")
    weekly_path = next((p for p in ([a.weekly] if a.weekly else
                                    ["data/processed/weekly_counts.csv", "data/shared/weekly_counts.csv"])
                        if Path(p).exists()), None)
    weekly = pd.read_csv(weekly_path) if weekly_path else None
    if weekly is None:
        log("WARNING: weekly_counts.csv not found - running WITHOUT lagged tag volume features")
    feat = build_features(q, weekly)
    log(f"features built: {len(feat):,} rows ({feat.attrs['dropped_no_history']} dropped: no weekly history yet)")
    if a.rolling_only:
        rolling_only(feat, a.out)
        return
    kw = dict(n_iter=20, n_splits=5, tune_rows=100000) if a.full else {}
    run_all(feat, a.out, do_rolling=not a.no_rolling, **kw)


if __name__ == "__main__":
    main()
