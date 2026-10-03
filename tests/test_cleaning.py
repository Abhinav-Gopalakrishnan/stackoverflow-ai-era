import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import cleaning  # noqa: E402

T0 = int(pd.Timestamp("2024-03-01", tz="UTC").timestamp())
H = 3600


def q(qid, tag="python", weight=10.0, owner=1, created=T0, body="<p>hi</p>", acc=None):
    return {"question_id": qid, "collected_tag": tag, "sampling_weight": weight, "owner_user_id": owner,
            "creation_date": created, "closed_date": None, "last_activity_date": created, "body": body,
            "accepted_answer_id": acc, "answer_count": 0}


def test_merge_keeps_smaller_weight_and_all_tags():
    a = pd.DataFrame([q(1, "python", 20.0), q(2, "python", 5.0)])
    b = pd.DataFrame([q(1, "pandas", 8.0)])
    ans = pd.DataFrame({"question_id": [1], "accepted_answer_creation_date": [T0 + H],
                        "first_answer_creation_date": [T0 + H]})
    users = pd.DataFrame({"user_hash": [], "account_creation_date": []})
    out, stats = cleaning.merge_questions([a, b], ans, users, salt="s")
    assert stats["rows_before"] == 3 and stats["rows_after"] == 2 and stats["duplicates_removed"] == 1
    assert stats["weight_conflicts"] == 1
    row = out[out.question_id == 1].iloc[0]
    assert row.sampling_weight == 8.0 and row.collected_tags == ["pandas", "python"]
    assert "owner_user_id" not in out.columns and out.user_hash.notna().all()


def test_split_html_separates_code():
    html = "<p>Why <code>x = 1</code> fails?</p><pre><code>Traceback (most recent call last)\nValueError</code></pre>"
    plain, code, n = cleaning.split_html(html)
    assert plain == "Why fails?" and n == 1
    assert "Traceback" in code and "x = 1" in code


def test_text_features():
    df = pd.DataFrame({"body": ["<p>no code here</p>", "<p>see</p><pre><code>Error: boom</code></pre>"]})
    out = cleaning.add_text_features(df)
    assert list(out.n_code_blocks) == [0, 1]
    assert list(out.has_error_text) == [False, True]
    assert out.code_ratio[0] == 0 and 0 < out.code_ratio[1] < 1


def base_frame():
    rows = [q(1, acc=10), q(2), q(3, acc=30), q(4, created=T0 + 40 * 86400)]
    df = pd.DataFrame(rows)
    df["accepted_answer_creation_date"] = [T0 + 2 * H, None, T0 + 200 * H, None]
    df["first_answer_creation_date"] = [T0 + H, None, T0 + 169 * H, T0 + 41 * 86400]
    df["account_creation_date"] = [T0 - 86400 * 100, None, T0 - 86400 * 300, T0 - 86400 * 50]
    return df


def test_timestamps_and_checks():
    df = base_frame()
    df.loc[1, "first_answer_creation_date"] = T0 - H
    out, checks = cleaning.convert_timestamps(df)
    assert str(out.created_at[0]) == "2024-03-01 00:00:00+00:00"
    assert checks["first_answer_before_question"] == 1 and checks["accepted_before_question"] == 0


def test_targets_and_maturity():
    out, _ = cleaning.convert_timestamps(base_frame())
    out, stats = cleaning.add_targets(out, "2024-04-05")
    assert stats["immature_dropped"] == 1 and len(out) == 3
    assert list(out.target_resolved_7d) == [1, 0, 0]
    assert list(out.target_answered_7d) == [1, 0, 0]
    assert out.accepted_given_answered.iloc[0] == 1 and pd.isna(out.accepted_given_answered.iloc[1])


def test_account_age_imputes_training_median():
    out, _ = cleaning.convert_timestamps(base_frame())
    out, stats = cleaning.add_account_age(out)
    assert list(out.missing_account_age) == [False, True, False, False]
    assert out.account_age_days.notna().all()
    assert stats["account_age_median_days"] == out.account_age_days[1]


def test_flag_invalid_never_uses_targets():
    df = pd.DataFrame({
        "body": ["<p>ok question here</p>", "", "<p>http://spam.example</p>", "<p>" + "я" * 40 + "</p>"],
        "plain_body": ["ok question here", "", "http://spam.example", "я" * 40],
        "code_text": ["", "", "", ""],
        "target_resolved_7d": [1, 1, 1, 1],
    })
    out, stats = cleaning.flag_invalid(df)
    assert len(out) == 1 and out.plain_body.iloc[0] == "ok question here"
    assert stats["empty_removed"] == 1 and stats["non_english_removed"] == 1 and stats["spam_like_removed"] == 1


def test_account_age_never_negative():
    df = base_frame()
    df.loc[0, "account_creation_date"] = T0 + 5 * 86400
    out, _ = cleaning.convert_timestamps(df)
    out, _ = cleaning.add_account_age(out)
    assert (out.account_age_days >= 0).all() and out.account_age_days[0] == 0
