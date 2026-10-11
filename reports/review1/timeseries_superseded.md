# Review 1 forecast results superseded by Review 2

The old `timeseries.py` selected Holt parameters against the 2025–26 test weeks and presented `100 - MAPE` as "accuracy". Its old results are historical artifacts, not an unbiased multi-horizon forecast benchmark.

Review 2 replaces that evaluation with 2024 H2 validation, fixed choices before the 2025–26 expanding-window backtest, naive/seasonal-naive/drift baselines, four horizons, MASE/sMAPE/log-RMSE, prediction-interval coverage, convergence logs and residual diagnostics. The new results are in `reports/review2/ts/`.

The old GRU is optional and is not presented as a winner without the same backtest. No old result is edited to imply a new evaluation took place.
