"""Generate authentic, publication-grade white-background matplotlib charts for Review 1 slides.

Outputs to reports/review1/deck_assets/:
1. timeseries_forecast_white.png - 4-panel time series demand forecasting with 2027 projections & 95% CI
2. confusion_white.png           - Test set confusion matrix (N=16,695) with counts and percentages
3. shap_bar_white.png            - Top 10 SHAP feature importances with descriptive labels
4. rolling_white.png             - 11-window rolling evaluation showing ChatGPT temporal invariance
5. error_analysis_white.png      - Diagnostic breakdown of 30 high-confidence misclassifications
6. split_white.png               - Chronological train/val/test timeline with resolution rate trend
7. model_comparison_white.png    - PR-AUC and ROC-AUC benchmark comparison across candidate models
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
M5 = ROOT / "reports" / "review1" / "m5"
OUT = ROOT / "reports" / "review1" / "deck_assets"
SUMMARY_PATH = ROOT / "reports" / "review1" / "timeseries_summary.json"
WEEKLY_CSV = ROOT / "data" / "processed" / "weekly_counts.csv"
PARQUET = ROOT / "data" / "processed" / "questions_clean_v1.parquet"

# Academic & Publication Palette (White background)
BG_WHITE = "#FFFFFF"
TEXT_DARK = "#1F2937"       # Charcoal / deep slate for crisp readability
TEXT_MUTED = "#4B5563"      # Secondary gray
GRID_COLOR = "#E5E7EB"      # Subtle hairline grid
LINE_DARK = "#1D4E89"       # Deep academic navy
ACCENT_BLUE = "#0284C7"     # Sky blue
ACCENT_ORANGE = "#D97706"   # Burnt amber
ACCENT_GREEN = "#059669"    # Emerald / teal
ACCENT_RED = "#DC2626"      # Crimson for events
ACCENT_PURPLE = "#7C3AED"   # Deep violet

plt.rcParams.update({
    "figure.facecolor": BG_WHITE,
    "axes.facecolor": BG_WHITE,
    "axes.edgecolor": "#D1D5DB",
    "axes.labelcolor": TEXT_DARK,
    "xtick.color": TEXT_DARK,
    "ytick.color": TEXT_DARK,
    "text.color": TEXT_DARK,
    "grid.color": GRID_COLOR,
    "grid.alpha": 0.8,
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.titleweight": "bold",
    "axes.labelsize": 10,
    "figure.titlesize": 13,
    "figure.titleweight": "bold",
})


def make_timeseries_forecast_white():
    """Create 2x2 multi-panel forecast visualization with historical data, test tracking, and 2027 projection."""
    with open(SUMMARY_PATH, "r") as f:
        data = json.load(f)

    weekly_df = pd.read_csv(WEEKLY_CSV)
    weekly_df["week_start"] = pd.to_datetime(weekly_df["week_start"])

    fig, axes = plt.subplots(2, 2, figsize=(11.5, 7.2), dpi=220)
    fig.patch.set_facecolor(BG_WHITE)

    panels = [
        ("ALL", "Site-Wide (ALL): 91.7% Acc | R²=0.976 | MAPE=8.3%", axes[0, 0], LINE_DARK, ACCENT_BLUE),
        ("python", "Python: 87.7% Acc | R²=0.969 | MAPE=12.3%", axes[0, 1], "#0F766E", "#0D9488"),
        ("javascript", "JavaScript: 81.5% Acc | R²=0.954 | MAPE=18.5%", axes[1, 0], "#B45309", "#D97706"),
        ("openai-api", "OpenAI API: 82.4% Acc | R²=0.521 | MAPE=17.6%", axes[1, 1], ACCENT_PURPLE, "#8B5CF6"),
    ]

    for tag, title_text, ax, primary_color, fit_color in panels:
        sub = weekly_df[weekly_df["tag"] == tag].sort_values("week_start").reset_index(drop=True)
        tag_data = data[tag]

        # Historical series
        hist_dates = sub["week_start"]
        hist_counts = sub["count"]

        ax.plot(hist_dates, hist_counts, color="#9CA3AF", linewidth=1.2, alpha=0.85, label="Historical Actuals (2019-2026)")

        # Vertical line at ChatGPT release (2022-11-30)
        chatgpt_date = pd.Timestamp("2022-11-30")
        ax.axvline(chatgpt_date, color=ACCENT_RED, linestyle="--", linewidth=1.3, alpha=0.85)
        if ax == axes[0, 0]:
            ax.text(chatgpt_date - pd.Timedelta(days=25), hist_counts.max() * 0.70, "ChatGPT Launch\n(Nov 2022)",
                    color=ACCENT_RED, fontsize=8.0, fontweight="bold", ha="right")

        # Test set period (2025 onwards)
        test_dates = [pd.to_datetime(d) for d in tag_data["test_dates"]]
        test_actuals = tag_data["test_actuals"]
        test_preds = tag_data["test_preds"]

        ax.plot(test_dates, test_actuals, color=TEXT_DARK, linewidth=1.6, label="Test Set Actuals")
        ax.plot(test_dates, test_preds, color=primary_color, linewidth=2.0, linestyle="-", label="Holt Model In-Sample Fit")

        # 26-week Future Projection
        fut_dates = [pd.to_datetime(d) for d in tag_data["future_dates"]]
        fut_preds = np.array(tag_data["future_preds"])
        std_err = tag_data["metrics"]["std_error"]

        ax.plot(fut_dates, fut_preds, color=ACCENT_ORANGE, linewidth=2.2, linestyle="--", label="2026-2027 Damped Forecast")
        ax.fill_between(fut_dates, np.maximum(0, fut_preds - 1.96 * std_err), fut_preds + 1.96 * std_err,
                        color=ACCENT_ORANGE, alpha=0.18, label="95% Confidence Interval")

        # Clean title & metric summary
        ax.set_title(title_text, color=TEXT_DARK, fontsize=9.8, fontweight="bold", pad=7)
        ax.grid(True, linestyle=":", alpha=0.6, color=GRID_COLOR)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.set_ylabel("Questions / Week", fontsize=9, color=TEXT_MUTED)

        for s in ("top", "right"):
            ax.spines[s].set_visible(False)

        if ax == axes[0, 0]:
            ax.legend(loc="upper right", fontsize=7.2, frameon=True, facecolor=BG_WHITE, edgecolor="#D1D5DB", framealpha=0.95)

    fig.suptitle("Demand Forecasting Across Developer Ecosystems (Holt's Damped Trend Model)",
                 fontsize=12.0, fontweight="bold", color=TEXT_DARK, y=0.98)
    fig.subplots_adjust(top=0.91, bottom=0.08, left=0.07, right=0.98, hspace=0.28, wspace=0.22)
    out_file = OUT / "timeseries_forecast_white.png"
    fig.savefig(out_file, dpi=200, bbox_inches="tight", facecolor=BG_WHITE)
    plt.close(fig)
    print(f"  ✓ {out_file.name}")


def make_confusion_white():
    """Create clean, authentic confusion matrix with counts, percentages, and marginal stats."""
    tn, fp, fn, tp = 5020, 6719, 1134, 3822
    total = tn + fp + fn + tp
    matrix = np.array([[tn, fp], [fn, tp]])

    fig, ax = plt.subplots(figsize=(5.5, 4.4), dpi=200)
    fig.patch.set_facecolor(BG_WHITE)

    # Clean Blues colormap
    cax = ax.imshow(matrix, cmap="Blues", interpolation="nearest", aspect="auto")

    # Annotate cells
    labels = [
        [f"True Negative\n{tn:,}\n({tn/total*100:.1f}%)", f"False Positive\n{fp:,}\n({fp/total*100:.1f}%)"],
        [f"False Negative\n{fn:,}\n({fn/total*100:.1f}%)", f"True Positive\n{tp:,}\n({tp/total*100:.1f}%)"]
    ]

    for i in range(2):
        for j in range(2):
            val = matrix[i, j]
            color = "white" if val > matrix.max() * 0.55 else TEXT_DARK
            ax.text(j, i, labels[i][j], ha="center", va="center",
                    fontsize=10.5, fontweight="bold", color=color)

    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(["Predicted Unresolved", "Predicted Resolved"], fontsize=10, fontweight="bold")
    ax.set_yticklabels(["Actual Unresolved", "Actual Resolved"], fontsize=10, fontweight="bold")
    ax.set_xlabel("Predicted Class (Tuned Threshold = 0.367)", fontsize=10.5, fontweight="bold", color=TEXT_DARK, labelpad=8)
    ax.set_ylabel("Actual Ground Truth", fontsize=10.5, fontweight="bold", color=TEXT_DARK, labelpad=8)

    ax.set_title(f"Test Set Confusion Matrix (N = {total:,})\nRecall: 77.1% | Precision: 36.3% | Accuracy: 53.0%",
                 fontsize=11, fontweight="bold", color=TEXT_DARK, pad=12)

    for s in ax.spines.values():
        s.set_edgecolor("#9CA3AF")

    fig.tight_layout()
    out_file = OUT / "confusion_white.png"
    fig.savefig(out_file, dpi=200, bbox_inches="tight", facecolor=BG_WHITE)
    plt.close(fig)
    print(f"  ✓ {out_file.name}")


def make_shap_bar_white():
    """Horizontal bar chart of top 10 SHAP features with readable labels."""
    df = pd.read_csv(M5 / "shap_top.csv", index_col=0)
    df = df.sort_values("mean_abs_shap", ascending=True)

    fig, ax = plt.subplots(figsize=(7.2, 4.4), dpi=200)
    fig.patch.set_facecolor(BG_WHITE)

    name_map = {
        "lagged_tag_volume": "Tag Volume (4-wk lag)",
        "account_age_days": "Account Age (days)",
        "code_ratio": "Code Block Ratio",
        "n_code_blocks": "# Code Blocks",
        "title_tfidf_svd_5": "Title Text (SVD-5)",
        "body_length": "Body Length (chars)",
        "title_tfidf_svd_3": "Title Text (SVD-3)",
        "title_tfidf_svd_2": "Title Text (SVD-2)",
        "title_tfidf_svd_28": "Title Text (SVD-28)",
        "title_tfidf_svd_20": "Title Text (SVD-20)",
    }
    labels = [name_map.get(n, n) for n in df.index]

    colors = [LINE_DARK if v >= 0.09 else ACCENT_BLUE for v in df["mean_abs_shap"]]
    bars = ax.barh(labels, df["mean_abs_shap"], color=colors, height=0.62, edgecolor="none")

    for bar, val in zip(bars, df["mean_abs_shap"]):
        ax.text(val + 0.003, bar.get_y() + bar.get_height() / 2,
                f"{val:.3f}", va="center", ha="left", color=TEXT_DARK, fontsize=9.5, fontweight="bold")

    ax.set_xlabel("Mean |SHAP Value| (Impact on 7-Day Resolution Prediction)", fontsize=10, fontweight="bold", color=TEXT_DARK)
    ax.set_title("Top 10 Feature Importances (TreeSHAP on XGBoost)", fontsize=11.5, fontweight="bold", color=TEXT_DARK, pad=10)
    ax.set_xlim(0, max(df["mean_abs_shap"]) * 1.18)
    ax.grid(axis="x", alpha=0.6, color=GRID_COLOR, linestyle=":")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

    fig.tight_layout()
    out_file = OUT / "shap_bar_white.png"
    fig.savefig(out_file, dpi=200, bbox_inches="tight", facecolor=BG_WHITE)
    plt.close(fig)
    print(f"  ✓ {out_file.name}")


def make_rolling_white():
    """White-themed rolling-origin evaluation chart showing temporal stability over 11 half-year windows."""
    df = pd.read_csv(M5 / "rolling_origin.csv")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.6, 4.3), dpi=200)
    fig.patch.set_facecolor(BG_WHITE)

    # Subplot 1: PR-AUC, F1, and Base Rate
    ax1.plot(df["window"], df["pr_auc"], marker="o", color=LINE_DARK, linewidth=2.0, markersize=5.5, label="PR-AUC", zorder=5)
    ax1.plot(df["window"], df["f1"], marker="s", color=ACCENT_ORANGE, linewidth=2.0, markersize=5.5, label="F1 Score", zorder=5)
    ax1.plot(df["window"], df["positive_rate"], marker="^", color="#6B7280", linewidth=1.5, markersize=5, linestyle=":", label="Base Rate (Share Resolved)", zorder=4)

    # Nov 2022 vertical line
    ax1.axvline(x=3.5, color=ACCENT_RED, linestyle="--", linewidth=1.3, alpha=0.85, label="ChatGPT Launch")

    ax1.set_ylabel("Score / Share", fontsize=10, fontweight="bold", color=TEXT_DARK)
    ax1.set_title("Performance Across 11 Half-Year Windows", fontsize=11, fontweight="bold", pad=8)
    ax1.legend(fontsize=8, loc="upper right", frameon=True, facecolor=BG_WHITE, edgecolor="#D1D5DB")
    ax1.set_ylim(0.18, 0.68)
    ax1.grid(axis="y", alpha=0.6, color=GRID_COLOR, linestyle=":")
    for s in ("top", "right"):
        ax1.spines[s].set_visible(False)
    ax1.tick_params(axis="x", rotation=45, labelsize=8)

    # Subplot 2: Invariance of Ranking (ROC-AUC) vs PR Lift
    pr_lift = df["pr_auc"] - df["positive_rate"]
    ax2.plot(df["window"], df["roc_auc"], marker="o", color=ACCENT_GREEN, linewidth=2.0, markersize=5.5, label="ROC-AUC (Discriminative Power)", zorder=5)
    ax2.plot(df["window"], pr_lift, marker="s", color=ACCENT_PURPLE, linewidth=2.0, markersize=5.5, label="PR-AUC Lift over Base Rate", zorder=5)
    ax2.axvline(x=3.5, color=ACCENT_RED, linestyle="--", linewidth=1.3, alpha=0.85, label="ChatGPT Launch")

    ax2.set_ylabel("Discriminative Metric", fontsize=10, fontweight="bold", color=TEXT_DARK)
    ax2.set_title("Ranking Invariance Across AI Shock", fontsize=11, fontweight="bold", pad=8)
    ax2.legend(fontsize=8, loc="center right", frameon=True, facecolor=BG_WHITE, edgecolor="#D1D5DB")
    ax2.set_ylim(0.08, 0.74)
    ax2.grid(axis="y", alpha=0.6, color=GRID_COLOR, linestyle=":")
    for s in ("top", "right"):
        ax2.spines[s].set_visible(False)
    ax2.tick_params(axis="x", rotation=45, labelsize=8)

    fig.suptitle("Temporal Robustness: 5-Year Rolling-Origin Cross-Validation (2021-H1 to 2026-H1)",
                 fontsize=12, fontweight="bold", color=TEXT_DARK, y=0.99)
    fig.tight_layout()
    out_file = OUT / "rolling_white.png"
    fig.savefig(out_file, dpi=200, bbox_inches="tight", facecolor=BG_WHITE)
    plt.close(fig)
    print(f"  ✓ {out_file.name}")


def make_error_analysis_white():
    """White-themed error analysis chart: side-by-side diagnosis of 30 most confident misclassifications."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.6, 4.3), dpi=200)
    fig.patch.set_facecolor(BG_WHITE)

    # Left: False Positives (15 cases)
    fp_reasons = ["Answered within 7d\n(Unaccepted / Abandoned)", "Niche Tag\n(Zero answers received)", "Boundary Case\n(Answered >7 days)"]
    fp_counts = [10, 4, 1]
    bars_fp = ax1.barh(fp_reasons, fp_counts, color=[ACCENT_ORANGE, "#F59E0B", "#FBBF24"], height=0.52, edgecolor="none")
    for bar, val in zip(bars_fp, fp_counts):
        ax1.text(val + 0.2, bar.get_y() + bar.get_height() / 2, f"{val} ({val/15*100:.0f}%)",
                 va="center", ha="left", fontsize=9.5, fontweight="bold", color=TEXT_DARK)
    ax1.set_xlabel("Count (out of 15 audited FP cases)", fontsize=9.5, fontweight="bold", color=TEXT_DARK)
    ax1.set_title("False Positives: High Predicted Resolution", fontsize=11, fontweight="bold", color=ACCENT_ORANGE, pad=10)
    ax1.set_xlim(0, 14.5)
    ax1.grid(axis="x", alpha=0.6, color=GRID_COLOR, linestyle=":")
    for s in ("top", "right"):
        ax1.spines[s].set_visible(False)

    # Right: False Negatives (15 cases)
    fn_reasons = ["New Account\n(0-day tenure)", "No Code Block\n(Concept query)", "Android / Framework\nComplex Error", "Long Body +\nDense Text", "Other Niche\nEdge Cases"]
    fn_counts = [8, 2, 2, 1, 2]
    bars_fn = ax2.barh(fn_reasons, fn_counts, color=[LINE_DARK, ACCENT_BLUE, "#0D9488", ACCENT_PURPLE, "#6B7280"], height=0.52, edgecolor="none")
    for bar, val in zip(bars_fn, fn_counts):
        ax2.text(val + 0.2, bar.get_y() + bar.get_height() / 2, f"{val} ({val/15*100:.0f}%)",
                 va="center", ha="left", fontsize=9.5, fontweight="bold", color=TEXT_DARK)
    ax2.set_xlabel("Count (out of 15 audited FN cases)", fontsize=9.5, fontweight="bold", color=TEXT_DARK)
    ax2.set_title("False Negatives: Low Predicted Resolution", fontsize=11, fontweight="bold", color=LINE_DARK, pad=10)
    ax2.set_xlim(0, 11.5)
    ax2.grid(axis="x", alpha=0.6, color=GRID_COLOR, linestyle=":")
    for s in ("top", "right"):
        ax2.spines[s].set_visible(False)

    fig.suptitle("Qualitative Error Diagnostics: 30 Most Confident Misclassifications",
                 fontsize=12, fontweight="bold", color=TEXT_DARK, y=0.99)
    fig.tight_layout()
    out_file = OUT / "error_analysis_white.png"
    fig.savefig(out_file, dpi=200, bbox_inches="tight", facecolor=BG_WHITE)
    plt.close(fig)
    print(f"  ✓ {out_file.name}")


