"""Charts for the full Review 1 deck (dark theme, transparent background).

Every function writes a PNG sized to the box it will be placed in (inches), so text in the
chart is the size it looks on the slide. Data comes from the committed files in ``data/processed``
and ``reports/review1/m5``, plus ``questions_clean_v1.parquet`` for a few team-level charts.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# palette of the reference deck: navy, burnt orange, teal, amber, grey, purple
TEXT, MUTED, GRID = "#1F2A37", "#4B5563", "#E5E7EB"
NAVY, ORANGE, TEAL, AMBER, GREY, PURPLE, SKY = "#1D4E89", "#C2410C", "#0F766E", "#B45309", "#9CA3AF", "#6D28D9", "#2A78D6"
GREEN, CORAL, BLUE = TEAL, ORANGE, SKY
DPI = 220
NOV_2022 = pd.Timestamp("2022-11-30")


def _fonts():
    from matplotlib import font_manager

    for d in ("/run/host/fonts/liberation", "/usr/share/fonts/liberation-fonts"):
        for f in Path(d).glob("LiberationSans-*.ttf"):
            font_manager.fontManager.addfont(str(f))


def _fig(w, h, **kw):
    _fonts()
    plt.rcParams.update({"font.family": "Liberation Sans", "text.color": TEXT, "axes.labelcolor": MUTED,
                         "xtick.color": MUTED, "ytick.color": MUTED, "axes.edgecolor": GRID,
                         "axes.facecolor": "none", "figure.facecolor": "none", "font.size": 11})
    fig, ax = plt.subplots(figsize=(w, h), **kw)
    return fig, ax


def _style(ax, grid="y"):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    if grid:
        ax.grid(axis=grid, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def _save(fig, path):
    fig.tight_layout(pad=0.6)
    fig.savefig(path, dpi=DPI, transparent=True)
    plt.close(fig)
    return str(path)


# ------------------------------------------------------------------ team-level
def weekly_volume(weekly_csv, path, size, events=True):
    d = pd.read_csv(weekly_csv, parse_dates=["week_start"])
    d = d[d.tag == "ALL"].sort_values("week_start")
    fig, ax = _fig(*size)
    ax.fill_between(d.week_start, d["count"] / 1000, color=NAVY, alpha=0.10)
    ax.plot(d.week_start, d["count"] / 1000, color=NAVY, linewidth=2.2)
    if events:
        top = ax.get_ylim()[1]
        for date, label, y, side in (("2022-06-21", "Copilot\navailable", 0.97, "left"),
                                     ("2022-11-30", "ChatGPT launch\n+ Stack Overflow ban", 0.70, "right"),
                                     ("2023-06-05", "Moderator\nstrike", 0.97, "right")):
            ax.axvline(pd.Timestamp(date), color=ORANGE, linestyle="--", linewidth=1.2)
            shift = pd.Timedelta(days=12) * (1 if side == "right" else -1)
            ax.text(pd.Timestamp(date) + shift, top * y, label, color=ORANGE, fontsize=10, va="top",
                    ha="left" if side == "right" else "right")
    ax.set_ylabel("Questions per week (thousands)")
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    _style(ax)
    return _save(fig, path)


def tag_bars(counts, path, size):
    items = sorted(counts.items(), key=lambda kv: kv[1])
    fig, ax = _fig(*size)
    bars = ax.barh([k for k, _ in items], [v for _, v in items],
                   color=[ORANGE if k == "openai-api" else NAVY for k, _ in items], height=0.68)
    for b, (_, v) in zip(bars, items):
        ax.text(v + max(counts.values()) * 0.012, b.get_y() + b.get_height() / 2, f"{v:,}", va="center", fontsize=10, color=TEXT)
    ax.set_xlim(0, max(counts.values()) * 1.18)
    ax.set_xticks([])
    _style(ax, grid=None)
    ax.spines["bottom"].set_visible(False)
    ax.spines["left"].set_color(GRID)
    return _save(fig, path)


def _monthly_weighted(monthly_tag_csv):
    t = pd.read_csv(monthly_tag_csv)
    t["date"] = pd.to_datetime(t["month"] + "-01")
    t = t[~t.low_sample]
    cols = ["resolved_rate_7d", "answered_rate_7d", "accepted_given_answered", "median_hours_to_first_answer",
            "median_hours_to_accept"]
    rows = []
    for date, g in t.groupby("date"):
        w = g["est_questions"].to_numpy()
        row = {"date": date}
        for c in cols:
            m = g[c].notna().to_numpy()
            row[c] = np.average(g[c].to_numpy()[m], weights=w[m]) if m.any() else np.nan
        rows.append(row)
    return pd.DataFrame(rows).sort_values("date")


def pre_post(monthly_tag_csv, cutoff="2022-11-01", post_from="2022-12-01"):
    """Averages before November 2022 and from December 2022, weighted by estimated questions.

    Same method as the EDA notebook: every non-low-sample tag-month is a row weighted by its
    estimated number of questions (November 2022 itself, the launch month, is left out of both).
    """
    t = pd.read_csv(monthly_tag_csv)
    t["date"] = pd.to_datetime(t["month"] + "-01")
    t = t[~t.low_sample]
    cols = ["resolved_rate_7d", "answered_rate_7d", "accepted_given_answered", "median_hours_to_first_answer",
            "median_hours_to_accept"]

    def wavg(frame, c):
        ok = frame[c].notna()
        return float(np.average(frame.loc[ok, c], weights=frame.loc[ok, "est_questions"]))

    pre, post = t[t.date < cutoff], t[t.date >= post_from]
    return {c: (wavg(pre, c), wavg(post, c)) for c in cols}


def rates_trend(monthly_tag_csv, path, size):
    m = _monthly_weighted(monthly_tag_csv)
    fig, ax = _fig(*size)
    for col, color, label in (("answered_rate_7d", SKY, "any answer in 7 days"),
                              ("resolved_rate_7d", NAVY, "accepted answer in 7 days"),
                              ("accepted_given_answered", AMBER, "accepted, given answered")):
        ax.plot(m.date, m[col] * 100, color=color, linewidth=1.0, alpha=0.35)
        ax.plot(m.date, m[col].rolling(6, min_periods=3, center=True).mean() * 100, color=color, linewidth=2.4, label=label)
    ax.axvline(NOV_2022, color=ORANGE, linestyle="--", linewidth=1.3)
    ax.text(NOV_2022 + pd.Timedelta(days=20), 83, "ChatGPT\nlaunch", color=ORANGE, fontsize=10, va="top")
    ax.set_ylim(15, 85)
    ax.set_ylabel("Share of questions (%)")
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.legend(loc="lower left", fontsize=9, frameon=False, labelcolor=TEXT, ncol=1)
    _style(ax)
    return _save(fig, path)


def hours_trend(monthly_tag_csv, path, size):
    m = _monthly_weighted(monthly_tag_csv)
    fig, ax = _fig(*size)
    for col, color, label in (("median_hours_to_first_answer", SKY, "to first answer"),
                              ("median_hours_to_accept", NAVY, "to accepted answer")):
        ax.plot(m.date, m[col], color=color, linewidth=1.0, alpha=0.35)
        ax.plot(m.date, m[col].rolling(6, min_periods=3, center=True).mean(), color=color, linewidth=2.4, label=label)
    ax.axvline(NOV_2022, color=ORANGE, linestyle="--", linewidth=1.3)
    ax.set_ylim(0, max(4.5, float(m[["median_hours_to_first_answer", "median_hours_to_accept"]].quantile(0.97).max()) * 1.1))
    ax.set_ylabel("Median hours")
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.legend(loc="upper left", fontsize=9, frameon=False, labelcolor=TEXT)
    _style(ax)
    return _save(fig, path)


def characteristics(parquet, path, size):
    q = pd.read_parquet(parquet, columns=["target_resolved_7d", "n_code_blocks", "has_error_text", "plain_body",
                                          "account_age_days", "missing_account_age"])
    y = q.target_resolved_7d
    body = q.plain_body.str.len()
    new = (q.account_age_days <= 7) & ~q.missing_account_age
    panels = [
        ("Code block in question", ["No", "Yes"], [y[q.n_code_blocks == 0].mean(), y[q.n_code_blocks > 0].mean()]),
        ("Error text in question", ["No", "Yes"], [y[~q.has_error_text].mean(), y[q.has_error_text].mean()]),
        ("Body length (characters)", ["<500", "500-1.5k", "1.5k-3k", "3k+"],
         [y[body < 500].mean(), y[(body >= 500) & (body < 1500)].mean(), y[(body >= 1500) & (body < 3000)].mean(), y[body >= 3000].mean()]),
        ("Asker account age", ["7+ days", "<7 days"], [y[~new].mean(), y[new].mean()]),
    ]
    fig, axes = _fig(*size, ncols=4, sharey=True)
    worse = [0, 1, None, 1]          # index of the bar that is worse in each panel
    for ax, (title, labels, vals), bad in zip(axes, panels, worse):
        colors = [NAVY] * len(vals)
        if bad is not None:
            colors[bad] = ORANGE
        else:
            colors[-1] = ORANGE
        bars = ax.bar(labels, [v * 100 for v in vals], color=colors, width=0.62)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v * 100 + 1.2, f"{v * 100:.0f}%", ha="center", fontsize=11, color=TEXT, fontweight="bold")
        ax.set_title(title, fontsize=11, color=TEXT, pad=8)
        ax.set_ylim(0, 58)
        ax.tick_params(axis="x", labelsize=9)
        _style(ax)
    axes[0].set_ylabel("Resolved in 7 days (%)")
    return _save(fig, path)


def baseline_bars(path, size, acc, majority_acc, pr_auc, no_skill_pr):
    fig, axes = _fig(*size, ncols=2)
    for ax, title, labels, vals, colors in (
        (axes[0], "Accuracy", ["Baseline model", "Always\n'unresolved'"], [acc, majority_acc], [ORANGE, GREY]),
        (axes[1], "PR-AUC", ["Baseline model", "No skill"], [pr_auc, no_skill_pr], [NAVY, GREY]),
    ):
        bars = ax.bar(labels, vals, color=colors, width=0.55)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.012, f"{v:.3f}", ha="center", fontsize=11, fontweight="bold", color=TEXT)
        ax.set_ylim(0, 0.8)
        ax.set_title(title, fontsize=11, color=TEXT, pad=8)
        ax.tick_params(axis="x", labelsize=9.5)
        _style(ax)
    return _save(fig, path)


# ------------------------------------------------------------------ Member 5
def rolling_chart(rolling_csv, path, size):
    r = pd.read_csv(rolling_csv, index_col=0)
    x = np.arange(len(r))
    cut = next(i for i, w in enumerate(r.index) if (int(w[:4]), 1 if w.endswith("H1") else 2) >= (2023, 1)) - 0.5
    fig, (a, b) = _fig(*size, ncols=2)
    a.plot(x, r.pr_auc, marker="o", color=NAVY, linewidth=2.2, label="PR-AUC")
    a.plot(x, r.positive_rate, marker="^", color=GREY, linewidth=1.8, linestyle=":", label="share resolved (no skill)")
    b.plot(x, r.roc_auc, marker="o", color=TEAL, linewidth=2.2, label="ROC-AUC")
    b.plot(x, r.pr_auc - r.positive_rate, marker="s", color=PURPLE, linewidth=2.2, label="PR-AUC minus no skill")
    for ax, title in ((a, "PR-AUC follows the share resolved"), (b, "Ranking quality stays flat")):
        ax.axvline(cut, color=ORANGE, linestyle="--", linewidth=1.3)
        ax.set_xticks(x)
        ax.set_xticklabels(r.index, rotation=60, fontsize=8.5)
        ax.set_title(title, fontsize=11, color=TEXT, pad=8)
        ax.legend(fontsize=8.5, frameon=False, labelcolor=TEXT, loc="lower left" if ax is a else "center right")
        _style(ax)
    a.set_ylim(0.2, 0.62)
    b.set_ylim(0.08, 0.72)
    return _save(fig, path)


def confusion(path, size, tn, fp, fn, tp):
    fig, ax = _fig(*size)
    m = np.array([[tn, fp], [fn, tp]])
    ax.imshow(m, cmap=matplotlib.colors.LinearSegmentedColormap.from_list("t", ["#EEF2F7", "#9DB7D5", NAVY]))
    for i in range(2):
        for j in range(2):
            ax.text(j, i, f"{m[i, j]:,}", ha="center", va="center", fontsize=16, fontweight="bold",
                    color="#FFFFFF" if m[i, j] > m.max() * 0.55 else TEXT)
    ax.set_xticks([0, 1], ["predicted\nunresolved", "predicted\nresolved"], fontsize=10)
    ax.set_yticks([0, 1], ["actually\nunresolved", "actually\nresolved"], fontsize=10)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)
    return _save(fig, path)


def reason_bars(items, path, size):
    """``items``: list of ``(label, count, kind)`` with kind ``"fp"`` (coral) or ``"fn"`` (teal)."""
    items = sorted(items, key=lambda t: t[1])
    fig, ax = _fig(*size)
    bars = ax.barh([t[0] for t in items], [t[1] for t in items], height=0.62,
                   color=[ORANGE if t[2] == "fp" else NAVY for t in items])
    for bar, t in zip(bars, items):
        ax.text(t[1] + 0.15, bar.get_y() + bar.get_height() / 2, str(t[1]), va="center", fontsize=11,
                fontweight="bold", color=TEXT)
    ax.set_xlim(0, max(t[1] for t in items) + 1.5)
    ax.set_xticks([])
    ax.tick_params(axis="y", labelsize=9.5)
    _style(ax, grid=None)
    ax.spines["bottom"].set_visible(False)
    return _save(fig, path)


def val_models_bars(path, size, models_pr, base):
    names, vals = zip(*models_pr)
    fig, ax = _fig(*size)
    colors = [GREY if n == "No skill" else (ORANGE if n == "XGBoost" else NAVY) for n in names]
    bars = ax.bar(names, vals, color=colors, width=0.6)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.006, f"{v:.3f}", ha="center", fontsize=10.5, fontweight="bold", color=TEXT)
    ax.set_ylim(0.25, 0.54)
    ax.set_ylabel("Validation PR-AUC")
    ax.tick_params(axis="x", labelsize=9)
    _style(ax)
    return _save(fig, path)


# ------------------------------------------------------------------ real-data charts used instead of drawn shapes
def class_balance(parquet, path, size):
    """Share of collected questions with each outcome, unweighted and weighted by ``sampling_weight``."""
    q = pd.read_parquet(parquet, columns=["target_resolved_7d", "target_answered_7d", "accepted_given_answered",
                                          "sampling_weight"])
    names = ["Accepted answer\nwithin 7 days", "Any answer\nwithin 7 days", "Accepted, given\nanswered"]
    cols = ["target_resolved_7d", "target_answered_7d", "accepted_given_answered"]
    plain, weighted = [], []
    for c in cols:
        ok = q[c].notna()
        plain.append(q.loc[ok, c].mean() * 100)
        weighted.append(np.average(q.loc[ok, c], weights=q.loc[ok, "sampling_weight"]) * 100)
    x = np.arange(3)
    fig, ax = _fig(*size)
    b1 = ax.bar(x - 0.19, plain, 0.36, color=NAVY, label="all collected questions")
    b2 = ax.bar(x + 0.19, weighted, 0.36, color=SKY, label="weighted by sampling weight")
    for bars in (b1, b2):
        for b in bars:
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 1.2, f"{b.get_height():.1f}%", ha="center",
                    fontsize=10.5, fontweight="bold", color=TEXT)
    ax.set_xticks(x, names)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Share of questions (%)")
    ax.legend(frameon=False, fontsize=10, loc="upper center", bbox_to_anchor=(0.5, 1.13), ncol=2)
    _style(ax)
    return _save(fig, path)


def split_timeline(parquet, path, size):
    """Monthly share resolved (weighted) with the train, validation and test periods shaded."""
    q = pd.read_parquet(parquet, columns=["created_at", "target_resolved_7d", "sampling_weight"])
    q["month"] = q.created_at.dt.tz_localize(None).dt.to_period("M").dt.to_timestamp()
    m = q.groupby("month").apply(lambda g: np.average(g.target_resolved_7d, weights=g.sampling_weight) * 100,
                                 include_groups=False)
    fig, ax = _fig(*size)
    spans = [("Train", "2019-01-01", "2025-01-01", NAVY, 0.07), ("Validation", "2025-01-01", "2025-07-01", SKY, 0.22),
             ("Test", "2025-07-01", "2026-08-01", ORANGE, 0.14)]
    for name, a, b, color, alpha in spans:
        ax.axvspan(pd.Timestamp(a), pd.Timestamp(b), color=color, alpha=alpha, linewidth=0)
        ax.text(pd.Timestamp(a) + (pd.Timestamp(b) - pd.Timestamp(a)) / 2, 53, name, ha="center", fontsize=11,
                fontweight="bold", color=color)
    ax.plot(m.index, m.values, color=NAVY, linewidth=2)
    ax.set_ylim(15, 58)
    ax.set_ylabel("Resolved within 7 days (%)")
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    _style(ax)
    return _save(fig, path)
