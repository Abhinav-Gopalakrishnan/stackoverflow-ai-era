"""Standalone script to collect weekly question counts for M1-06 (Issue #21).

Collects counts from /questions with filter=total for each study tag
plus site-wide total (tag="ALL") across exactly 400 7-day weeks from
2019-01-01 to 2026-08-31 UTC.

Outputs:
  data/processed/weekly_counts.csv (tag, week_start, count)
"""

import argparse
import logging
from datetime import datetime, timezone, date, timedelta
from pathlib import Path
import sys
import yaml
import pandas as pd

from src.collect import api_get, QuotaExhausted, _ROOT

logger = logging.getLogger("collect_weekly")

WEEKLY_COUNTS_PATH = _ROOT / "data" / "processed" / "weekly_counts.csv"
WINDOW_START = "2019-01-01"
WINDOW_END = "2026-08-31"

DEFAULT_TAGS = [
    "ALL",
    "python",
    "javascript",
    "java",
    "sql",
    "pandas",
    "reactjs",
    "android",
    "excel",
    "r",
    "docker",
    "powerbi",
    "fastapi",
    "openai-api",
]


def generate_weekly_windows(start_str: str = WINDOW_START, end_str: str = WINDOW_END) -> list[tuple[date, date]]:
    """Generate exactly 400 7-day windows spanning start_str to end_str inclusive."""
    start_d = date.fromisoformat(start_str)
    end_d = date.fromisoformat(end_str)
    windows = []
    curr = start_d
    while curr <= end_d:
        w_end = min(curr + timedelta(days=6), end_d)
        windows.append((curr, w_end))
        curr = curr + timedelta(days=7)
    return windows


def setup_logger() -> logging.Logger:
    log_dir = _ROOT / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "collect_weekly.log"

    logger = logging.getLogger("collect_weekly")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s UTC | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.Formatter.converter = lambda *args: datetime.now(timezone.utc).timetuple()

    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger


def collect_weekly_counts(tags: list[str], max_calls: int = 10000) -> None:
    log = setup_logger()
    windows = generate_weekly_windows()
    log.info("Loaded %d weekly windows from %s to %s", len(windows), WINDOW_START, WINDOW_END)

    WEEKLY_COUNTS_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Load existing weekly counts if present (resumable)
    existing_records: dict[tuple[str, str], int] = {}
    if WEEKLY_COUNTS_PATH.exists():
        try:
            df_exist = pd.read_csv(WEEKLY_COUNTS_PATH)
            for _, r in df_exist.iterrows():
                existing_records[(str(r["tag"]), str(r["week_start"]))] = int(r["count"])
            log.info("Loaded %d existing weekly count records", len(existing_records))
        except Exception as e:
            log.warning("Could not load existing weekly counts (%s); starting fresh", e)

    total_new_calls = 0

    try:
        for tag in tags:
            tag_label = tag
            log.info("=== Starting Weekly Counts for Tag: %s ===", tag_label)
            tag_new_calls = 0

            for idx, (start_d, end_d) in enumerate(windows, start=1):
                week_start_str = start_d.isoformat()
                key = (tag_label, week_start_str)

                if key in existing_records:
                    continue

                if total_new_calls >= max_calls:
                    log.warning("Reached max_calls cap of %d, stopping gracefully", max_calls)
                    return

                # Convert to UTC epoch seconds
                # Start: 00:00:00 UTC
                dt_s = datetime(start_d.year, start_d.month, start_d.day, 0, 0, 0, tzinfo=timezone.utc)
                # End: 23:59:59 UTC
                dt_e = datetime(end_d.year, end_d.month, end_d.day, 23, 59, 59, tzinfo=timezone.utc)
                s_ts = int(dt_s.timestamp())
                e_ts = int(dt_e.timestamp())

                params = {
                    "fromdate": s_ts,
                    "todate": e_ts,
                    "filter": "total",
                }
                if tag_label != "ALL":
                    params["tagged"] = tag_label

                resp = api_get("questions", params=params)
                count = resp.get("total", 0)
                existing_records[key] = count
                tag_new_calls += 1
                total_new_calls += 1

                # Periodically log progress every 50 weeks
                if idx % 50 == 0 or idx == len(windows):
                    log.info(
                        "[%s] Progress: %d/%d weeks (Week %s: %d questions)",
                        tag_label, idx, len(windows), week_start_str, count,
                    )

            log.info("Finished tag %s with %d new calls", tag_label, tag_new_calls)

            # Checkpoint after each tag
            save_records(existing_records)

    except QuotaExhausted as e:
        log.error("Quota floor reached: %s. Checkpoint saved. Run again to resume.", e)
    finally:
        save_records(existing_records)
        log.info("Total new API calls across this run: %d", total_new_calls)


def save_records(records: dict[tuple[str, str], int]) -> None:
    rows = []
    for (tag, week_start), count in records.items():
        rows.append({
            "tag": tag,
            "week_start": week_start,
            "count": count,
        })
    df = pd.DataFrame(rows).sort_values(by=["tag", "week_start"])
    df.to_csv(WEEKLY_COUNTS_PATH, index=False)


def main():
    parser = argparse.ArgumentParser(description="Collect weekly question counts for M1-06")
    parser.add_argument("--tags", nargs="+", default=DEFAULT_TAGS, help="List of tags to collect")
    parser.add_argument("--max-calls", type=int, default=10000, help="Max calls before stopping")
    args = parser.parse_args()

    collect_weekly_counts(args.tags, max_calls=args.max_calls)


if __name__ == "__main__":
    main()
