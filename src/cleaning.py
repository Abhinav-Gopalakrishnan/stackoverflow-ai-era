"""Cleaning and preprocessing (M2-05 to M2-10).

Pipeline: merge_questions -> convert_timestamps -> add_text_features ->
add_account_age -> add_targets -> flag_invalid -> clean_questions (all steps).
Every step records what it changed in a stats dict so the notebook can show
before/after numbers.
"""
import re
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup

WINDOW_START = pd.Timestamp("2019-01-01", tz="UTC")
WINDOW_END = pd.Timestamp("2026-09-01", tz="UTC")
TRAIN_END = pd.Timestamp("2025-01-01", tz="UTC")
MATURITY_DAYS = 30
WINDOW_HOURS = 168
LONG_BODY_QUANTILE = 0.999
NON_ENGLISH_RATIO = 0.5
ERROR_PATTERN = re.compile(r"Traceback|Exception|Error:|errno")
URL_PATTERN = re.compile(r"https?://")


def merge_questions(frames, answers, users, salt=None):
    """M2-05: one row per question_id; join answers and hashed askers."""
    from src.enrich import hash_user_id

    q = pd.concat(frames, ignore_index=True)
    stats = {"rows_before": len(q)}
    tags_by_q = q.groupby("question_id")["collected_tag"].agg(lambda s: sorted(set(s)))
    weight_spread = q.groupby("question_id")["sampling_weight"].nunique()
    stats["weight_conflicts"] = int((weight_spread > 1).sum())
    q = (q.sort_values("sampling_weight", kind="stable")
          .drop_duplicates("question_id", keep="first")
          .sort_values("question_id").reset_index(drop=True))
    q["collected_tags"] = q["question_id"].map(tags_by_q)
    stats["rows_after"] = len(q)
    stats["duplicates_removed"] = stats["rows_before"] - stats["rows_after"]

    owners = q["owner_user_id"].dropna().astype("int64").unique()
    hashes = {u: hash_user_id(u, salt) for u in owners}
    q["user_hash"] = q["owner_user_id"].map(lambda u: hashes.get(int(u)) if pd.notna(u) else None)
    q = q.drop(columns=["owner_user_id"])

    q = q.merge(answers, on="question_id", how="left").merge(users, on="user_hash", how="left")
    assert len(q) == stats["rows_after"]
    return q, stats


def convert_timestamps(df):
    """M2-06: Unix seconds -> UTC datetimes, plus consistency checks."""
    df = df.copy()
    pairs = {
        "creation_date": "created_at", "closed_date": "closed_at", "last_activity_date": "last_activity_at",
        "accepted_answer_creation_date": "accepted_at", "first_answer_creation_date": "first_answer_at",
        "account_creation_date": "account_created_at",
    }
    for src, dst in pairs.items():
        df[dst] = pd.to_datetime(df[src], unit="s", utc=True)
    checks = {
        "accepted_before_question": int((df["accepted_at"] < df["created_at"]).sum()),
        "first_answer_before_question": int((df["first_answer_at"] < df["created_at"]).sum()),
        "accepted_before_first_answer": int((df["accepted_at"] < df["first_answer_at"]).sum()),
        "question_outside_window": int(((df["created_at"] < WINDOW_START) | (df["created_at"] >= WINDOW_END)).sum()),
        "account_after_question": int((df["account_created_at"] > df["created_at"]).sum()),
    }
    return df, checks


def split_html(html):
    """Return (plain_body, code_text, n_code_blocks) for one question body."""
    soup = BeautifulSoup(html or "", "html.parser")
    blocks = soup.find_all("pre")
    code = [b.get_text() for b in blocks]
    for b in blocks:
        b.decompose()
    for c in soup.find_all("code"):
        code.append(c.get_text())
        c.decompose()
    plain = re.sub(r"\s+", " ", soup.get_text(" ", strip=True)).strip()
    return plain, "\n".join(code), len(blocks)


