import hashlib
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import enrich  # noqa: E402


CALLS = []


def fake_get(endpoint, params=None, n_ids=0, page=1):
    CALLS.append(endpoint)
    ids = [int(i) for i in endpoint.split("/")[1].split(";")]
    if endpoint.startswith("answers/"):
        return {"items": [{"answer_id": a, "question_id": a // 10, "creation_date": 1000 + a} for a in ids], "has_more": False}
    if endpoint.startswith("questions/"):
        items = [{"answer_id": q * 10 + k, "question_id": q, "creation_date": 5000 - k * 100} for q in ids for k in (1, 2)]
        half = len(items) // 2
        if page == 1 and len(items) > 2:
            return {"items": items[:half], "has_more": True}
        return {"items": items[half:] if len(items) > 2 else items, "has_more": False}
    return {"items": [{"user_id": u, "creation_date": 200 + u} for u in ids], "has_more": False}


def test_enrich_questions(tmp_path):
    qs = pd.DataFrame({
        "question_id": range(1, 251),
        "accepted_answer_id": [q * 10 + 1 if q % 2 == 0 else None for q in range(1, 251)],
        "owner_user_id": [q % 7 + 1 if q % 11 else None for q in range(1, 251)],
        "answer_count": [2] * 250,
    })
    qs = pd.concat([qs, qs.iloc[:5]])
    answers, users = enrich.enrich_questions(qs, get=fake_get, out_dir=tmp_path, salt="s")
    assert len(answers) == 250 and answers.question_id.is_unique
    assert answers.accepted_answer_creation_date.notna().sum() == 125
    assert (answers.first_answer_creation_date == 4800).all()
    assert hashlib.sha256(b"s3").hexdigest() in set(users.user_hash) and len(users) == 7
    assert list(users.columns) == ["user_hash", "account_creation_date"]
    CALLS.clear()
    enrich.enrich_questions(qs, get=fake_get, out_dir=tmp_path, salt="s")
    assert CALLS == []
    assert len(pd.read_parquet(tmp_path / "answers.parquet")) == 250
    assert len(pd.read_parquet(tmp_path / "users.parquet")) == 7


def test_overlapping_tag_only_fetches_new_questions(tmp_path):
    first = pd.DataFrame({"question_id": [1, 2], "accepted_answer_id": [11.0, None], "owner_user_id": [1, 2], "answer_count": [2, 2]})
    second = pd.DataFrame({"question_id": [2, 3], "accepted_answer_id": [None, 31.0], "owner_user_id": [2, 3], "answer_count": [2, 2]})
    enrich.enrich_questions(first, get=fake_get, out_dir=tmp_path, salt="s")
    CALLS.clear()
    answers, users = enrich.enrich_questions(second, get=fake_get, out_dir=tmp_path, salt="s")
    assert sorted(answers.question_id) == [1, 2, 3] and len(users) == 3
    assert [c.split("/")[1] for c in CALLS if c.startswith("users/")] == ["3"]
