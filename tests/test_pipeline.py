"""Tests for src/build_features.py, src/run_models.py and src/make_slides.py (synthetic data only).

Run: python tests/test_pipeline.py   (needs xgboost, shap, python-pptx; takes about a minute)
"""

import json
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import build_features as bf  # noqa: E402
from src import leakage, make_slides, models, run_models  # noqa: E402

CLEAN = models.make_synthetic_clean(2500)
WEEKLY = models.make_synthetic_weekly(bf.DEFAULT_TAGS)


def test_lagged_volume_matches_independent_implementation():
    feat = bf.build_features(CLEAN, WEEKLY)
    assert feat.attrs["dropped_no_history"] > 0          # first weeks of 2019 have no history
    first_ok = pd.Timestamp(WEEKLY["week_start"].min()).tz_localize("UTC") + pd.Timedelta(weeks=8)
    assert feat["created_at"].min() >= first_ok
    tags_by_id = CLEAN.set_index("question_id")["tags"]
    for _, r in feat.sample(60, random_state=0).iterrows():
        tags = [t for t in tags_by_id[r["question_id"]] if t in bf.DEFAULT_TAGS]
        volume, change = leakage.expected_lagged_volume(WEEKLY, tags, r["created_at"])
        assert volume == r["lagged_tag_volume"] and change == r["lagged_tag_change"]


def test_lagged_volume_ignores_posting_week_and_later():
    changed = WEEKLY.copy()
    changed.loc[changed["week_start"] >= "2024-01-01", "count"] = 10**7
    a = bf.build_features(CLEAN, WEEKLY)
    b = bf.build_features(CLEAN, changed)
    early = a["created_at"] < "2023-12-01"            # posting weeks well before the change
    assert (a.loc[early, "lagged_tag_volume"].to_numpy() == b.loc[early, "lagged_tag_volume"].to_numpy()).all()


def test_feature_columns_pass_leakage_check():
    feat = bf.build_features(CLEAN, WEEKLY)
    cols = [c for c in feat.columns if c not in bf.META]
    assert leakage.check_feature_columns(cols) == [] and leakage.unexpected_columns(cols) == []
    assert feat["new_account"].isin([0, 1]).all() and "tag_python" in feat and "other_tags_count" in feat


def test_run_all_and_slides_on_synthetic_data():
    feat = models.make_synthetic_data(5000)
    with tempfile.TemporaryDirectory() as tmp:
        R = run_models.run_all(feat, f"{tmp}/m5", n_iter=2, n_splits=2, tune_rows=3000, svd_components=10,
                               max_features=500, do_rolling=False)
        out = Path(tmp, "m5")
        for name in ("model_comparison_val.csv", "feature_gain.csv", "test_metrics.csv", "shap_top.csv",
                     "secondary_target.csv", "error_annotation_sheet.csv", "results.json", ".test_evaluated"):
            assert (out / name).exists(), name
        assert R["chosen"]["model"] in ("logistic regression", "random forest", "xgboost")
        assert len(R["split"]) == 3 and R["unexpected_columns"] == []
        try:                                             # the test period can be evaluated only once
            run_models.run_all(feat, f"{tmp}/m5", n_iter=2, n_splits=2, tune_rows=3000, do_rolling=False)
        except RuntimeError:
            pass
        else:
            raise AssertionError("a second run on the same output folder must be refused")
        run_models.rolling_only(feat, out)               # adds rolling-origin to the finished run
        added = json.loads((out / "results.json").read_text())
        assert added["rolling"]["windows"] >= 8 and (out / "rolling_origin.png").exists()
        assert added["test"] == R["test"]                # the test result is untouched
        deck = make_slides.build_deck(out, f"{tmp}/slides_no_m4.pptx")
        pd.DataFrame({"threshold": [0.5, 0.36], "precision": [0.42, 0.36], "recall": [0.16, 0.91], "f1": [0.23, 0.51],
                      "pr_auc": [0.39, 0.39], "roc_auc": [0.58, 0.58]},
                     index=["logistic regression (Member 4 features), threshold 0.5",
                            "logistic regression (Member 4 features), tuned threshold"]).to_csv(out / "m4_baseline_val.csv")
        deck = make_slides.build_deck(out, f"{tmp}/slides.pptx")
        from pptx import Presentation
        first_table = [sh for sh in Presentation(deck).slides[0].shapes if sh.has_table][0].table
        assert len(first_table.rows) == 6 and "Member 4" in first_table.cell(2, 0).text
        findings = make_slides.build_findings(out, f"{tmp}/findings.md")
        assert Path(deck).stat().st_size > 10000
        assert "unresolved" in Path(findings).read_text()
        assert json.loads((out / "results.json").read_text())["test"]["n"] > 0


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print("ok", t.__name__)
    print(f"{len(tests)} tests passed")
