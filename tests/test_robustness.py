import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import robustness  # noqa: E402


def frame():
    return pd.DataFrame({
        "collected_tags": [["sql"]] * 4,
        "created_at": pd.to_datetime(["2024-03-05", "2024-03-06", "2025-02-01", "2025-02-02"], utc=True),
        "sampling_weight": [10.0, 10.0, 1.0, 1.0],
        "target_resolved_7d": [1, 0, 1, 1], "target_answered_7d": [1, 1, 1, 0],
    })


def test_volume_check_and_summary():
    complete = pd.DataFrame({"tag": ["sql", "sql"], "month": ["2024-03", "2025-02"], "count": [25, 2]})
    c = robustness.volume_check(frame(), complete).set_index("month")
    assert c.loc["2024-03", "estimated"] == 20 and abs(c.loc["2024-03", "pct_err"] - (-20)) < 1e-9
    assert c.loc["2025-02", "pct_err"] == 0
    s = robustness.volume_summary(c.reset_index())
    assert s["sampled_tag_months"] == 1 and abs(s["sampled_mean_abs_err_pct"] - 20) < 1e-9 and s["full_max_abs_err_pct"] == 0


def test_weighted_vs_unweighted_and_balance():
    t = robustness.weighted_vs_unweighted(frame())
    assert t.loc[2024, "weighted_resolved"] == 0.5 and t.loc[2025, "resolved_diff_pp"] == 0
    f = frame().assign(month=["2024-03", "2024-03", "2025-02", "2025-02"])
    b = robustness.weighted_balance(f)
    assert b["rows"] == 2 and b["est_questions"] == 20 and b["resolved_7d"] == 0.5
