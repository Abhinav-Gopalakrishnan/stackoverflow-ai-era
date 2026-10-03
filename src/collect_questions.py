"""src/collect_questions.py — M1-07: Question records with stratified sampling.

Executes stratified sampling and full collection across specified tags.
Default tag: python.

Sampling Rules:
- Before 2025-01: for each month with >= cutoff questions, shuffle weekdays and
  weekend days with deterministic RNG seeded from f"{seed}_{tag}_{month}", taking
  the first k of each (Option A: 1 weekday, 1 weekend day).
  Collect all questions created on each chosen day (00:00:00 to 23:59:59 UTC).
  sampling_weight = days_of_type_in_month / days_sampled.
- Low volume months (< cutoff) or from 2025-01 through 2026-08:
  collect all questions in full, sampling_weight = 1.0.

Outputs:
1. data/shared/questions_{tag}.parquet (untracked / git-ignored; contains raw owner_user_id)
2. data/processed/sampling_manifest.csv (tracked / committed; no raw IDs)
"""

from __future__ import annotations

import argparse
import calendar
import json
import logging
import os
import random
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml
from dotenv import load_dotenv

# Ensure repo root is on sys.path
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.collect import QuotaExhausted, api_get

load_dotenv()

# Load configuration
CONFIG_PATH = _ROOT / "config.yaml"
with open(CONFIG_PATH, encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)

STUDY_CFG = CONFIG.get("study", {})
SAMPLING_CFG = STUDY_CFG.get("sampling", {})

DEFAULT_SEED = SAMPLING_CFG.get("seed", 42)
DEFAULT_WEEKDAYS_SAMPLED = SAMPLING_CFG.get("weekdays_sampled", 1)
DEFAULT_WEEKEND_SAMPLED = SAMPLING_CFG.get("weekend_days_sampled", 1)
DEFAULT_CUTOFF = SAMPLING_CFG.get("full_cutoff", 300)
DEFAULT_FULL_FROM = SAMPLING_CFG.get("full_collection_from", "2025-01")
WINDOW_START = STUDY_CFG.get("window_start", "2019-01-01")
WINDOW_END = STUDY_CFG.get("window_end", "2026-08-31")

SHARED_DIR = _ROOT / "data" / "shared"
PROCESSED_DIR = _ROOT / "data" / "processed"
LOGS_DIR = _ROOT / "logs"

PARQUET_COLUMNS = [
    "question_id",
    "accepted_answer_id",
    "owner_user_id",
    "answer_count",
    "creation_date",
    "tags",
    "title",
    "body",
    "sampling_weight",
    "score",
    "view_count",
    "is_answered",
    "last_activity_date",
    "closed_date",
    "collected_tag",
    "month",
    "day_type",
]

MANIFEST_COLUMNS = [
    "tag",
    "month",
    "mode",
    "day_type",
    "sampled_date",
    "days_of_type_in_month",
    "days_sampled",
    "weight",
    "n_questions",
    "collection_date",
]


