"""Generate dark-themed chart images for Member 5's additional slides."""

import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

ROOT = Path("/home/adhikkesh/adhikkesh/SEM7/BA/stackoverflow-ai-era")
M5 = ROOT / "reports" / "review1" / "m5"
OUT = ROOT / "reports" / "review1" / "deck_assets"

# Dark theme colors
BG = "#1A1D24"
CARD = "#131822"
MINT = "#1DE9B6"
ORANGE = "#FF9800"
WHITE = "#FFFFFF"
LIGHT = "#CFD8DC"
GRID = "#2A2F3A"
CYAN = "#00BCD4"
PINK = "#FF4081"
PURPLE = "#B388FF"
YELLOW = "#FFD54F"

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
    "font.size": 11,
})


def make_shap_bar_dark():
    """Horizontal bar chart of top 10 SHAP features."""
    df = pd.read_csv(M5 / "shap_top.csv", index_col=0)
    df = df.sort_values("mean_abs_shap", ascending=True)

    fig, ax = plt.subplots(figsize=(7.5, 4.5))

    # Readable feature names
    name_map = {
        "lagged_tag_volume": "Tag Volume (4-wk lag)",
        "account_age_days": "Account Age (days)",
        "code_ratio": "Code Block Ratio",
        "n_code_blocks": "# Code Blocks",
        "title_tfidf_svd_5": "Title Text (SVD-5)",
        "body_length": "Body Length",
        "title_tfidf_svd_3": "Title Text (SVD-3)",
        "title_tfidf_svd_2": "Title Text (SVD-2)",
        "title_tfidf_svd_28": "Title Text (SVD-28)",
        "title_tfidf_svd_20": "Title Text (SVD-20)",
    }
    labels = [name_map.get(n, n) for n in df.index]

    colors = [MINT if v >= 0.09 else CYAN for v in df["mean_abs_shap"]]
    bars = ax.barh(labels, df["mean_abs_shap"], color=colors, edgecolor="none", height=0.6)

    for bar, val in zip(bars, df["mean_abs_shap"]):
        ax.text(val + 0.003, bar.get_y() + bar.get_height()/2,
                f"{val:.3f}", va="center", ha="left", color=WHITE, fontsize=9.5, fontweight="bold")

    ax.set_xlabel("Mean |SHAP value|", fontsize=12, color=MINT)
    ax.set_title("Top 10 Feature Importances (SHAP)", fontsize=14, fontweight="bold", color=WHITE, pad=12)
    ax.set_xlim(0, max(df["mean_abs_shap"]) * 1.22)
    ax.grid(axis="x", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()
    fig.savefig(OUT / "shap_bar_dark.png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    print("  ✓ shap_bar_dark.png")


def make_pr_roc_dark():
    """Dark PR and ROC curves from the validation comparison data."""
    # Use the existing val_pr_roc.png — but we'll make a cleaner dark version
    # with just the key message: XGBoost beats all others
    from matplotlib.patches import FancyBboxPatch

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.5, 4.2))

    # PR-AUC comparison (bar chart is more readable for slides)
    models = ["Majority\nClass", "Baseline\nLogReg", "LogReg\n+Text", "Random\nForest", "XGBoost\n(Val)", "XGBoost\n(Test)"]
    pr_aucs = [0.341, 0.394, 0.471, 0.473, 0.482, 0.431]
    roc_aucs = [0.500, 0.579, 0.636, 0.638, 0.645, 0.655]

    colors_pr = [LIGHT, LIGHT, CYAN, CYAN, MINT, ORANGE]
    bars1 = ax1.bar(models, pr_aucs, color=colors_pr, edgecolor="none", width=0.6)
    for bar, val in zip(bars1, pr_aucs):
        ax1.text(bar.get_x() + bar.get_width()/2, val + 0.008, f"{val:.3f}",
                 ha="center", va="bottom", fontsize=8.5, fontweight="bold", color=WHITE)
    ax1.set_ylabel("PR-AUC", fontsize=11, color=MINT)
    ax1.set_title("Precision-Recall AUC Comparison", fontsize=12, fontweight="bold", pad=10)
    ax1.set_ylim(0, 0.58)
    ax1.grid(axis="y", alpha=0.25)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    ax1.tick_params(axis="x", labelsize=8)

    colors_roc = [LIGHT, LIGHT, CYAN, CYAN, MINT, ORANGE]
    bars2 = ax2.bar(models, roc_aucs, color=colors_roc, edgecolor="none", width=0.6)
    for bar, val in zip(bars2, roc_aucs):
        ax2.text(bar.get_x() + bar.get_width()/2, val + 0.008, f"{val:.3f}",
                 ha="center", va="bottom", fontsize=8.5, fontweight="bold", color=WHITE)
    ax2.set_ylabel("ROC-AUC", fontsize=11, color=MINT)
    ax2.set_title("ROC-AUC Comparison", fontsize=12, fontweight="bold", pad=10)
    ax2.set_ylim(0, 0.78)
    ax2.grid(axis="y", alpha=0.25)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    ax2.tick_params(axis="x", labelsize=8)

    fig.tight_layout(w_pad=3)
    fig.savefig(OUT / "model_comparison_dark.png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    print("  ✓ model_comparison_dark.png")


def make_rolling_dark():
    """Dark-themed rolling-origin evaluation chart showing stability over time."""
    df = pd.read_csv(M5 / "rolling_origin.csv")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.5, 4.2))

    # Left: PR-AUC, F1, base rate over time
    ax1.plot(df["window"], df["pr_auc"], marker="o", color=MINT, linewidth=2.2, markersize=6, label="PR-AUC", zorder=5)
    ax1.plot(df["window"], df["f1"], marker="s", color=ORANGE, linewidth=2.2, markersize=6, label="F1", zorder=5)
    ax1.plot(df["window"], df["positive_rate"], marker="^", color=LIGHT, linewidth=1.5, markersize=5, linestyle=":", label="Base rate", zorder=4)

    # Nov 2022 vertical line
    ax1.axvline(x=3.5, color=PINK, linestyle="--", linewidth=1.5, alpha=0.7, label="ChatGPT launch")

    ax1.set_ylabel("Score", fontsize=11, color=MINT)
    ax1.set_title("Performance by Half-Year Window", fontsize=12, fontweight="bold", pad=10)
    ax1.legend(fontsize=8, loc="upper right", framealpha=0.3)
    ax1.set_ylim(0.15, 0.70)
    ax1.grid(axis="y", alpha=0.25)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    ax1.tick_params(axis="x", rotation=45, labelsize=7.5)

    # Right: ROC-AUC (stable) vs PR-AUC minus base rate
    pr_lift = df["pr_auc"] - df["positive_rate"]
    ax2.plot(df["window"], df["roc_auc"], marker="o", color=MINT, linewidth=2.2, markersize=6, label="ROC-AUC", zorder=5)
    ax2.plot(df["window"], pr_lift, marker="s", color=PURPLE, linewidth=2.2, markersize=6, label="PR-AUC − base rate", zorder=5)
    ax2.axvline(x=3.5, color=PINK, linestyle="--", linewidth=1.5, alpha=0.7, label="ChatGPT launch")

    ax2.set_ylabel("Score", fontsize=11, color=MINT)
    ax2.set_title("Ranking Quality Over Time", fontsize=12, fontweight="bold", pad=10)
    ax2.legend(fontsize=8, loc="upper right", framealpha=0.3)
    ax2.set_ylim(0.0, 0.75)
    ax2.grid(axis="y", alpha=0.25)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    ax2.tick_params(axis="x", rotation=45, labelsize=7.5)

    fig.tight_layout(w_pad=3)
    fig.savefig(OUT / "rolling_dark.png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    print("  ✓ rolling_dark.png")


def make_error_analysis_dark():
    """Dark-themed error analysis chart: stacked bar of error categories."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.5, 4.2))

    # Left: False positive reasons
    fp_reasons = ["Answered but\nnot accepted", "Niche tag\n(no answer)", "Boundary\n(just past 7d)"]
    fp_counts = [10, 4, 1]
    colors_fp = [ORANGE, YELLOW, PINK]
    bars_fp = ax1.barh(fp_reasons, fp_counts, color=colors_fp, edgecolor="none", height=0.5)
    for bar, val in zip(bars_fp, fp_counts):
        ax1.text(val + 0.2, bar.get_y() + bar.get_height()/2, str(val),
                 va="center", ha="left", fontsize=11, fontweight="bold", color=WHITE)
    ax1.set_xlabel("Count (out of 15)", fontsize=10, color=ORANGE)
    ax1.set_title("False Positives", fontsize=13, fontweight="bold", color=ORANGE, pad=10)
    ax1.set_xlim(0, 14)
    ax1.grid(axis="x", alpha=0.2)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)

    # Right: False negative reasons
    fn_reasons = ["New account\n(0 days old)", "No code block", "Android + error", "Long body +\nerror text", "Error text\nmissed", "High-visibility\nquestion"]
    fn_counts = [8, 2, 2, 1, 1, 1]
    colors_fn = [MINT, CYAN, CYAN, PURPLE, PURPLE, LIGHT]
    bars_fn = ax2.barh(fn_reasons, fn_counts, color=colors_fn, edgecolor="none", height=0.5)
    for bar, val in zip(bars_fn, fn_counts):
        ax2.text(val + 0.2, bar.get_y() + bar.get_height()/2, str(val),
                 va="center", ha="left", fontsize=11, fontweight="bold", color=WHITE)
    ax2.set_xlabel("Count (out of 15)", fontsize=10, color=MINT)
    ax2.set_title("False Negatives", fontsize=13, fontweight="bold", color=MINT, pad=10)
    ax2.set_xlim(0, 11)
    ax2.grid(axis="x", alpha=0.2)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)

    fig.suptitle("Error Analysis: 30 Most Confident Misclassifications", fontsize=14, fontweight="bold", color=WHITE, y=1.02)
    fig.tight_layout(w_pad=3)
    fig.savefig(OUT / "error_analysis_dark.png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    print("  ✓ error_analysis_dark.png")


if __name__ == "__main__":
    print("Generating dark-themed charts for Member 5 slides...")
    make_shap_bar_dark()
    make_pr_roc_dark()
    make_rolling_dark()
    make_error_analysis_dark()
    print("Done!")
