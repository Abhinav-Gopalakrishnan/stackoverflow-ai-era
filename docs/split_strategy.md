# Split and Validation Strategy

> Historical Review 1 design/evidence. The implemented v2 model protocol and remaining snapshot limitations are documented in [the current technical handoff](final_implementation.md). Original locked results have not been regenerated.

## 1. Chronological Split
We will use a chronological split rather than a random split. The data will be partitioned as follows:
- **Training Set:** January 2019 to December 2024
- **Validation Set:** January 2025 to June 2025
- **Test Set:** July 2025 to July 2026

**Why not a random split?** 
A random split would leak future patterns into the training data. For instance, if user habits change globally in 2024, a random split would allow the model to learn from 2024 data to predict 2023 data, which is unrealistic in a production setting. We must predict the future using only the past.

## 2. Time-Series Cross-Validation
Inside the training period (Jan 2019 to Dec 2024), we will use time-series cross-validation folds. This ensures that even during cross-validation, the model is trained on past data and evaluated on subsequent data, preserving the chronological integrity.

## 3. Rolling-Origin Evaluation (with Member 5)
To understand how model performance changes over time, especially before and after November 2022 (the release of ChatGPT), we will implement a rolling-origin evaluation.
- We will train on all data available before a specific half-year.
- We will test on that half-year.
- We will iterate this process for every half-year from **2021 H1 to 2026 H1**.

This approach provides a continuous view of performance, allowing us to compare results from before and after the AI adoption shift, which a single static test period cannot provide.