def setup_logger(tag: str) -> logging.Logger:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(f"collect_{tag}")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    # File handler
    log_file = LOGS_DIR / f"collect_{tag}.log"
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter("%(asctime)s UTC | %(levelname)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
    logger.addHandler(fh)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("%(asctime)s UTC | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
    logger.addHandler(ch)

    return logger


def generate_months(start_str: str, end_str: str) -> list[str]:
    start_y, start_m = int(start_str[:4]), int(start_str[5:7])
    end_y, end_m = int(end_str[:4]), int(end_str[5:7])
    months = []
    curr_y, curr_m = start_y, start_m
    while (curr_y < end_y) or (curr_y == end_y and curr_m <= end_m):
        months.append(f"{curr_y:04d}-{curr_m:02d}")
        curr_m += 1
        if curr_m > 12:
            curr_m = 1
            curr_y += 1
    return months


def get_month_day_distribution(year: int, month: int) -> tuple[list[date], list[date]]:
    _, num_days = calendar.monthrange(year, month)
    all_days = [date(year, month, d) for d in range(1, num_days + 1)]
    weekdays = sorted([d for d in all_days if d.weekday() < 5])
    weekend_days = sorted([d for d in all_days if d.weekday() >= 5])
    return weekdays, weekend_days


def parse_question_item(item: dict, weight: float, tag: str, month: str, day_type: str) -> dict:
    item = dict(item)
    owner = item.pop("owner", {}) or {}
    return {
        "question_id": item.get("question_id"),
        "accepted_answer_id": item.get("accepted_answer_id"),
        "owner_user_id": owner.get("user_id"),
        "answer_count": item.get("answer_count"),
        "creation_date": item.get("creation_date"),
        "tags": item.get("tags"),
        "title": item.get("title"),
        "body": item.get("body"),
        "sampling_weight": float(weight),
        "score": item.get("score"),
        "view_count": item.get("view_count"),
        "is_answered": item.get("is_answered"),
        "last_activity_date": item.get("last_activity_date"),
        "closed_date": item.get("closed_date"),
        "collected_tag": tag,
        "month": month,
        "day_type": day_type,
    }


def fetch_questions_range(tag: str, fromdate: int, todate: int) -> tuple[list[dict], int]:
    """Fetch questions within [fromdate, todate] paging 100 per call."""
    page = 1
    items: list[dict] = []
    calls = 0
    while True:
        params = {
            "tagged": tag,
            "fromdate": fromdate,
            "todate": todate,
            "sort": "creation",
            "order": "asc",
            "pagesize": 100,
        }
        resp = api_get("questions", params=params, page=page)
        calls += 1
        page_items = resp.get("items", [])
        items.extend(page_items)
        if not resp.get("has_more"):
            break
        page += 1
    return items, calls


def collect_tag(
    tag: str,
    seed: int = DEFAULT_SEED,
    weekdays_sampled: int = DEFAULT_WEEKDAYS_SAMPLED,
    weekend_days_sampled: int = DEFAULT_WEEKEND_SAMPLED,
    cutoff: int = DEFAULT_CUTOFF,
    full_from: str = DEFAULT_FULL_FROM,
    window_start: str = WINDOW_START,
    window_end: str = WINDOW_END,
) -> None:
    logger = setup_logger(tag)
    today_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    SHARED_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    parquet_path = SHARED_DIR / f"questions_{tag}.parquet"
    manifest_path = PROCESSED_DIR / "sampling_manifest.csv"

    # Load monthly counts to determine mode
    mc_path = PROCESSED_DIR / "monthly_counts.csv"
    if not mc_path.exists():
        raise FileNotFoundError(f"Missing {mc_path}. Run M1-05/06 first.")
    df_mc = pd.read_csv(mc_path)
    tag_mc = df_mc[df_mc["tag"] == tag].set_index("month")["count"].to_dict()

    months = generate_months(window_start, window_end)

    # Resume capability: load existing manifest and parquet if present
    existing_questions: list[dict] = []
    finished_months: set[str] = set()
    manifest_rows: list[dict] = []

    if manifest_path.exists():
        try:
            df_man_exist = pd.read_csv(manifest_path)
            # Only consider finished months for this tag
            tag_man = df_man_exist[df_man_exist["tag"] == tag]
            finished_months = set(tag_man["month"].unique())
            manifest_rows = df_man_exist[df_man_exist["tag"] != tag].to_dict(orient="records")
            manifest_rows.extend(tag_man.to_dict(orient="records"))
            logger.info("Loaded existing manifest with %d finished months for tag %s", len(finished_months), tag)
        except Exception as e:
            logger.warning("Could not read existing manifest (%s), starting fresh", e)

    if parquet_path.exists():
        try:
            df_exist = pd.read_parquet(parquet_path)
            existing_questions = df_exist.to_dict(orient="records")
            # If parquet has months not in finished_months or vice versa, sync
            pq_months = set(df_exist["month"].unique())
            finished_months = finished_months.intersection(pq_months)
            logger.info("Loaded %d existing question rows from %s", len(existing_questions), parquet_path.name)
        except Exception as e:
            logger.warning("Could not read existing parquet (%s), starting fresh", e)

    logger.info("=== Starting Collection for Tag: %s ===", tag)
    logger.info("Window: %s to %s (%d months)", window_start, window_end, len(months))
    logger.info("Sampling Seed: %d | Weekdays: %d | Weekend: %d | Cutoff: %d", seed, weekdays_sampled, weekend_days_sampled, cutoff)
    logger.info("Already completed months: %d | Remaining: %d", len(finished_months), len(months) - len(finished_months))

    total_calls = 0
    t0 = time.time()

    # Pre-calculate call estimate
    est_calls = 0
    for mo in months:
        if mo in finished_months:
            continue
        cnt = tag_mc.get(mo, 0)
        if mo >= full_from or cnt < cutoff:
            est_calls += max(1, int(np.ceil(cnt / 100)))
        else:
            # Approx 1/15 of monthly count
            est_calls += max(2, int(np.ceil((cnt / 15) / 100)))
    logger.info("Estimated API calls needed: ~%d calls", est_calls)

    try:
        for mo_idx, mo in enumerate(months, 1):
            if mo in finished_months:
                continue

            year = int(mo[:4])
            m = int(mo[5:7])
            weekdays, weekend_days = get_month_day_distribution(year, m)
            cnt = tag_mc.get(mo, 0)

            is_full = (mo >= full_from) or (cnt < cutoff)
            month_questions: list[dict] = []
            month_calls = 0

            if is_full:
                mode = "full"
                # Whole month range
                _, n_days = calendar.monthrange(year, m)
                dt_start = datetime(year, m, 1, 0, 0, 0, tzinfo=timezone.utc)
                dt_end = datetime(year, m, n_days, 23, 59, 59, tzinfo=timezone.utc)
                fromdate = int(dt_start.timestamp())
                todate = int(dt_end.timestamp())

                raw_items, calls = fetch_questions_range(tag, fromdate, todate)
                month_calls += calls
                total_calls += calls

                # Classify day_type based on creation_date
                wd_cnt = 0
                we_cnt = 0
                for item in raw_items:
                    c_date = item.get("creation_date", 0)
                    dt_q = datetime.fromtimestamp(c_date, tz=timezone.utc)
                    day_type = "weekday" if dt_q.weekday() < 5 else "weekend"
                    if day_type == "weekday":
                        wd_cnt += 1
                    else:
                        we_cnt += 1
                    month_questions.append(parse_question_item(item, 1.0, tag, mo, day_type))

                # Manifest entries for full month (split by day_type)
                manifest_rows.append({
                    "tag": tag,
                    "month": mo,
                    "mode": "full",
                    "day_type": "weekday",
                    "sampled_date": "all",
                    "days_of_type_in_month": len(weekdays),
                    "days_sampled": len(weekdays),
                    "weight": 1.0,
                    "n_questions": wd_cnt,
                    "collection_date": today_utc,
                })
                manifest_rows.append({
                    "tag": tag,
                    "month": mo,
                    "mode": "full",
                    "day_type": "weekend",
                    "sampled_date": "all",
                    "days_of_type_in_month": len(weekend_days),
                    "days_sampled": len(weekend_days),
                    "weight": 1.0,
                    "n_questions": we_cnt,
                    "collection_date": today_utc,
                })

                logger.info(
                    "[%d/%d] Month %s (full): %d questions (WD: %d, WE: %d) in %d calls",
                    mo_idx, len(months), mo, len(month_questions), wd_cnt, we_cnt, month_calls,
                )

            else:
                mode = "sampled"
                rng = random.Random(f"{seed}_{tag}_{mo}")
                shuf_wd = list(weekdays)
                rng.shuffle(shuf_wd)
                shuf_we = list(weekend_days)
                rng.shuffle(shuf_we)

                sel_wd = shuf_wd[:weekdays_sampled]
                sel_we = shuf_we[:weekend_days_sampled]

                weight_wd = len(weekdays) / len(sel_wd)
                weight_we = len(weekend_days) / len(sel_we)

                # Fetch chosen weekdays
                wd_cnt = 0
                for d in sel_wd:
                    dt_start = datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=timezone.utc)
                    dt_end = datetime(d.year, d.month, d.day, 23, 59, 59, tzinfo=timezone.utc)
                    raw_items, calls = fetch_questions_range(tag, int(dt_start.timestamp()), int(dt_end.timestamp()))
                    month_calls += calls
                    total_calls += calls
                    wd_cnt += len(raw_items)
                    for item in raw_items:
                        month_questions.append(parse_question_item(item, weight_wd, tag, mo, "weekday"))

                    manifest_rows.append({
                        "tag": tag,
                        "month": mo,
                        "mode": "sampled",
                        "day_type": "weekday",
                        "sampled_date": d.isoformat(),
                        "days_of_type_in_month": len(weekdays),
                        "days_sampled": 1,
                        "weight": float(weight_wd),
                        "n_questions": len(raw_items),
                        "collection_date": today_utc,
                    })

                # Fetch chosen weekend days
                we_cnt = 0
                for d in sel_we:
                    dt_start = datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=timezone.utc)
                    dt_end = datetime(d.year, d.month, d.day, 23, 59, 59, tzinfo=timezone.utc)
                    raw_items, calls = fetch_questions_range(tag, int(dt_start.timestamp()), int(dt_end.timestamp()))
                    month_calls += calls
                    total_calls += calls
                    we_cnt += len(raw_items)
                    for item in raw_items:
                        month_questions.append(parse_question_item(item, weight_we, tag, mo, "weekend"))

                    manifest_rows.append({
                        "tag": tag,
                        "month": mo,
                        "mode": "sampled",
                        "day_type": "weekend",
                        "sampled_date": d.isoformat(),
                        "days_of_type_in_month": len(weekend_days),
                        "days_sampled": 1,
                        "weight": float(weight_we),
                        "n_questions": len(raw_items),
                        "collection_date": today_utc,
                    })

                logger.info(
                    "[%d/%d] Month %s (sampled): %d questions (WD: %d, WE: %d) in %d calls",
                    mo_idx, len(months), mo, len(month_questions), wd_cnt, we_cnt, month_calls,
                )

            # Append and checkpoint
            existing_questions.extend(month_questions)
            finished_months.add(mo)

            # Deduplicate by question_id and save checkpoint
            df_all = pd.DataFrame(existing_questions).drop_duplicates(subset=["question_id"], keep="first")
            for col in PARQUET_COLUMNS:
                if col not in df_all.columns:
                    df_all[col] = np.nan
            df_all = df_all[PARQUET_COLUMNS]

            # Enforce clean dtypes
            df_all["question_id"] = df_all["question_id"].astype("int64")
            df_all["accepted_answer_id"] = pd.to_numeric(df_all["accepted_answer_id"], errors="coerce")
            df_all["owner_user_id"] = pd.to_numeric(df_all["owner_user_id"], errors="coerce")
            df_all["answer_count"] = df_all["answer_count"].fillna(0).astype("int64")
            df_all["creation_date"] = df_all["creation_date"].astype("int64")
            df_all["sampling_weight"] = df_all["sampling_weight"].astype("float64")
            df_all["score"] = df_all["score"].fillna(0).astype("int64")
            df_all["view_count"] = df_all["view_count"].fillna(0).astype("int64")
            df_all["is_answered"] = df_all["is_answered"].fillna(False).astype("bool")
            df_all["last_activity_date"] = df_all["last_activity_date"].fillna(0).astype("int64")
            df_all["closed_date"] = pd.to_numeric(df_all["closed_date"], errors="coerce")
            df_all["collected_tag"] = df_all["collected_tag"].astype("str")
            df_all["month"] = df_all["month"].astype("str")
            df_all["day_type"] = df_all["day_type"].astype("str")

            df_all.to_parquet(parquet_path, index=False)

            df_man = pd.DataFrame(manifest_rows)[MANIFEST_COLUMNS]
            df_man.to_csv(manifest_path, index=False)

    except QuotaExhausted as e:
        logger.error("[STOP] QuotaExhausted: %s. Checkpoint safely preserved at %d finished months.", e, len(finished_months))
        logger.info("Saved %d total rows in %s.", len(existing_questions), parquet_path.name)
        return

    runtime = time.time() - t0
    logger.info("=== Collection Complete for Tag: %s ===", tag)
    logger.info("Total rows: %d | Total new API calls: %d | Runtime: %.1fs", len(existing_questions), total_calls, runtime)


