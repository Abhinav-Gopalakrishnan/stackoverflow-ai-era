"""Generate dark-themed time-series forecasting charts for Member 5's slides."""

import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = ROOT / "reports/review1/timeseries_summary.json"
OUT = ROOT / "reports/review1/deck_assets"

# Dark theme colors
BG = "#1A1D24"
CARD = "#131822"
MINT = "#1DE9B6"
ORANGE = "#FF9800"
WHITE = "#FFFFFF"
LIGHT = "#CFD8DC"
GRID = "#2A2F3A"
CYAN = "#00BCD4"
RED = "#EF5350"

plt.rcParams.update({
    "figure.facecolor": BG,
    "axes.facecolor": CARD,
    "axes.edgecolor": GRID,
    "axes.labelcolor": WHITE,
    "xtick.color": LIGHT,
    "ytick.color": LIGHT,
    "text.color": WHITE,
    "grid.color": GRID,
    "grid.alpha": 0.4,
    "font.family": "sans-serif",
    "font.size": 10,
})


def make_timeseries_forecast_dark():
    """Create 2x2 multi-panel forecast visualization with historical data, test tracking, and 2027 projection."""
    with open(SUMMARY_PATH, "r") as f:
        data = json.load(f)

    weekly_df = pd.read_csv(ROOT / "data/processed/weekly_counts.csv")
    weekly_df["week_start"] = pd.to_datetime(weekly_df["week_start"])

    fig, axes = plt.subplots(2, 2, figsize=(11.5, 7.0))
    fig.patch.set_facecolor(BG)

    panels = [
        ("ALL", "Site-Wide Questions (ALL)", axes[0, 0], MINT),
        ("python", "Python Ecosystem (python)", axes[0, 1], CYAN),
        ("javascript", "JavaScript Ecosystem (javascript)", axes[1, 0], ORANGE),
        ("openai-api", "AI Tooling (openai-api)", axes[1, 1], "#B388FF"),
    ]

    for tag, title_text, ax, color in panels:
        sub = weekly_df[weekly_df["tag"] == tag].sort_values("week_start").reset_index(drop=True)
        tag_data = data[tag]

        # Historical series
        hist_dates = sub["week_start"]
        hist_counts = sub["count"]

        ax.plot(hist_dates, hist_counts, color="#78909C", linewidth=1.2, alpha=0.7, label="Historical Data (2019-2026)")

        # Vertical line at ChatGPT release (2022-11-30)
        chatgpt_date = pd.Timestamp("2022-11-30")
        ax.axvline(chatgpt_date, color=RED, linestyle="--", linewidth=1.2, alpha=0.8)
        if ax == axes[0, 0]:
            ax.text(chatgpt_date + pd.Timedelta(days=15), hist_counts.max() * 0.85, "ChatGPT Launch\n(Nov 2022)",
                    color=RED, fontsize=8.5, fontweight="bold")

        # Test set period (2025 onwards)
        test_dates = [pd.to_datetime(d) for d in tag_data["test_dates"]]
        test_actuals = tag_data["test_actuals"]
        test_preds = tag_data["test_preds"]

        ax.plot(test_dates, test_actuals, color=WHITE, linewidth=1.6, label="2025-2026 Actuals")
        ax.plot(test_dates, test_preds, color=color, linewidth=2.0, linestyle="-", label="Model In-Sample Fit")

        # 26-week Future Projection
        fut_dates = [pd.to_datetime(d) for d in tag_data["future_dates"]]
        fut_preds = np.array(tag_data["future_preds"])
        std_err = tag_data["metrics"]["std_error"]

        ax.plot(fut_dates, fut_preds, color=color, linewidth=2.2, linestyle="--", label="2026-2027 Forecast")
        ax.fill_between(fut_dates, np.maximum(0, fut_preds - 1.96 * std_err), fut_preds + 1.96 * std_err,
                        color=color, alpha=0.2, label="95% Confidence Interval")

        acc = tag_data["metrics"]["forecast_accuracy"]
        r2 = tag_data["metrics"]["r2"]
        mape = tag_data["metrics"]["mape"]

        # Title & Metric badge
        ax.set_title(f"{title_text} — Accuracy: {acc:.1f}% (R² = {r2:.3f})", color=WHITE, fontsize=10.5, fontweight="bold", pad=8)
        ax.grid(True, linestyle=":", alpha=0.3)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

        if ax == axes[0, 0]:
            ax.legend(loc="upper right", fontsize=7.5, facecolor=CARD, edgecolor=GRID, framealpha=0.9)

    plt.tight_layout()
    OUT.mkdir(parents=True, exist_ok=True)
    out_file = OUT / "timeseries_forecast_dark.png"
    plt.savefig(out_file, dpi=160, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print(f"Generated {out_file}")


def make_timeseries_table_dark():
    """Create summary ranking card for time series metrics across top ecosystems."""
    res_df = pd.read_csv(ROOT / "reports/review1/timeseries_results.csv")
    res_df = res_df.sort_values("forecast_accuracy_pct", ascending=False).reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(8.0, 4.2))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(CARD)
    ax.axis("off")

    # Table columns
    col_labels = ["Ecosystem Tag", "Forecast Accuracy", "MAPE", "R² Score", "2027 Est. Weekly"]
    table_data = []
    for _, row in res_df.head(8).iterrows():
        table_data.append([
            row["tag"],
            f"{row['forecast_accuracy_pct']:.1f}%",
            f"{row['mape_pct']:.1f}%",
            f"{row['r2_score']:.3f}",
            f"{row['forecast_2027_weekly_mean']:.1f} /wk"
        ])

    table = ax.table(
        cellText=table_data,
        colLabels=col_labels,
        cellLoc="center",
        loc="center",
        bbox=[0.02, 0.05, 0.96, 0.90]
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9.5)

    # Style cells
    for (r, c), cell in table.get_celld().items():
        cell.set_edgecolor(GRID)
        if r == 0:
            cell.set_facecolor("#1E2430")
            cell.set_text_props(color=MINT, fontweight="bold")
            cell.set_height(0.12)
        else:
            cell.set_facecolor(CARD if r % 2 == 1 else "#171C26")
            if c == 1:
                cell.set_text_props(color=MINT, fontweight="bold")
            elif c == 0:
                cell.set_text_props(color=WHITE, fontweight="bold")
            else:
                cell.set_text_props(color=LIGHT)
            cell.set_height(0.10)

    out_file = OUT / "timeseries_table_dark.png"
    plt.savefig(out_file, dpi=160, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print(f"Generated {out_file}")


if __name__ == "__main__":
    make_timeseries_forecast_dark()
    make_timeseries_table_dark()
