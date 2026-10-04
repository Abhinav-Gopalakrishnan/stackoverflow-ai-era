"""Error analysis on confident wrong predictions (M5-04, M5-14).

Method (docs/error_analysis_design.md): among the test-period errors, take the
15 most confidently wrong false positives and the 15 most confidently wrong
false negatives (confidence = distance of the predicted probability from the
decision threshold), pick 15 of each at random from the top ``pool_frac`` of that
list with a fixed seed, and write an annotation sheet. The "likely reason"
column is filled in by hand.

Licence: Stack Overflow content is CC BY-SA 4.0. The sheet holds titles only,
each with a link to the original question; raw question text is never written.
"""

from __future__ import annotations

import pandas as pd

SHEET_COLUMNS = ["error_type", "question_id", "title", "tags", "predicted_probability",
                 "actual_outcome", "link", "likely_reason"]
LINK = "https://stackoverflow.com/q/{}"


def sample_confident_errors(df, y_true, y_score, threshold, n_each=15, pool_frac=0.25, seed=42):
    """Annotation sheet: ``n_each`` false positives and ``n_each`` false negatives.

    ``df`` needs ``question_id``, ``title`` and ``tags`` (list or string),
    aligned row by row with ``y_true`` and ``y_score`` (probability of resolved).
    """
    d = df.reset_index(drop=True).copy()
    d["y"] = pd.Series(y_true).reset_index(drop=True)
    d["p"] = pd.Series(y_score).reset_index(drop=True).astype(float)
    parts = []
    for error_type, mask, confidence in (
        ("false_positive", (d["p"] >= threshold) & (d["y"] == 0), d["p"] - threshold),
        ("false_negative", (d["p"] < threshold) & (d["y"] == 1), threshold - d["p"]),
    ):
        errors = d[mask].assign(confidence=confidence[mask]).sort_values("confidence", ascending=False)
        pool = errors.head(max(n_each, int(len(errors) * pool_frac)))
        pick = pool.sample(min(n_each, len(pool)), random_state=seed)
        parts.append(pick.assign(error_type=error_type))
    out = pd.concat(parts, ignore_index=True)
    out["tags"] = out["tags"].map(lambda t: ";".join(t) if isinstance(t, (list, tuple)) else t)
    out["predicted_probability"] = out["p"].round(3)
    out["actual_outcome"] = out["y"].map({1: "resolved", 0: "unresolved"})
    out["link"] = out["question_id"].map(lambda q: LINK.format(q))
    out["likely_reason"] = ""
    return out[SHEET_COLUMNS]


def write_annotation_sheet(sheet, path):
    sheet.to_csv(path, index=False)
    return path


def summarise_reasons(annotated):
    """Counts of each hand-written reason, split by error type."""
    done = annotated[annotated["likely_reason"].fillna("").str.strip() != ""]
    return (done.groupby(["likely_reason", "error_type"]).size()
            .unstack(fill_value=0).assign(total=lambda t: t.sum(axis=1))
            .sort_values("total", ascending=False))


def error_rate_by(df, y_true, y_score, threshold, column, bins=None):
    """Error rate and counts per group of ``column`` (optionally binned), to spot patterns.

    Example: very short titles or rare tags having a higher error rate.
    """
    d = df.reset_index(drop=True).copy()
    d["error"] = ((pd.Series(y_score).reset_index(drop=True) >= threshold).astype(int)
                  != pd.Series(y_true).reset_index(drop=True)).astype(int)
    group = pd.cut(d[column], bins) if bins is not None else d[column]
    table = d.groupby(group, observed=True)["error"].agg(n="size", errors="sum", error_rate="mean")
    return table.round({"error_rate": 3})
