"""Date-based validation folds and rolling-origin windows (docs/evaluation_plan.md).

Both helpers cut by calendar date, never by row count, and leave a gap of
``gap_days`` between the end of training and the start of testing. A label is
only known 7 days after posting, so a question posted inside that gap has a
label that would not be available yet at the cut-off.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

GAP_DAYS = 7


def _utc(dates):
    return pd.to_datetime(pd.Series(dates).reset_index(drop=True), utc=True)


def time_series_folds(dates, n_splits=5, gap_days=GAP_DAYS):
    """Expanding-window folds: list of ``(train_positions, test_positions)``.

    The date range is cut into ``n_splits + 1`` chunks of equal row count at
    date boundaries. Fold *i* tests on chunk *i* and trains on every row dated
    before that chunk's start minus ``gap_days``. Positions are integer row
    positions, so the list can be passed straight to ``RandomizedSearchCV(cv=...)``.
    """
    d = _utc(dates)
    seconds = (d - d.min()).dt.total_seconds().to_numpy()
    edges = np.quantile(seconds, np.linspace(0, 1, n_splits + 2))
    gap = gap_days * 86400
    folds = []
    for i in range(1, n_splits + 1):
        last = i == n_splits
        test = np.flatnonzero((seconds >= edges[i]) & ((seconds <= edges[i + 1]) if last
                                                      else (seconds < edges[i + 1])))
        train = np.flatnonzero(seconds < edges[i] - gap)
        if len(train) and len(test):
            folds.append((train, test))
    return folds


def half_year_windows(first_start="2021-01-01", last_start="2026-01-01"):
    """Half-year test windows as ``(label, start, end)``; 2021 H1 to 2026 H1 gives 11."""
    windows = []
    start = pd.Timestamp(first_start, tz="UTC")
    last = pd.Timestamp(last_start, tz="UTC")
    while start <= last:
        end = start + pd.DateOffset(months=6)
        windows.append((f"{start.year} H{1 if start.month <= 6 else 2}", start, end))
        start = end
    return windows
