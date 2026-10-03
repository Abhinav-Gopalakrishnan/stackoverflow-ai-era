"""Enrichment: accepted/first answer dates and asker account dates (M2-03).

Input: a questions DataFrame with question_id, accepted_answer_id, owner_user_id.
Output (data/processed/): answers.parquet and users.parquet. User IDs are hashed
with SHA-256 + HASH_SALT (from .env) as soon as they are fetched; raw IDs and
names are never stored.
"""
import hashlib
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

try:
    from src.collect import _ENDPOINT_FILTERS, api_get
except ModuleNotFoundError:
    from collect import _ENDPOINT_FILTERS, api_get

load_dotenv()

BATCH = 100
ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"


def hash_user_id(user_id, salt=None):
    salt = salt if salt is not None else os.environ["HASH_SALT"]
    return hashlib.sha256(f"{salt}{int(user_id)}".encode()).hexdigest()


def _chunks(values, size=BATCH):
    values = list(values)
    for i in range(0, len(values), size):
        yield values[i:i + size]


def _ids(chunk):
    return ";".join(str(int(v)) for v in chunk)


def _paged(get, endpoint, n_ids, params):
    page = 1
    while True:
        data = get(endpoint, params, n_ids=n_ids, page=page)
        yield from data.get("items", [])
        if not data.get("has_more"):
            return
        page += 1


def fetch_accepted_answer_dates(answer_ids, get=api_get):
    rows = []
    for chunk in _chunks(answer_ids):
        for a in _paged(get, f"answers/{_ids(chunk)}", len(chunk), {"pagesize": BATCH}):
            rows.append({"accepted_answer_id": a["answer_id"], "question_id": a["question_id"],
                         "accepted_answer_creation_date": a["creation_date"]})
    return pd.DataFrame(rows, columns=["accepted_answer_id", "question_id", "accepted_answer_creation_date"]).astype("int64")


def fetch_first_answer_dates(question_ids, get=api_get):
    first = {}
    for chunk in _chunks(question_ids):
        params = {"pagesize": BATCH, "sort": "creation", "order": "asc", "filter": _ENDPOINT_FILTERS["answers"]}
        for a in _paged(get, f"questions/{_ids(chunk)}/answers", len(chunk), params):
            q, t = a["question_id"], a["creation_date"]
            first[q] = min(first.get(q, t), t)
    return pd.DataFrame({"question_id": list(first), "first_answer_creation_date": list(first.values())}).astype("int64")


def fetch_user_dates(user_ids, get=api_get, salt=None):
    rows = []
    for chunk in _chunks(user_ids):
        for u in _paged(get, f"users/{_ids(chunk)}", len(chunk), {"pagesize": BATCH}):
            rows.append({"user_hash": hash_user_id(u["user_id"], salt),
                         "account_creation_date": u["creation_date"]})
    return pd.DataFrame(rows, columns=["user_hash", "account_creation_date"]).astype({"account_creation_date": "int64"})


def _merge_save(new, path, key):
    if path.exists():
        new = pd.concat([pd.read_parquet(path), new], ignore_index=True)
    new = new.drop_duplicates(subset=key, keep="last").reset_index(drop=True)
    new.to_parquet(path, index=False)
    return new


def enrich_questions(questions, get=api_get, out_dir=PROCESSED_DIR, salt=None):
    """Enrich a tag's questions and merge into answers.parquet and users.parquet.

    Questions and askers already present in those files are skipped, so overlapping tags cost no extra calls.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    q = questions.drop_duplicates("question_id")
    answers_path, users_path = out_dir / "answers.parquet", out_dir / "users.parquet"
    if answers_path.exists():
        done = pd.read_parquet(answers_path, columns=["question_id"])["question_id"]
        q = q[~q["question_id"].isin(done)]
    owners = q["owner_user_id"].dropna().astype("int64").unique()
    if users_path.exists():
        known = set(pd.read_parquet(users_path, columns=["user_hash"])["user_hash"])
        owners = [o for o in owners if hash_user_id(o, salt) not in known]

    accepted = fetch_accepted_answer_dates(q["accepted_answer_id"].dropna().astype("int64").unique(), get)
    with_answers = q.loc[q["answer_count"] > 0, "question_id"] if "answer_count" in q else q["question_id"]
    first = fetch_first_answer_dates(with_answers.unique(), get)
    answers = (q[["question_id"]]
               .merge(accepted[["question_id", "accepted_answer_creation_date"]], on="question_id", how="left")
               .merge(first, on="question_id", how="left"))
    users = fetch_user_dates(owners, get, salt)

    answers = _merge_save(answers, answers_path, "question_id")
    users = _merge_save(users, users_path, "user_hash")
    return answers, users


if __name__ == "__main__":
    import sys

    path = sys.argv[1]
    answers, users = enrich_questions(pd.read_parquet(path))
    print(f"{path}: answers.parquet {len(answers)} rows, users.parquet {len(users)} rows")
