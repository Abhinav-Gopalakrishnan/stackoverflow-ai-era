"""Tests for src/error_analysis.py and src/leakage.py. Run: python tests/test_error_leakage.py"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import error_analysis as ea  # noqa: E402
from src import leakage  # noqa: E402


def _toy(n=400, seed=0):
    rng = np.random.default_rng(seed)
    y = rng.binomial(1, 0.5, n)
    p = np.clip(0.5 * y + rng.normal(0.25, 0.25, n), 0, 1)
    df = pd.DataFrame({"question_id": np.arange(1000, 1000 + n), "title": [f"t{i}" for i in range(n)],
                       "tags": [["python", "pandas"]] * n, "title_length": rng.integers(10, 100, n)})
    return df, y, p


def test_sample_confident_errors():
    df, y, p = _toy()
    sheet = ea.sample_confident_errors(df, y, p, 0.5)
    assert list(sheet.columns) == ea.SHEET_COLUMNS and len(sheet) == 30
    assert (sheet["error_type"].value_counts() == 15).all()
    fp, fn = (sheet[sheet["error_type"] == t] for t in ("false_positive", "false_negative"))
    assert (fp["predicted_probability"] >= 0.5).all() and (fp["actual_outcome"] == "unresolved").all()
    assert (fn["predicted_probability"] < 0.5).all() and (fn["actual_outcome"] == "resolved").all()
    # confident: false positives come from the top quarter of wrong-and-high scores
    all_fp = np.sort(p[(p >= 0.5) & (y == 0)])[::-1]
    pool = max(15, int(len(all_fp) * 0.25))
    assert fp["predicted_probability"].min() >= all_fp[pool - 1] - 1e-3
    assert sheet["link"].iloc[0].startswith("https://stackoverflow.com/q/")
    assert sheet["tags"].iloc[0] == "python;pandas" and (sheet["likely_reason"] == "").all()
    pd.testing.assert_frame_equal(sheet, ea.sample_confident_errors(df, y, p, 0.5))  # seeded


def test_summaries():
    df, y, p = _toy()
    sheet = ea.sample_confident_errors(df, y, p, 0.5)
    sheet.loc[:9, "likely_reason"] = "very short title"
    sheet.loc[10:14, "likely_reason"] = "rare tag"
    counts = ea.summarise_reasons(sheet)
    assert counts["total"].sum() == 15 and counts.index[0] == "very short title"
    table = ea.error_rate_by(df, y, p, 0.5, "title_length", bins=[0, 40, 70, 100])
    assert table["n"].sum() == len(df) and table["error_rate"].between(0, 1).all()


def test_leakage_checks():
    ok = ["title_length", "has_error_text", "tag_python", "title_tfidf_svd_3", "question_word_how"]
    assert leakage.check_feature_columns(ok) == [] and leakage.unexpected_columns(ok) == []
    bad = ["title_length", "hours_to_accept", "sampling_weight", "target_answered_7d", "score"]
    assert [c for c, _ in leakage.check_feature_columns(bad)] == bad[1:]
    assert leakage.unexpected_columns(["title_length", "mystery_col"]) == ["mystery_col"]
    try:
        leakage.assert_no_leakage(bad)
    except AssertionError as e:
        assert "hours_to_accept" in str(e)
    else:
        raise AssertionError("expected failure")


def test_expected_lagged_volume_hand_checked():
    # weeks are the table's own 7-day steps (here Mondays). Posting date Wed 2024-03-13 -> posting week starts 2024-03-11.
    # 4 weeks used: 02-12, 02-19, 02-26, 03-04; previous 4: 01-15, 01-22, 01-29, 02-05.
    weeks = pd.date_range("2024-01-01", "2024-03-25", freq="7D")  # includes the posting week
    rows = [(t, w, 100 * (i + 1) if t == "python" else 10)
            for t in ("python", "pandas") for i, w in enumerate(weeks)]
    wc = pd.DataFrame(rows, columns=["tag", "week_start", "count"])
    py = wc[wc.tag == "python"].set_index("week_start")["count"]
    recent = py["2024-02-12":"2024-03-04"].sum()
    before = py["2024-01-15":"2024-02-05"].sum()
    vol, change = leakage.expected_lagged_volume(wc, ["python"], "2024-03-13 15:30")
    # python counts are 100 * (week number): weeks 7-10 -> 700+800+900+1000, weeks 3-6 -> 300+400+500+600
    assert recent == 3400 and before == 1800
    assert vol == recent and change == recent - before
    # the posting week and later weeks never matter
    wc2 = wc.copy()
    wc2.loc[wc2["week_start"] >= "2024-03-11", "count"] = 10**6
    assert leakage.expected_lagged_volume(wc2, ["python"], "2024-03-13") == (vol, change)
    # two tags sum; missing history gives NaN
    assert leakage.expected_lagged_volume(wc, ["python", "pandas"], "2024-03-13")[0] == recent + 40
    assert np.isnan(leakage.expected_lagged_volume(wc, ["python"], "2024-01-20")[0])


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print("ok", t.__name__)
    print(f"{len(tests)} tests passed")