def make_split_white():
    """White-themed chronological dataset split timeline showing resolution rate decline."""
    q = pd.read_parquet(PARQUET, columns=["created_at", "target_resolved_7d", "sampling_weight"])
    q["month"] = q.created_at.dt.tz_localize(None).dt.to_period("M").dt.to_timestamp()
    m = q.groupby("month").apply(lambda g: np.average(g.target_resolved_7d, weights=g.sampling_weight) * 100,
                                 include_groups=False)

    fig, ax = plt.subplots(figsize=(10.0, 3.8), dpi=200)
    fig.patch.set_facecolor(BG_WHITE)

    spans = [
        ("Train (2019-2024)\n248,294 rows (85%)", "2019-01-01", "2025-01-01", "#DBEAFE", LINE_DARK, 53.0),
        ("Validation\n28,132 (10%)", "2025-01-01", "2025-07-01", "#CCFBF1", "#0F766E", 47.5),
        ("Held-Out Test\n16,695 (5%)", "2025-07-01", "2026-08-01", "#FEF3C7", ACCENT_ORANGE, 53.0),
    ]

    for label_text, start, end, fill_col, border_col, y_pos in spans:
        ax.axvspan(pd.Timestamp(start), pd.Timestamp(end), color=fill_col, alpha=0.55, linewidth=0)
        mid = pd.Timestamp(start) + (pd.Timestamp(end) - pd.Timestamp(start)) / 2
        ax.text(mid, y_pos, label_text, ha="center", va="top", fontsize=8.8, fontweight="bold", color=border_col)

    ax.plot(m.index, m.values, color=LINE_DARK, linewidth=2.2, label="Monthly Resolution Rate (Weighted %)")
    ax.axvline(pd.Timestamp("2022-11-30"), color=ACCENT_RED, linestyle="--", linewidth=1.2, alpha=0.8)
    ax.text(pd.Timestamp("2022-11-30") + pd.Timedelta(days=15), 24, "ChatGPT Launch\n(Nov 2022)",
            color=ACCENT_RED, fontsize=8, fontweight="bold")

    ax.set_ylim(16, 56)
    ax.set_ylabel("Resolved in 7 Days (%)", fontsize=10, fontweight="bold", color=TEXT_DARK)
    ax.set_title("Chronological Partitioning & Resolution Rate Trajectory (2019 - 2026)",
                 fontsize=11.5, fontweight="bold", color=TEXT_DARK, pad=10)
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.grid(True, linestyle=":", alpha=0.6, color=GRID_COLOR)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

    fig.tight_layout()
    out_file = OUT / "split_white.png"
    fig.savefig(out_file, dpi=200, bbox_inches="tight", facecolor=BG_WHITE)
    plt.close(fig)
    print(f"  ✓ {out_file.name}")