def add_text_features(df):
    """M2-07: plain_body, code_text, n_code_blocks, code_ratio, has_error_text."""
    df = df.copy()
    parts = [split_html(h) for h in df["body"]]
    df["plain_body"] = [p[0] for p in parts]
    df["code_text"] = [p[1] for p in parts]
    df["n_code_blocks"] = [p[2] for p in parts]
    plain_len = df["plain_body"].str.len()
    code_len = df["code_text"].str.len()
    df["code_ratio"] = (code_len / (plain_len + code_len).replace(0, np.nan)).fillna(0.0)
    df["has_error_text"] = (df["plain_body"] + "\n" + df["code_text"]).str.contains(ERROR_PATTERN)
    return df


def add_account_age(df):
    """M2-08: account age at posting; deleted/unknown askers get the training-period median."""
    df = df.copy()
    age = ((df["created_at"] - df["account_created_at"]).dt.total_seconds() / 86400).clip(lower=0)
    df["missing_account_age"] = age.isna()
    median = age[df["created_at"] < TRAIN_END].median()
    df["account_age_days"] = age.fillna(median)
    return df, {"account_age_median_days": float(median), "missing_account_age": int(df["missing_account_age"].sum())}


def add_targets(df, collection_date):
    """M2-09: both targets, accepted_given_answered, and the 30-day label maturity rule."""
    df = df.copy()
    cutoff = pd.Timestamp(collection_date, tz="UTC") - timedelta(days=MATURITY_DAYS)
    immature = df["created_at"] > cutoff
    stats = {"immature_dropped": int(immature.sum()), "maturity_cutoff": str(cutoff.date())}
    df = df[~immature].copy()
    df["hours_to_accept"] = (df["accepted_at"] - df["created_at"]).dt.total_seconds() / 3600
    df["hours_to_first_answer"] = (df["first_answer_at"] - df["created_at"]).dt.total_seconds() / 3600
    df["target_resolved_7d"] = (df["hours_to_accept"] <= WINDOW_HOURS).astype(int)
    df["target_answered_7d"] = (df["hours_to_first_answer"] <= WINDOW_HOURS).astype(int)
    df["accepted_given_answered"] = df["target_resolved_7d"].where(df["target_answered_7d"] == 1)
    return df, stats


def flag_invalid(df):
    """M2-10: flag and drop empty, mostly non-English and spam-like posts; cap very long bodies.

    Decisions never look at the targets.
    """
    df = df.copy()
    stats = {}
    empty = (df["plain_body"].str.len() == 0) & (df["code_text"].str.len() == 0)
    letters = df["plain_body"].map(lambda s: sum(c.isalpha() for c in s))
    foreign = df["plain_body"].map(lambda s: sum(c.isalpha() and ord(c) > 127 for c in s))
    non_english = (foreign / letters.replace(0, np.nan)).fillna(0) > NON_ENGLISH_RATIO
    spam = (df["plain_body"].str.len() + df["code_text"].str.len() < 30) & df["body"].str.contains(URL_PATTERN)
    cap = int(df["plain_body"].str.len().quantile(LONG_BODY_QUANTILE))
    long_body = df["plain_body"].str.len() > cap
    df["body_truncated"] = long_body
    df.loc[long_body, "plain_body"] = df.loc[long_body, "plain_body"].str.slice(0, cap)
    drop = empty | non_english | spam
    stats.update({"empty_removed": int(empty.sum()), "non_english_removed": int(non_english.sum()),
                  "spam_like_removed": int(spam.sum()), "long_body_cap_chars": cap,
                  "long_body_capped": int(long_body.sum()), "invalid_removed": int(drop.sum())})
    return df[~drop].copy(), stats


def class_balance(df):
    return {t: df[t].value_counts().sort_index().to_dict() for t in ("target_resolved_7d", "target_answered_7d")}


def clean_questions(frames, answers, users, collection_date, salt=None):
    """Run every step; return the cleaned frame and a stats dict for the before/after table."""
    q, s_merge = merge_questions(frames, answers, users, salt)
    q, s_time = convert_timestamps(q)
    q = add_text_features(q)
    q, s_age = add_account_age(q)
    q, s_target = add_targets(q, collection_date)
    q, s_invalid = flag_invalid(q)
    stats = {"merge": s_merge, "timestamps": s_time, "account_age": s_age, "targets": s_target,
             "invalid": s_invalid, "final_rows": len(q), "class_balance": class_balance(q)}
    return q, stats
