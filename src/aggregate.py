"""Monthly weighted tables per tag for EDA (M2-13).

Each sampled question stands for `sampling_weight` real questions, so every rate and
median below is weighted. A question collected under several selected tags counts in
each of those tags' tables. Weekly volume is NOT computed here: it comes from the
complete counts (Member 1), because sampled days cannot support weekly rates.
"""
from pathlib import Path

import numpy as np
import pandas as pd

MIN_SAMPLED = 30
ROOT = Path(__file__).resolve().parents[1]


def weighted_median(values, weights):
    v = np.asarray(values, dtype=float)
    w = np.asarray(weights, dtype=float)
    keep = ~np.isnan(v)
    v, w = v[keep], w[keep]
    if len(v) == 0:
        return np.nan
    order = np.argsort(v, kind="stable")
    v, w = v[order], w[order]
    cum = np.cumsum(w)
    return float(v[np.searchsorted(cum, cum[-1] / 2)])


def weighted_mean(values, weights):
    v = np.asarray(values, dtype=float)
    w = np.asarray(weights, dtype=float)
    keep = ~np.isnan(v)
    return float(np.average(v[keep], weights=w[keep])) if keep.any() and w[keep].sum() > 0 else np.nan


def _summarise(g):
    w = g["sampling_weight"]
    return pd.Series({
        "n_sampled": len(g),
        "est_questions": float(w.sum()),
        "resolved_rate_7d": weighted_mean(g["target_resolved_7d"], w),
        "answered_rate_7d": weighted_mean(g["target_answered_7d"], w),
        "accepted_given_answered": weighted_mean(g["accepted_given_answered"], w),
        "median_hours_to_accept": weighted_median(g["hours_to_accept"], w),
        "median_hours_to_first_answer": weighted_median(g["hours_to_first_answer"], w),
    })


def monthly_tag_tables(df, min_sampled=MIN_SAMPLED):
    """One row per (tag, month). `low_sample` flags months with fewer than min_sampled questions."""
    d = df.explode("collected_tags").rename(columns={"collected_tags": "tag"})
    d["month"] = d["created_at"].dt.strftime("%Y-%m")
    out = d.groupby(["tag", "month"]).apply(_summarise, include_groups=False).reset_index()
    out["n_sampled"] = out["n_sampled"].astype(int)
    out["low_sample"] = out["n_sampled"] < min_sampled
    return out


def main():
    src = ROOT / "data" / "processed" / "questions_clean_v1.parquet"
    out = ROOT / "data" / "processed" / "monthly_tag_tables.csv"
    table = monthly_tag_tables(pd.read_parquet(src))
    table.to_csv(out, index=False)
    print(f"{out.name}: {len(table)} tag-months, {int(table.low_sample.sum())} flagged low_sample")


if __name__ == "__main__":
    main()