def make_model_comparison_white():
    """White-themed PR-AUC and ROC-AUC benchmark comparison across all models."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.6, 4.2), dpi=200)
    fig.patch.set_facecolor(BG_WHITE)

    models = ["Majority\nClass", "Baseline\nLogReg", "LogReg\n+Text SVD", "Random\nForest", "XGBoost\n(Val)", "XGBoost\n(Test)"]
    pr_aucs = [0.341, 0.394, 0.471, 0.473, 0.482, 0.431]
    roc_aucs = [0.500, 0.579, 0.636, 0.638, 0.645, 0.655]

    colors_pr = ["#9CA3AF", "#9CA3AF", ACCENT_BLUE, ACCENT_BLUE, LINE_DARK, ACCENT_ORANGE]
    bars1 = ax1.bar(models, pr_aucs, color=colors_pr, edgecolor="none", width=0.58)
    for bar, val in zip(bars1, pr_aucs):
        ax1.text(bar.get_x() + bar.get_width() / 2, val + 0.008, f"{val:.3f}",
                 ha="center", va="bottom", fontsize=8.5, fontweight="bold", color=TEXT_DARK)
    ax1.set_ylabel("PR-AUC Score", fontsize=10, fontweight="bold", color=TEXT_DARK)
    ax1.set_title("Precision-Recall AUC (PR-AUC) Comparison", fontsize=10.5, fontweight="bold", pad=8)
    ax1.set_ylim(0, 0.56)
    ax1.grid(axis="y", alpha=0.6, color=GRID_COLOR, linestyle=":")
    for s in ("top", "right"):
        ax1.spines[s].set_visible(False)
    ax1.tick_params(axis="x", labelsize=8)

    colors_roc = ["#9CA3AF", "#9CA3AF", ACCENT_BLUE, ACCENT_BLUE, LINE_DARK, ACCENT_ORANGE]
    bars2 = ax2.bar(models, roc_aucs, color=colors_roc, edgecolor="none", width=0.58)
    for bar, val in zip(bars2, roc_aucs):
        ax2.text(bar.get_x() + bar.get_width() / 2, val + 0.008, f"{val:.3f}",
                 ha="center", va="bottom", fontsize=8.5, fontweight="bold", color=TEXT_DARK)
    ax2.set_ylabel("ROC-AUC Score", fontsize=10, fontweight="bold", color=TEXT_DARK)
    ax2.set_title("ROC-AUC Comparison (Ranking Discrimination)", fontsize=10.5, fontweight="bold", pad=8)
    ax2.set_ylim(0, 0.76)
    ax2.grid(axis="y", alpha=0.6, color=GRID_COLOR, linestyle=":")
    for s in ("top", "right"):
        ax2.spines[s].set_visible(False)
    ax2.tick_params(axis="x", labelsize=8)

    fig.suptitle("Predictive Modeling Benchmark Performance Across Candidate Architectures",
                 fontsize=12, fontweight="bold", color=TEXT_DARK, y=0.99)
    fig.tight_layout()
    out_file = OUT / "model_comparison_white.png"
    fig.savefig(out_file, dpi=200, bbox_inches="tight", facecolor=BG_WHITE)
    plt.close(fig)
    print(f"  ✓ {out_file.name}")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    print("Generating authentic white-background scientific charts...")
    make_timeseries_forecast_white()
    make_confusion_white()
    make_shap_bar_white()
    make_rolling_white()
    make_error_analysis_white()
    make_split_white()
    make_model_comparison_white()
    print("All white-background charts generated successfully!")
