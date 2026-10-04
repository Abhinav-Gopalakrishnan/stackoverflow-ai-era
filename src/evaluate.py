"""Evaluation tools for the Review 1 models (see docs/evaluation_plan.md).

All functions take the true labels ``y_true`` (0/1) and the predicted
probability of the positive class ``y_score``. By default the positive class is
1 = resolved (``target_resolved_7d``). Pass ``pos_label=0`` to evaluate with
"unresolved" as the positive class instead.

``sample_weight`` is optional. Use ``sampling_weight`` for the sampled period
(before 2025); validation and test periods are fully collected and need none.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)

FLAG_FRACTION = 0.20


def _prepare(y_true, y_score, sample_weight=None, pos_label=1):
    """Validate inputs and return arrays where 1 always means the positive class."""
    y_true = np.asarray(y_true)
    y_score = np.asarray(y_score, dtype=float)
    if y_true.shape != y_score.shape or y_true.ndim != 1:
        raise ValueError("y_true and y_score must be 1-D arrays of the same length")
    if not set(np.unique(y_true)) <= {0, 1}:
        raise ValueError("y_true must contain only 0 and 1")
    if pos_label not in (0, 1):
        raise ValueError("pos_label must be 0 or 1")
    if np.isnan(y_score).any():
        raise ValueError("y_score contains NaN")
    weight = None if sample_weight is None else np.asarray(sample_weight, dtype=float)
    if weight is not None and weight.shape != y_true.shape:
        raise ValueError("sample_weight must have the same length as y_true")
    if pos_label == 0:
        y_true, y_score = 1 - y_true, 1 - y_score
    return y_true.astype(int), y_score, weight


def capture_rate(y_true, y_score, flag_fraction=FLAG_FRACTION, sample_weight=None):
    """Share of unresolved questions captured by flagging the lowest-scored ones.

    Flags the ``flag_fraction`` of questions with the lowest predicted
    resolution probability (by rank; ties broken by row order) and returns
    ``(unresolved among flagged) / (all unresolved)``. ``y_score`` is always the
    probability of resolution (y_true == 1). Random flagging gives about
    ``flag_fraction``, so lift = capture / flag_fraction.
    """
    y_true, y_score, weight = _prepare(y_true, y_score, sample_weight)
    if not 0 < flag_fraction < 1:
        raise ValueError("flag_fraction must be between 0 and 1")
    weight = np.ones(len(y_true)) if weight is None else weight

    unresolved = (y_true == 0) * weight
    if unresolved.sum() == 0:
        return float("nan")

    order = np.argsort(y_score, kind="stable")
    n_flag = int(np.ceil(flag_fraction * len(y_true)))
    return float(unresolved[order[:n_flag]].sum() / unresolved.sum())


def tune_threshold(y_true, y_score, sample_weight=None, pos_label=1):
    """Threshold that maximises F1. Call on the validation period only."""
    y_true, y_score, weight = _prepare(y_true, y_score, sample_weight, pos_label)
    precision, recall, thresholds = precision_recall_curve(
        y_true, y_score, sample_weight=weight
    )
    # precision/recall have one more entry than thresholds; drop the last one.
    denom = precision[:-1] + recall[:-1]
    f1 = np.divide(2 * precision[:-1] * recall[:-1], denom,
                   out=np.zeros_like(denom), where=denom > 0)
    best = int(np.argmax(f1))
    # thresholds were computed on the flipped score when pos_label == 0
    return float(thresholds[best] if pos_label == 1 else 1 - thresholds[best])


def metrics_table(y_true, y_score, threshold=0.5, name="model",
                  sample_weight=None, pos_label=1):
    """One-row DataFrame: precision, recall, F1, PR-AUC, ROC-AUC, capture rate.

    Accuracy is deliberately not included (see docs/evaluation_plan.md).
    ``threshold`` applies to ``y_score`` as passed in (probability of
    resolution), whatever ``pos_label`` is.
    """
    y_pos, s_pos, weight = _prepare(y_true, y_score, sample_weight, pos_label)
    t = threshold if pos_label == 1 else 1 - threshold
    y_pred = (s_pos >= t).astype(int) if pos_label == 1 else (s_pos > t).astype(int)

    both_classes = len(np.unique(y_pos)) == 2
    row = {
        "model": name,
        "n": len(y_pos),
        "positive_rate": float(np.average(y_pos, weights=weight)),
        "threshold": threshold,
        "precision": precision_score(y_pos, y_pred, sample_weight=weight, zero_division=0),
        "recall": recall_score(y_pos, y_pred, sample_weight=weight, zero_division=0),
        "f1": f1_score(y_pos, y_pred, sample_weight=weight, zero_division=0),
        "pr_auc": average_precision_score(y_pos, s_pos, sample_weight=weight)
        if both_classes else float("nan"),
        "roc_auc": roc_auc_score(y_pos, s_pos, sample_weight=weight)
        if both_classes else float("nan"),
        "capture_rate_20": capture_rate(y_true, y_score, sample_weight=sample_weight),
    }
    return pd.DataFrame([row]).set_index("model")


TEST_LOCK = "reports/review1/.test_evaluated"


def final_test_evaluation(y_true, y_score, threshold, name="final model", lock_path=TEST_LOCK,
                          sample_weight=None):
    """The single evaluation on the test period (M5-10).

    Writes a lock file the first time it runs and refuses to run again, so the
    test period cannot be used for tuning by accident. The threshold must come
    from the validation period.
    """
    from datetime import datetime, timezone
    from pathlib import Path

    lock = Path(lock_path)
    if lock.exists():
        raise RuntimeError(f"test period already evaluated ({lock.read_text().splitlines()[0]}); "
                           "no tuning is allowed after the final test evaluation")
    table = metrics_table(y_true, y_score, threshold, name, sample_weight)
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_text(f"{datetime.now(timezone.utc).isoformat()}\n{name} threshold={threshold}\n")
    return table


def compare_models(results, threshold=0.5, sample_weight=None, pos_label=1):
    """Stack metric rows for several models.

    ``results`` maps model name -> (y_true, y_score), or -> (y_true, y_score,
    threshold) to give a model its own tuned threshold.
    """
    rows = []
    for name, values in results.items():
        y_true, y_score, *rest = values
        rows.append(metrics_table(y_true, y_score, rest[0] if rest else threshold,
                                  name, sample_weight, pos_label))
    return pd.concat(rows)


def plot_confusion_matrix(y_true, y_score, threshold=0.5, ax=None, normalize=False,
                          title=None, sample_weight=None, pos_label=1):
    """Heat-mapped confusion matrix with the count (or share) in each cell."""
    import matplotlib.pyplot as plt

    y_pos, s_pos, weight = _prepare(y_true, y_score, sample_weight, pos_label)
    t = threshold if pos_label == 1 else 1 - threshold
    y_pred = (s_pos >= t).astype(int) if pos_label == 1 else (s_pos > t).astype(int)
    cm = confusion_matrix(y_pos, y_pred, labels=[0, 1], sample_weight=weight,
                          normalize="true" if normalize else None)

    ax = ax or plt.subplots(figsize=(4, 3.5))[1]
    ax.imshow(cm, cmap="Blues")
    names = ("unresolved", "resolved") if pos_label == 1 else ("resolved", "unresolved")
    ax.set_xticks([0, 1], [f"predicted {n}" for n in names])
    ax.set_yticks([0, 1], [f"actual {n}" for n in names])
    for i in range(2):
        for j in range(2):
            text = f"{cm[i, j]:.2f}" if normalize else f"{cm[i, j]:,.0f}"
            ax.text(j, i, text, ha="center", va="center",
                    color="white" if cm[i, j] > cm.max() / 2 else "black")
    ax.set_title(title or f"Confusion matrix (threshold {threshold:.2f})")
    return ax


def plot_pr_curves(results, ax=None, sample_weight=None, pos_label=1):
    """Precision-recall curves; ``results`` maps name -> (y_true, y_score)."""
    import matplotlib.pyplot as plt

    ax = ax or plt.subplots(figsize=(5, 4))[1]
    for name, (y_true, y_score, *_) in results.items():
        y_pos, s_pos, weight = _prepare(y_true, y_score, sample_weight, pos_label)
        precision, recall, _ = precision_recall_curve(y_pos, s_pos, sample_weight=weight)
        ap = average_precision_score(y_pos, s_pos, sample_weight=weight)
        ax.plot(recall, precision, label=f"{name} (PR-AUC {ap:.3f})")
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.set_title("Precision-recall curve")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.02)
    ax.legend(loc="best")
    return ax


def plot_roc_curves(results, ax=None, sample_weight=None, pos_label=1):
    """ROC curves; ``results`` maps name -> (y_true, y_score)."""
    import matplotlib.pyplot as plt

    ax = ax or plt.subplots(figsize=(5, 4))[1]
    for name, (y_true, y_score, *_) in results.items():
        y_pos, s_pos, weight = _prepare(y_true, y_score, sample_weight, pos_label)
        fpr, tpr, _ = roc_curve(y_pos, s_pos, sample_weight=weight)
        auc = roc_auc_score(y_pos, s_pos, sample_weight=weight)
        ax.plot(fpr, tpr, label=f"{name} (ROC-AUC {auc:.3f})")
    ax.plot([0, 1], [0, 1], "k--", linewidth=0.8, label="chance")
    ax.set_xlabel("False positive rate")
    ax.set_ylabel("True positive rate")
    ax.set_title("ROC curve")
    ax.legend(loc="best")
    return ax


def _demo(out_dir="reports/review1/evaluation_examples"):
    """Write example outputs from synthetic data (used as PR evidence)."""
    from pathlib import Path

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rng = np.random.default_rng(42)
    n = 5000
    y = rng.binomial(1, 0.6, n)
    good = np.clip(0.35 * y + rng.normal(0.35, 0.2, n), 0, 1)
    weak = np.clip(0.10 * y + rng.normal(0.45, 0.2, n), 0, 1)
    majority = np.full(n, y.mean())
    results = {"majority": (y, majority), "weak model": (y, weak), "good model": (y, good)}

    threshold = tune_threshold(y, good)
    table = compare_models(results)
    table.loc["good model"] = metrics_table(y, good, threshold, "good model").iloc[0]

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    table.round(4).to_csv(out / "metrics_table.csv")
    fig, ax = plt.subplots(figsize=(4, 3.5))
    plot_confusion_matrix(y, good, threshold, ax=ax)
    fig.tight_layout()
    fig.savefig(out / "confusion_matrix.png", dpi=120)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    plot_pr_curves(results, ax=axes[0])
    plot_roc_curves(results, ax=axes[1])
    fig.tight_layout()
    fig.savefig(out / "pr_roc_curves.png", dpi=120)
    print(table.round(3).to_string())
    print(f"tuned threshold: {threshold:.3f}; outputs in {out}")


if __name__ == "__main__":
    _demo()