def run_checks(tag: str) -> None:
    logger = setup_logger(tag)
    parquet_path = SHARED_DIR / f"questions_{tag}.parquet"
    manifest_path = PROCESSED_DIR / "sampling_manifest.csv"
    mc_path = PROCESSED_DIR / "monthly_counts.csv"

    if not parquet_path.exists():
        logger.error("Parquet file %s does not exist", parquet_path)
        return

    df = pd.read_parquet(parquet_path)
    df_man = pd.read_csv(manifest_path)
    df_mc = pd.read_csv(mc_path)
    tag_mc = df_mc[df_mc["tag"] == tag]

    print("\n" + "=" * 70)
    print(f"VERIFICATION CHECKS FOR TAG: {tag}")
    print("=" * 70)

    # 1. Duplicates & Null counts
    dupes = df.duplicated(subset=["question_id"]).sum()
    print(f"\n1. Integrity & Schema:")
    print(f"   Total rows: {len(df):,}")
    print(f"   Duplicate question_ids: {dupes}")
    print(f"   Creation date range: {df['creation_date'].min()} to {df['creation_date'].max()}")
    print(f"   (UTC Dates: {datetime.fromtimestamp(df['creation_date'].min(), tz=timezone.utc).isoformat()} to {datetime.fromtimestamp(df['creation_date'].max(), tz=timezone.utc).isoformat()})")
    print(f"   All weights > 0: {(df['sampling_weight'] > 0).all()} (Min: {df['sampling_weight'].min():.2f}, Max: {df['sampling_weight'].max():.2f})")
    print(f"\n   Nulls per column:")
    for col in df.columns:
        null_count = df[col].isna().sum()
        pct = (null_count / len(df)) * 100
        print(f"     {col:20s}: {null_count:6d} ({pct:5.1f}%)")

    # 2. Rows per year
    df["year"] = df["creation_date"].apply(lambda t: datetime.fromtimestamp(t, tz=timezone.utc).year)
    print(f"\n2. Rows and Weight Sum per Year:")
    yearly = df.groupby("year").agg(
        collected_rows=("question_id", "count"),
        weight_sum=("sampling_weight", "sum"),
        weekday_rows=("day_type", lambda s: (s == "weekday").sum()),
        weekend_rows=("day_type", lambda s: (s == "weekend").sum()),
    ).reset_index()

    tag_mc["year"] = tag_mc["month"].apply(lambda m: int(m[:4]))
    yearly_mc = tag_mc.groupby("year")["count"].sum().to_dict()

    yearly["total_population"] = yearly["year"].map(yearly_mc)
    yearly["ratio_weight_to_pop"] = yearly["weight_sum"] / yearly["total_population"]
    yearly["weekday_pct"] = (yearly["weekday_rows"] / yearly["collected_rows"]) * 100
    yearly["weekend_pct"] = (yearly["weekend_rows"] / yearly["collected_rows"]) * 100

    print(f"   {'Year':<6} {'Collected':<11} {'Weight Sum':<13} {'Population':<13} {'Weight/Pop':<12} {'WD %':<8} {'WE %':<8}")
    print("   " + "-" * 72)
    for _, r in yearly.iterrows():
        y = int(r["year"])
        coll = int(r["collected_rows"])
        ws = r["weight_sum"]
        pop = int(r["total_population"])
        ratio = r["ratio_weight_to_pop"]
        wd_pct = r["weekday_pct"]
        we_pct = r["weekend_pct"]
        flag = " *" if (y < 2025 and not (0.90 <= ratio <= 1.10)) else ""
        print(f"   {y:<6} {coll:<11,d} {ws:<13,.1f} {pop:<13,d} {ratio:<12.4f} {wd_pct:<8.1f} {we_pct:<8.1f}{flag}")

    # 3. Fully collected vs monthly_counts.csv
    post2025_df = df[df["month"] >= "2025-01"]
    post2025_mc = tag_mc[tag_mc["month"] >= "2025-01"]["count"].sum()
    print(f"\n3. Fully collected period (2025-01 to 2026-08):")
    print(f"   Collected rows: {len(post2025_df):,}")
    print(f"   Monthly counts total: {post2025_mc:,}")
    print(f"   Difference: {len(post2025_df) - post2025_mc} (expected slight divergence from deletion/post-timing)")

    print("\n" + "=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Collect stratified questions for target tags.")
    parser.add_argument("--tags", nargs="+", default=["python"], help="Tags to collect (default: python)")
    parser.add_argument("--check-only", action="store_true", help="Only run validation checks on existing data")
    args = parser.parse_args()

    for tag in args.tags:
        if not args.check_only:
            collect_tag(tag)
        run_checks(tag)


if __name__ == "__main__":
    main()
