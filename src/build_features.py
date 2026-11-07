"""Feature matrix from the cleaned table, following docs/feature_spec.md.

Stand-in used by the Member 5 modelling run until Member 4's saved feature pipeline
(M4-05 to M4-09) is available; the column names match the spec, so the two can be
swapped. Title text (TF-IDF + SVD) is NOT built here: it is fitted inside the model
pipeline (``src/models.py``) so it is refitted on training data only in every fold.

Input: ``questions_clean_v1`` columns used: question_id, title, tags, plain_body,
n_code_blocks, code_ratio, has_error_text, account_age_days, missing_account_age,
created_at, sampling_weight, and the two targets.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src import features as m4

DEFAULT_TAGS = ["python", "javascript", "java", "sql", "pandas", "reactjs", "android", "excel",
                "r", "docker", "powerbi", "fastapi", "openai-api"]
REQUIRED = ["title", "tags", "plain_body", "n_code_blocks", "code_ratio",
            "has_error_text", "account_age_days", "missing_account_age", "created_at"]
META = ["question_id", "created_at", "title", "tags", "sampling_weight",
        "target_resolved_7d", "target_answered_7d"]
NEW_ACCOUNT_DAYS = 7
LAG_WEEKS = 4


def selected_tags(config_path="config.yaml"):
    """Study tags from config.yaml (falls back to the agreed list)."""
    try:
        import yaml

        with open(config_path) as f:
            return list(yaml.safe_load(f)["study"]["tags"])
    except Exception:
        return list(DEFAULT_TAGS)


def lagged_tag_volume(created_at, tag_matrix, weekly_counts, weeks=LAG_WEEKS):
    """Questions in the question's tags during the ``weeks`` full weeks before its posting week.

    Returns ``(volume, change)`` arrays. ``change`` = volume minus the same total for the
    ``weeks`` before that. Uses only weeks strictly before the posting week (the week
    containing the posting date is never used) and the complete weekly counts, not the
    sampled records. NaN where any needed week is missing (e.g. early 2019).

    ``tag_matrix``: DataFrame, one 0/1 column per selected tag (column name = tag).
    ``weekly_counts``: columns tag, week_start, count (Member 1's weekly_counts.csv).
    """
    wc = weekly_counts.copy()
    wc["week_start"] = pd.to_datetime(wc["week_start"]).dt.tz_localize(None).dt.normalize()
    base = wc["week_start"].min()
    n_weeks = int((wc["week_start"].max() - base).days // 7) + 1
    grid = np.full((len(tag_matrix.columns), n_weeks), np.nan)
    row = {t: i for i, t in enumerate(tag_matrix.columns)}
    keep = wc[wc["tag"].isin(row)]
    grid[keep["tag"].map(row).to_numpy(), ((keep["week_start"] - base).dt.days // 7).to_numpy()] = \
        keep["count"].to_numpy()

    value = np.concatenate([np.zeros((grid.shape[0], 1)), np.cumsum(np.nan_to_num(grid), axis=1)], axis=1)
    missing = np.concatenate([np.zeros((grid.shape[0], 1)), np.cumsum(np.isnan(grid), axis=1)], axis=1)

    posted = pd.to_datetime(created_at, utc=True).dt.tz_localize(None).dt.normalize()
    w = ((posted - base).dt.days // 7).to_numpy()  # posting week index
    onehot = tag_matrix.to_numpy().astype(float)

    def window(first, last):  # weeks first..last inclusive: total over the question's tags
        usable = (first >= 0) & (last < n_weeks) & (w >= 0)
        lo, hi = np.clip(first, 0, n_weeks), np.clip(last + 1, 0, n_weeks)
        total = (value[:, hi] - value[:, lo]).T                  # questions x tags
        gaps = (missing[:, hi] - missing[:, lo]).T > 0
        mine = onehot > 0
        unknown = ((gaps & mine).any(axis=1)) | ~usable
        result = np.where(mine, total, 0.0).sum(axis=1)
        result[unknown] = np.nan
        return result

    recent = window(w - weeks, w - 1)
    before = window(w - 2 * weeks, w - weeks - 1)
    return recent, recent - before


def build_features(q, weekly_counts=None, tags=None):
    """Spec features plus the meta columns needed to split and score.

    Returns a DataFrame; the model feature columns are listed by
    ``src.models.feature_lists``. Rows with no weekly history yet (the first weeks of
    2019, when lagged volume is undefined) are dropped and counted in ``attrs``.
    """
    missing = [c for c in REQUIRED if c not in q.columns]
    if missing:
        raise KeyError(f"cleaned table is missing columns: {missing}")
    tags = tags or selected_tags()
    out = q[[c for c in META if c in q]].copy()
    created = pd.to_datetime(q["created_at"], utc=True)
    out["created_at"] = created
    tag_lists = q["tags"].map(lambda t: list(t) if t is not None else [])

    out["title_length"] = q["title"].str.len()
    out["body_length"] = q["plain_body"].str.len()
    out["n_code_blocks"] = q["n_code_blocks"]
    out["code_ratio"] = q["code_ratio"]
    out["has_error_text"] = q["has_error_text"].astype(int)
    out["question_word"] = m4.get_question_word(q)
    out["tag_count"] = tag_lists.map(len)
    out["hour_posted"] = created.dt.hour
    out["weekday_posted"] = created.dt.weekday
    out["month_posted"] = created.dt.month
    # Undo the cleaning-stage global imputation. Each fitted model/fold learns
    # its own median inside its preprocessing pipeline.
    out["account_age_days"] = q["account_age_days"].where(~q["missing_account_age"].astype(bool))
    out["missing_account_age"] = q["missing_account_age"].astype(int)
    out["new_account"] = ((q["account_age_days"] <= NEW_ACCOUNT_DAYS)
                          & ~q["missing_account_age"].astype(bool)).astype(int)

    tag_matrix = pd.DataFrame({t: tag_lists.map(lambda ts, t=t: int(t in ts)) for t in tags},
                              index=q.index)
    for t in tags:
        out[f"tag_{t}"] = tag_matrix[t]
    out["other_tags_count"] = out["tag_count"] - tag_matrix.sum(axis=1)

    dropped = 0
    if weekly_counts is not None:
        vol, change = lagged_tag_volume(created, tag_matrix, weekly_counts)
        out["lagged_tag_volume"], out["lagged_tag_change"] = vol, change
        keep = ~np.isnan(vol) & ~np.isnan(change)
        dropped = int((~keep).sum())
        out = out[keep]
    out.attrs["dropped_no_history"] = dropped
    out.attrs["tags"] = tags
    return out.reset_index(drop=True)
