# Final project visualizations

Selected charts cover all three units and the interactive dashboard. These are copies of saved project evidence; no models were refitted for packaging.

| Figure | Description | Numerical evidence |
|---|---|---|
| [project_workflow.png](project_workflow.png) | Units 1–3 workflow | [reports/final_submission/figures/workflow.png](../reports/final_submission/figures/workflow.png) |
| [unit1_weekly_volume.png](unit1_weekly_volume.png) | Sitewide weekly activity | [data/processed/weekly_counts.csv](../data/processed/weekly_counts.csv) |
| [unit1_resolution_monthly.png](unit1_resolution_monthly.png) | Weighted monthly resolution proxy | [dashboard/data/monthly_rates_masked.csv](../dashboard/data/monthly_rates_masked.csv) |
| [unit2_model_comparison.png](unit2_model_comparison.png) | Original classifier validation comparison | [dashboard/data/classifier_validation.csv](../dashboard/data/classifier_validation.csv) |
| [unit2_locked_test_pr_roc.png](unit2_locked_test_pr_roc.png) | Original locked-test PR and ROC curves | [reports/review1/m5/test_metrics.csv](../reports/review1/m5/test_metrics.csv) |
| [unit2_august_confusion.png](unit2_august_confusion.png) | Separate retrospective August classifier evaluation | [reports/final_validation/confusion.csv](../reports/final_validation/confusion.csv) |
| [unit3_time_series_decomposition.png](unit3_time_series_decomposition.png) | STL decomposition | [reports/review2/ts/stl_components.csv](../reports/review2/ts/stl_components.csv) |
| [unit3_time_series_its.png](unit3_time_series_its.png) | Interrupted time-series estimates | [reports/review2/ts/its_results.csv](../reports/review2/ts/its_results.csv) |
| [unit3_forecast_backtest_skill.png](unit3_forecast_backtest_skill.png) | Forecast skill comparison | [reports/review2/ts/backtest_metrics_matched.csv](../reports/review2/ts/backtest_metrics_matched.csv) |
| [unit3_sitewide_forecast.png](unit3_sitewide_forecast.png) | Sitewide forecast and uncertainty | [reports/review2/ts/forecasts_26w.csv](../reports/review2/ts/forecasts_26w.csv) |
| [unit3_topic_model_selection.png](unit3_topic_model_selection.png) | NMF versus LDA evaluation | [reports/review2/text/topic_model_selection.csv](../reports/review2/text/topic_model_selection.csv) |
| [unit3_topic_share_changes.png](unit3_topic_share_changes.png) | Weighted topic-share changes | [reports/review2/text/topic_prepost.csv](../reports/review2/text/topic_prepost.csv) |
| [unit3_tone_and_complexity.png](unit3_tone_and_complexity.png) | Tone and writing structure | [reports/review2/text/complexity_prepost.csv](../reports/review2/text/complexity_prepost.csv) |
| [dashboard_overview.png](dashboard_overview.png) | Dashboard overview evidence | [reports/final_validation/screenshots/01_overview.png](../reports/final_validation/screenshots/01_overview.png) |
| [dashboard_public_prediction.png](dashboard_public_prediction.png) | Public fitted-classifier result evidence | [reports/final_validation/public_deployment.json](../reports/final_validation/public_deployment.json) |
| [dashboard_business_scenarios.png](dashboard_business_scenarios.png) | Business scenario interface | [reports/final_validation/screenshots/09_scenarios.png](../reports/final_validation/screenshots/09_scenarios.png) |

The original classifier locked-test results and the revised August retrospective evaluation use different periods and must not be presented as a direct improvement comparison. Forecast intervals under-cover; topic names are automatic; tone validation is weak. Dashboard screenshots document captured states, not continuous availability.

`manifest.json` records source paths and checksums. Additional charts and their CSVs are preserved in `reports/review1/`, `reports/review2/` and `reports/final_validation/`.
