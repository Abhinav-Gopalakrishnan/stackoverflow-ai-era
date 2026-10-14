"""Export and slim Review 2 method outputs into dashboard/data/.

Only clean, aggregated and privacy-compliant CSV files are exported.
Parquet files, question bodies, and user hashes are strictly excluded.
"""

from pathlib import Path
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "dashboard" / "data"

MAX_TOTAL_SIZE_MB = 50.0

FORBIDDEN_COLUMNS = {
    "body",
    "plain_body",
    "code_text",
    "owner_user_id",
    "user_id",
    "user_hash",
    "account_id",
}

# Source -> Destination and required columns specification
EXPORT_SPECS = {
    "series_long.csv": {
        "src": ROOT / "reports" / "review2" / "ts" / "series_long.csv",
        "columns": ["tag", "week_start", "count", "log_count", "share_of_all"],
    },
    "monthly_rates_masked.csv": {
        "src": ROOT / "reports" / "review2" / "ts" / "monthly_rates_masked.csv",
        "columns": [
            "tag",
            "month",
            "n_sampled",
            "est_questions",
            "resolved_rate_7d",
            "answered_rate_7d",
            "accepted_given_answered",
            "median_hours_to_accept",
            "median_hours_to_first_answer",
            "low_sample",
        ],
    },
    "stl_components.csv": {
        "src": ROOT / "reports" / "review2" / "ts" / "stl_components.csv",
        "columns": ["tag", "week_start", "log_count", "trend", "seasonal", "resid"],
    },
    "changepoints.csv": {
        "src": ROOT / "reports" / "review2" / "ts" / "changepoints.csv",
        "columns": [
            "tag",
            "index",
            "week_start",
            "mean_before",
            "mean_after",
            "delta",
            "nearest_event_date",
            "nearest_event_name",
            "distance_days",
            "within_4_weeks_of_event",
        ],
    },
    "its_results.csv": {
        "src": ROOT / "reports" / "review2" / "ts" / "its_results.csv",
        "columns": [
            "tag",
            "intervention_date",
            "intervention_week_start",
            "intervention_event",
            "placebo_break_date",
            "n_weeks",
            "n_pre_weeks",
            "n_post_weeks",
            "beta0",
            "beta1",
            "beta2",
            "beta3",
            "level_change",
            "level_change_pct",
            "level_ci_lo",
            "level_ci_hi",
            "level_p",
            "slope_change",
            "slope_change_pct",
            "slope_ci_lo",
            "slope_ci_hi",
            "slope_p",
            "slope_pre",
            "slope_post",
            "status",
            "placebo_level_change",
            "placebo_level_ci_lo",
            "placebo_level_ci_hi",
            "placebo_level_p",
            "placebo_slope_change",
            "placebo_slope_ci_lo",
            "placebo_slope_ci_hi",
            "placebo_slope_p",
            "effect_exceeds_placebo",
        ],
    },
    "forecasts_26w.csv": {
        "src": ROOT / "reports" / "review2" / "ts" / "forecasts_26w.csv",
        "columns": [
            "tag",
            "model",
            "week_start",
            "horizon",
            "selected",
            "pred",
            "log_pred",
            "lower80",
            "upper80",
            "lower95",
            "upper95",
        ],
    },
    "tag_classes.csv": {
        "src": ROOT / "reports" / "review2" / "ts" / "tag_classes.csv",
        "columns": [
            "tag",
            "selected_model",
            "change_26w_pct",
            "forecast_class",
            "last_week_count",
            "forecast_week26",
            "post2023_log_slope",
            "half_life_weeks",
            "load_index_vs_2025",
            "its_slope_change_pct",
            "its_status",
        ],
    },
    "backtest_summary_matched.csv": {
        "src": ROOT / "reports" / "review2" / "ts" / "backtest_summary_matched.csv",
        "columns": [
            "model",
            "horizon",
            "n_series",
            "mase",
            "smape",
            "log_rmse",
            "skill_vs_naive",
            "coverage80",
            "coverage95",
        ],
    },
    "backtest_metrics_matched.csv": {
        "src": ROOT / "reports" / "review2" / "ts" / "backtest_metrics_matched.csv",
        "columns": [
            "tag",
            "model",
            "horizon",
            "n_origins",
            "mase",
            "smape",
            "coverage80",
            "coverage95",
            "naive_mase",
            "log_rmse",
            "skill_vs_naive",
        ],
    },
    "model_choices.csv": {
        "src": ROOT / "reports" / "review2" / "ts" / "model_choices.csv",
        "columns": ["tag", "selected_model", "p", "q", "validation_end", "selection"],
    },
    "topics_top_terms.csv": {
        "src": ROOT / "reports" / "review2" / "text" / "topics_top_terms.csv",
        "columns": ["topic", "rank", "term", "weight"],
    },
    "topic_monthly_share.csv": {
        "src": ROOT / "reports" / "review2" / "text" / "topic_monthly_share.csv",
        "columns": ["topic", "month", "period", "weighted_share", "n_questions"],
    },
    "topic_prepost.csv": {
        "src": ROOT / "reports" / "review2" / "text" / "topic_prepost.csv",
        "columns": [
            "topic",
            "pre_share",
            "post_share",
            "change",
            "change_pct",
            "lower95",
            "upper95",
            "bootstrap_resamples",
        ],
    },
    "topic_outcomes.csv": {
        "src": ROOT / "reports" / "review2" / "text" / "topic_outcomes.csv",
        "columns": ["topic", "n_questions", "resolved_rate_7d", "median_hours_to_first_answer"],
    },
    "topic_examples.csv": {
        "src": ROOT / "reports" / "review2" / "text" / "topic_examples.csv",
        "columns": ["topic", "title", "link"],
    },
    "topic_labels.csv": {
        "src": ROOT / "reports" / "review2" / "text" / "topic_labels.csv",
        "columns": ["topic", "top_terms", "name_m4", "name_m2", "final_name", "agreement"],
    },
    "tone_monthly.csv": {
        "src": ROOT / "reports" / "review2" / "text" / "tone_monthly.csv",
        "columns": [
            "tag",
            "month",
            "period",
            "n_sampled",
            "low_sample",
            "negative_share",
            "neutral_share",
            "positive_share",
            "frustration_flag_share",
            "politeness_flag_share",
        ],
    },
    "tone_prepost.csv": {
        "src": ROOT / "reports" / "review2" / "text" / "tone_prepost.csv",
        "columns": [
            "tag",
            "measure",
            "pre",
            "post",
            "change",
            "lower95",
            "upper95",
            "bootstrap_resamples",
        ],
    },
    "tone_validation.csv": {
        "src": ROOT / "reports" / "review2" / "text" / "tone_validation.csv",
        "columns": [
            "status",
            "labelled_rows",
            "required_rows",
            "accuracy",
            "macro_f1",
            "cohen_kappa",
        ],
    },
    "complexity_monthly.csv": {
        "src": ROOT / "reports" / "review2" / "text" / "complexity_monthly.csv",
        "columns": [
            "tag",
            "month",
            "period",
            "n_sampled",
            "low_sample",
            "prose_words_median",
            "code_lines_median",
            "n_code_blocks_median",
            "tag_count_median",
            "flesch_reading_ease_median",
            "error_text_flag_share",
            "why_how_flag_share",
            "version_flag_share",
            "multi_technology_flag_share",
        ],
    },
    "complexity_prepost.csv": {
        "src": ROOT / "reports" / "review2" / "text" / "complexity_prepost.csv",
        "columns": [
            "tag",
            "metric",
            "statistic",
            "pre",
            "post",
            "change",
            "lower95",
            "upper95",
            "n_pre",
            "n_post",
            "bootstrap_resamples",
        ],
    },
    "keywords_prepost.csv": {
        "src": ROOT / "reports" / "review2" / "text" / "keywords_prepost.csv",
        "columns": [
            "term",
            "z_score",
            "log_odds",
            "count_pre",
            "count_post",
            "freq_pre_pct",
            "freq_post_pct",
            "direction",
            "rank",
            "tag_scope",
        ],
    },
    "recommendations.csv": {
        "src": ROOT / "reports" / "review2" / "recommendations.csv",
        "columns": [
            "finding",
            "time_series_evidence",
            "text_mining_evidence",
            "action",
            "stakeholder",
            "kpi_to_track",
            "caveat",
        ],
    },
    "insight_matrix.csv": {
        "src": ROOT / "reports" / "review2" / "insight_matrix.csv",
        "columns": [
            "tag",
            "forecast_class",
            "change_26w_pct",
            "half_life_weeks",
            "load_index_vs_2025",
            "its_level_change_pct",
            "its_level_p",
            "its_slope_change_pct",
            "its_slope_p",
            "its_status",
            "its_exceeds_placebo",
            "rising_topics",
            "falling_topics",
            "topic_evidence_scope",
            "frustration_change",
            "frustration_lower95",
            "frustration_upper95",
            "resolved_rate_pre",
            "resolved_rate_post",
            "resolved_rate_change",
            "complexity_prose_words_change",
            "complexity_code_lines_change",
            "complexity_version_flag_change",
        ],
    },
    "event_list.csv": {
        "src": ROOT / "docs" / "event_list.csv",
        "columns": ["event_id", "event_name", "date", "category", "description", "source_url"],
    },
}


