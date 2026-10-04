"""Rolling-origin evaluation (M5-12, docs/evaluation_plan.md section 6).

For each half-year window: train on all data before the window (minus a gap),
test on the window. The decision threshold is tuned on the last
``threshold_months`` of that training data, never on the test window: the model
is fitted on the earlier part, the threshold is tuned on the later part, then
the model is refitted on all training data and scored on the window.
"""

from __future__ import annotations

import pandas as pd

from src import evaluate as ev
from src.models import fit_pipeline, predict_score
from src.timecv import GAP_DAYS, half_year_windows

MIN_TRAIN_ROWS = 200


def _threshold_from_inner(make_model, features, target, train, date_col, weight_col,
                          cut, gap):
    """Tune the threshold on the last months of training; 0.5 if there is too little data."""
    inner_fit = train[train[date_col] < cut - gap]
    inner_val = train[train[date_col] >= cut]
    if (len(inner_fit) < MIN_TRAIN_ROWS or inner_val[target].nunique() < 2
            or inner_fit[target].nunique() < 2):
        return 0.5
    model = fit_pipeline(make_model(inner_fit[target]), inner_fit[features], inner_fit[target],
                         None if weight_col is None else inner_fit[weight_col])
    weights = None if weight_col is None else inner_val[weight_col]
    return ev.tune_threshold(inner_val[target], predict_score(model, inner_val[features]),
                             sample_weight=weights)


def rolling_origin(df, make_model, features, target="target_resolved_7d", date_col="created_at",
                   weight_col=None, windows=None, gap_days=GAP_DAYS, threshold_months=6,
                   keep_models=False):
    """Metrics per half-year window.

    ``make_model(y_train)`` returns a fresh unfitted pipeline (use the chosen
    model's final hyperparameters; no per-window tuning). With ``weight_col``
    (``sampling_weight``) the sampled pre-2025 windows are weighted correctly.
    Returns a DataFrame indexed by window; with ``keep_models=True`` also a
    dict of fitted pipelines, for comparing SHAP features between windows.
    """
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col], utc=True)
    gap = pd.Timedelta(days=gap_days)
    rows, models = [], {}
    for label, start, end in windows or half_year_windows():
        train = df[df[date_col] < start - gap]
        test = df[(df[date_col] >= start) & (df[date_col] < end)]
        if len(train) < MIN_TRAIN_ROWS or test[target].nunique() < 2 or train[target].nunique() < 2:
            continue
        cut = start - gap - pd.DateOffset(months=threshold_months)
        threshold = _threshold_from_inner(make_model, features, target, train, date_col,
                                          weight_col, cut, gap)
        model = fit_pipeline(make_model(train[target]), train[features], train[target],
                             None if weight_col is None else train[weight_col])
        weights = None if weight_col is None else test[weight_col]
        row = ev.metrics_table(test[target], predict_score(model, test[features]), threshold,
                               name=label, sample_weight=weights).iloc[0].to_dict()
        row.update(window=label, window_start=start, n_train=len(train))
        rows.append(row)
        models[label] = model
    result = pd.DataFrame(rows).set_index("window")
    return (result, models) if keep_models else result


def window_start(label):
    """Start date of a window label such as ``"2022 H2"``."""
    year, half = label.split()
    return pd.Timestamp(int(year), 1 if half == "H1" else 7, 1, tz="UTC")


def summarise_rolling(table, marker="2022-11-30"):
    """Before/after comparison of a rolling-origin table (index = window label).

    PR-AUC depends on how common the positive class is, so it is reported next to the share
    resolved (``positive_rate``) and ROC-AUC, which does not. ``pr_auc_lift`` = PR-AUC minus
    the share resolved: how far the model is above a no-skill ranking in that window.
    """
    t = table.copy()
    t["pr_auc_lift"] = t["pr_auc"] - t["positive_rate"]
    after = pd.Series([window_start(w) >= pd.Timestamp(marker, tz="UTC") for w in t.index], index=t.index)
    out = {"windows": len(t)}
    for column in ("pr_auc", "roc_auc", "f1", "positive_rate", "pr_auc_lift"):
        out[f"{column}_pre"] = round(float(t.loc[~after, column].mean()), 4)
        out[f"{column}_post"] = round(float(t.loc[after, column].mean()), 4)
    # names used by the slides and findings before this summary existed
    out["mean_pr_auc_pre_nov2022"], out["mean_pr_auc_post_nov2022"] = out["pr_auc_pre"], out["pr_auc_post"]
    return out


def plot_rolling(result, marker="2022-11-30"):
    """Two panels with the November 2022 marker: PR-AUC, F1 and share resolved; ROC-AUC and PR-AUC lift."""
    import matplotlib.pyplot as plt

    fig, (left, right) = plt.subplots(1, 2, figsize=(12, 4.2))
    labels = list(result.index)
    x = range(len(labels))
    left.plot(x, result["pr_auc"], marker="o", label="PR-AUC")
    left.plot(x, result["f1"], marker="s", label="F1")
    left.plot(x, result["positive_rate"], marker="^", linestyle=":", color="grey", label="share resolved (base rate)")
    right.plot(x, result["roc_auc"], marker="o", color="tab:green", label="ROC-AUC")
    right.plot(x, result["pr_auc"] - result["positive_rate"], marker="s", color="tab:purple",
               label="PR-AUC minus base rate")
    after = [i for i, w in enumerate(labels) if window_start(w) >= pd.Timestamp(marker, tz="UTC")]
    for ax, title in ((left, "Scores by half-year (test window)"), (right, "Ranking quality by half-year")):
        if after:
            ax.axvline(after[0] - 0.5, color="red", linestyle="--", label="30 Nov 2022")
        ax.set_xticks(list(x), labels, rotation=45)
        ax.set_xlabel("Test half-year")
        ax.set_ylabel("Score")
        ax.set_title(title)
        ax.legend(fontsize=8)
    fig.tight_layout()
    return fig
