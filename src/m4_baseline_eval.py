"""Member 4's logistic-regression baseline (M4-07), scored with the shared evaluation functions.

Reproduces ``src/baseline.py`` (same features, plain logistic regression) from Member 4's saved
``features_train/val.parquet`` and evaluates it on validation with ``src/evaluate.py`` so it can sit
in the same comparison table as the other models. Also reports the majority-class baseline's
accuracy, to show why accuracy alone is misleading.

    python -m src.m4_baseline_eval          # writes reports/review1/m5/m4_baseline_val.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from src import evaluate as ev

TARGETS = ["target_resolved_7d", "target_answered_7d"]


def run(train_path="data/processed/features_train.parquet", val_path="data/processed/features_val.parquet",
        out="reports/review1/m5/m4_baseline_val.csv"):
    train, val = pd.read_parquet(train_path), pd.read_parquet(val_path)
    drop = TARGETS + ["question_word_none"]
    X_tr, X_va = train.drop(columns=drop, errors="ignore"), val.drop(columns=drop, errors="ignore")
    y_tr, y_va = train["target_resolved_7d"], val["target_resolved_7d"]
    p = LogisticRegression(max_iter=1000, random_state=42).fit(X_tr, y_tr).predict_proba(X_va)[:, 1]

    name = "logistic regression (Member 4 features)"
    rows = pd.concat([ev.metrics_table(y_va, p, 0.5, name + ", threshold 0.5"),
                      ev.metrics_table(y_va, p, ev.tune_threshold(y_va, p), name + ", tuned threshold")])
    rows["accuracy_for_reference"] = [float(((p >= t) == y_va).mean()) for t in rows["threshold"]]
    majority_accuracy = float(max(y_va.mean(), 1 - y_va.mean()))
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    rows.round(4).to_csv(out)
    print(rows[["threshold", "precision", "recall", "f1", "pr_auc", "roc_auc", "capture_rate_20",
                "accuracy_for_reference"]].round(4).to_string())
    print(f"majority-class accuracy on the same validation rows: {majority_accuracy:.4f}")
    return rows, majority_accuracy


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    run()