def export_all():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    total_bytes = 0

    print(f"Exporting dashboard data to {DATA_DIR}...")
    print(f"{'Filename':<30} {'Rows':<8} {'Cols':<6} {'Size (KB)':<10}")
    print("-" * 56)

    for filename, spec in EXPORT_SPECS.items():
        src_path = spec["src"]
        if not src_path.exists():
            print(f"ERROR: Source file missing: {src_path}", file=sys.stderr)
            sys.exit(1)

        df = pd.read_csv(src_path)
        required_cols = spec["columns"]

        # Validate that all required columns are present in source
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            print(f"ERROR: {src_path.name} missing columns: {missing}", file=sys.stderr)
            sys.exit(1)

        # Slim down to exact required columns
        df_slim = df[required_cols].copy()

        # Security check: ensure no forbidden columns are present
        forbidden_found = [c for c in df_slim.columns if c.lower() in FORBIDDEN_COLUMNS]
        if forbidden_found:
            print(
                f"SECURITY ERROR: Forbidden columns {forbidden_found} in {filename}",
                file=sys.stderr,
            )
            sys.exit(1)

        dest_path = DATA_DIR / filename
        df_slim.to_csv(dest_path, index=False)

        size_bytes = dest_path.stat().st_size
        total_bytes += size_bytes
        print(f"{filename:<30} {len(df_slim):<8} {len(df_slim.columns):<6} {size_bytes / 1024:<10.2f}")

    total_mb = total_bytes / (1024 * 1024)
    print("-" * 56)
    print(f"Total exported data size: {total_mb:.3f} MB")

    if total_mb >= MAX_TOTAL_SIZE_MB:
        print(
            f"ERROR: Total size ({total_mb:.2f} MB) exceeds maximum allowed ({MAX_TOTAL_SIZE_MB} MB)",
            file=sys.stderr,
        )
        sys.exit(1)

    print("Export completed successfully.")


if __name__ == "__main__":
    export_all()
