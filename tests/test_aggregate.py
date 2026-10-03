import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import aggregate  # noqa: E402


def test_weighted_median_and_mean():
    assert aggregate.weighted_median([1, 2, 3], [1, 1, 1]) == 2
    assert aggregate.weighted_median([1, 2, 10], [1, 1, 5]) == 10
    assert aggregate.weighted_median([np.nan, np.nan], [1, 1]) != aggregate.weighted_median([np.nan, np.nan], [1, 1])
    assert aggregate.weighted_mean([0, 1], [3, 1]) == 0.25


def frame(n, month, tag, resolved, weight):
    return pd.DataFrame({
        "collected_tags": [[tag]] * n,
        "created_at": pd.Timestamp(f"{month}-10", tz="UTC"),
        "sampling_weight": weight,
        "target_resolved_7d": resolved, "target_answered_7d": 1,
        "accepted_given_answered": resolved,
        "hours_to_accept": [5.0 if r else np.nan for r in resolved],
        "hours_to_first_answer": 2.0,
    })


def test_monthly_tables_weights_and_flags():
    big = frame(40, "2024-03", "python", [1] * 10 + [0] * 30, 10.0)
    small = frame(5, "2024-04", "python", [1] * 5, 1.0)
    both = frame(2, "2024-03", "python", [1, 1], 1.0)
    both["collected_tags"] = [["pandas", "python"]] * 2
    t = aggregate.monthly_tag_tables(pd.concat([big, small, both], ignore_index=True)).set_index(["tag", "month"])
    row = t.loc[("python", "2024-03")]
    assert row.n_sampled == 42 and not row.low_sample
    assert abs(row.resolved_rate_7d - (10 * 10 + 2) / (400 + 2)) < 1e-9
    assert row.median_hours_to_accept == 5.0 and row.median_hours_to_first_answer == 2.0
    assert t.loc[("python", "2024-04")].low_sample
    assert ("pandas", "2024-03") in t.index and t.loc[("pandas", "2024-03")].n_sampled == 2
