# Member 5: forecasting findings

- Models were selected on 2024 H2 validation; the expanding-window 2025–26 backtest uses first-forecast-week origins spaced four weeks apart.
- On matched origins, SARIMAX's mean 26-week skill versus naive is 55.9%; this is a retrospective model-family comparison, not a new selection from test results.
- Nominal 95% SARIMAX bands cover 52.0% of the 26-week endpoints on matched origins: intervals are too narrow for this changing process.
- The validation-selected site model is sarimax; its week-26 median is 134.2 questions versus 215 in the last observed week (-37.6%). Forecasts end February 23, 2027.
- There are 10 recorded fit failures. Zero baseline counts cannot support a percentage-change tag class; ITS slope interpretation awaits Akshay's estimates.

Association is not causation. MASE is scaled forecast error, not percent accuracy.
