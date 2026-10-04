"""Leakage checks for the feature matrix (M5-05, M5-06; sign-off for M4-08).

``check_feature_columns`` flags any forbidden column; ``unexpected_columns``
flags anything not named in docs/feature_spec.md. ``expected_lagged_volume`` is
an independent implementation of the lagged tag volume, for checking Member 4's
numbers on hand-picked questions.
"""

from __future__ import annotations

import pandas as pd

FORBIDDEN = {
    # docs/feature_spec.md section 2: known only after posting
    "score": "forbidden by the leakage rule", "views": "forbidden by the leakage rule",
    "view_count": "forbidden by the leakage rule", "answer_count": "forbidden by the leakage rule",
    "is_answered": "forbidden by the leakage rule", "closed_date": "closed status",
    "closed_at": "closed status", "closed_status": "closed status",
    "comments": "forbidden by the leakage rule", "comment_count": "forbidden by the leakage rule",
    "reputation": "current reputation", "owner_reputation": "current reputation",
    # outcome fields produced by cleaning (missing from the spec's forbidden list)
    "hours_to_accept": "contains the outcome", "hours_to_first_answer": "contains the outcome",
    "accepted_at": "contains the outcome", "first_answer_at": "contains the outcome",
    "accepted_answer_id": "contains the outcome",
    "accepted_answer_creation_date": "contains the outcome",
    "first_answer_creation_date": "contains the outcome",
    "target_resolved_7d": "target", "target_answered_7d": "other target",
    "accepted_given_answered": "function of both targets",
    "last_activity_date": "recorded after posting", "last_activity_at": "recorded after posting",
    # excluded by design or proxies for the time period / identity
    "post_ai": "excluded by design", "first_question": "excluded by design",
    "sampling_weight": "proxy for the time period; use as sample weight only",
    "collected_tag": "collection artifact", "collected_tags": "collection artifact",
    "question_id": "identifier correlated with time", "user_hash": "identifier",
    "creation_date": "raw time; use hour/weekday/month", "created_at": "raw time; use hour/weekday/month",
    "account_created_at": "raw date; use account_age_days",
}
ALLOWED = {
    "title_length", "body_length", "n_code_blocks", "code_ratio", "has_error_text", "question_word",
    "tag_count", "hour_posted", "weekday_posted", "month_posted", "account_age_days",
    "missing_account_age", "new_account", "lagged_tag_volume", "lagged_tag_change",
    "other_tags_count",
}
ALLOWED_PREFIXES = ("tag_", "title_tfidf_svd_", "question_word_")


def check_feature_columns(columns):
    """List of ``(column, reason)`` for every forbidden column."""
    return [(c, FORBIDDEN[c]) for c in columns if c in FORBIDDEN]


def unexpected_columns(columns):
    """Columns that are neither in the spec nor forbidden (to review by hand)."""
    return [c for c in columns
            if c not in ALLOWED and c not in FORBIDDEN and not c.startswith(ALLOWED_PREFIXES)]


def assert_no_leakage(columns):
    """Raise if any forbidden column is present."""
    bad = check_feature_columns(columns)
    if bad:
        raise AssertionError("forbidden columns in feature matrix: "
                             + ", ".join(f"{c} ({why})" for c, why in bad))


def expected_lagged_volume(weekly_counts, tags, posting_date, weeks=4):
    """Lagged tag volume and change, computed independently of Member 4's code.

    ``weekly_counts`` has columns ``tag, week_start, count`` (the complete counts,
    not sampled). Weeks are the ones in the table (Member 1's weeks are anchored on
    2019-01-01, i.e. 7-day steps). The posting week is the last ``week_start`` on or
    before the posting date and is never used. Volume = total over the ``weeks`` full
    weeks before it, change = volume minus the ``weeks`` before those. Questions with
    several tags use the sum over their distinct tags. Returns ``(volume, change)``;
    NaN if any needed week is missing.
    """
    posted = pd.Timestamp(posting_date).tz_localize(None).normalize()
    wc = weekly_counts.copy()
    wc["week_start"] = pd.to_datetime(wc["week_start"]).dt.tz_localize(None).dt.normalize()
    posting_week = wc.loc[wc["week_start"] <= posted, "week_start"].max()
    if pd.isna(posting_week):
        return float("nan"), float("nan")
    wc = wc[wc["tag"].isin(set(tags))]

    def window(first, last):  # inclusive weeks first..last, step 7 days
        needed = pd.date_range(first, last, freq="7D")
        got = wc[wc["week_start"].isin(needed)]
        per_tag = got.groupby("tag")["week_start"].nunique()
        if len(per_tag) < len(set(tags)) or (per_tag < len(needed)).any():
            return float("nan")
        return float(got["count"].sum())

    recent = window(posting_week - pd.Timedelta(weeks=weeks), posting_week - pd.Timedelta(weeks=1))
    before = window(posting_week - pd.Timedelta(weeks=2 * weeks),
                    posting_week - pd.Timedelta(weeks=weeks + 1))
    return recent, recent - before
