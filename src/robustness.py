"""Sampling robustness checks (M2-14).

Before 2025 each tag-month is a sample of one weekday and one weekend day, so monthly
estimates carry sampling noise. These helpers measure it three ways: estimated vs
complete monthly volume, weighted vs unweighted rates, and the same rates under a
second random seed.
"""
import numpy as np
import pandas as pd

FULL_FROM = "2025-01"


def _by_tag(v1):
    d = v1.explode("collected_tags").rename(columns={"collected_tags": "tag"})
    d["month"] = d["created_at"].dt.strftime("%Y-%m")
    return d


def volume_check(v1, complete):
    """Estimated (sum of sampling weights) vs complete monthly counts, per tag-month."""
    est = _by_tag(v1).groupby(["tag", "month"])["sampling_weight"].sum().rename("estimated").reset_index()
    out = est.merge(complete.rename(columns={"count": "complete"}), on=["tag", "month"], how="outer")
    out["pct_err"] = (out["estimated"] / out["complete"] - 1) * 100
    return out


def volume_summary(check):
    sampled = check[(check["month"] < FULL_FROM) & check["estimated"].notna() & (check["complete"] > 0)]
    full = check[(check["month"] >= FULL_FROM) & check["estimated"].notna() & (check["complete"] > 0)]
    err = sampled["pct_err"].abs()
    return {
        "sampled_tag_months": len(sampled), "sampled_mean_abs_err_pct": err.mean(), "sampled_median_abs_err_pct": err.median(),
        "sampled_p90_abs_err_pct": err.quantile(0.9), "sampled_max_abs_err_pct": err.max(),
        "full_tag_months": len(full), "full_mean_abs_err_pct": full["pct_err"].abs().mean(),
        "full_max_abs_err_pct": full["pct_err"].abs().max(),
    }


def yearly_volume_bias(check):
    y = check.assign(year=check["month"].str[:4]).groupby("year")[["estimated", "complete"]].sum()
    y["pct_err"] = (y["estimated"] / y["complete"] - 1) * 100
    return y


def weighted_vs_unweighted(v1, by="year"):
    d = _by_tag(v1)
    d["year"] = d["created_at"].dt.year

    def rates(g):
        w = g["sampling_weight"]
        return pd.Series({
            "unweighted_resolved": g["target_resolved_7d"].mean(),
            "weighted_resolved": np.average(g["target_resolved_7d"], weights=w),
            "unweighted_answered": g["target_answered_7d"].mean(),
            "weighted_answered": np.average(g["target_answered_7d"], weights=w),
        })

    out = d.groupby(by).apply(rates, include_groups=False)
    out["resolved_diff_pp"] = (out["weighted_resolved"] - out["unweighted_resolved"]) * 100
    out["answered_diff_pp"] = (out["weighted_answered"] - out["unweighted_answered"]) * 100
    return out


def weighted_balance(df, sampled_only=True):
    """Weighted share of both targets; sampled_only keeps months before 2025 (the sampled part)."""
    d = df[df["month"] < FULL_FROM] if sampled_only else df
    w = d["sampling_weight"]
    return {"rows": len(d), "est_questions": float(w.sum()),
            "resolved_7d": float(np.average(d["target_resolved_7d"], weights=w)),
            "answered_7d": float(np.average(d["target_answered_7d"], weights=w))}
