# Review 1 Contribution Summary: Member 4 (Nishanth Konchada)

Role: Data Splitting, Feature Engineering, Baseline Modeling, and Leakage Assessment Lead
Rubric components owned: Splitting Strategy (2 marks); Baseline Models (1 mark); Feature Engineering Pipeline (2 marks); Leakage/Multicollinearity Checks (part of 3 marks)

---

## Tasks Completed
| Issue | Title | Evidence link | Reviewed by |
|:---|:---|:---|:---:|
| #24 | [M4-04] Split module and verification | [PR #96](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/96) | Member 5 |
| #25 | [M4-05] Feature pipeline | [PR #97](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/97) | Member 5 |
| #26 | [M4-06] Correlation and leakage check | [PR #98](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/98) | Member 5 |
| #27 | [M4-07] Baseline model | [PR #99](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/99) | Member 5 |

---

## Key Outputs
- **`src/split.py`**: A robust data partitioning module that chronologically separates the dataset into Training (2019–2024), Validation (Jan-Jun 2025), and Test (Jul 2025+). Also includes a `create_time_series_folds` function to prevent future-data leakage during cross-validation.
- **`src/features.py`**: A comprehensive feature extraction and transformation pipeline. It constructs predictive signals (`title_length`, `tag_count`, `hour_posted`, `question_word`), integrates structural metrics, applies `StandardScaler` to continuous variables, and executes `OneHotEncoder` on categorical variables.
- **`src/leakage_check.py`**: A dedicated diagnostic script for identifying multicollinearity via Variance Inflation Factor (VIF) and Pearson correlation coefficients against the target.
- **`src/baseline.py`**: The baseline Logistic Regression model training script that establishes a performance floor (64% Accuracy, 58% ROC AUC) for advanced models to beat.
- **`notebooks/04_features.ipynb`**: The fully executed and logged pipeline notebook serving as the primary evidence artifact for Phase 3.

---

## Decisions I Made and Why
1. **Chronological Splitting over Random Splitting**: Because Stack Overflow user behaviour and platform dynamics (like the sudden adoption of AI tools in late 2022) are highly non-stationary, random splitting would introduce severe target leakage by allowing the model to "peek" into the future. A strict chronological split ensures we evaluate the model purely on its ability to generalize to subsequent, unseen time periods.
2. **Implementation of Time-Series Cross-Validation Folds**: Inside the training period, standard k-fold cross-validation would randomize the time series. I implemented rolling-origin folds to ensure that even during cross-validation, the model only trains on past data and predicts subsequent data, preserving temporal integrity.
3. **Addressing the Dummy Variable Trap (VIF > 1e15)**: During the correlation and leakage analysis, I discovered that one-hot encoding the `question_word` column introduced perfect multicollinearity. I resolved this structurally by forcing the `OneHotEncoder` to drop the first category (`drop='first'`), removing the rank deficiency from the design matrix.
4. **Excluding Outcome-Descriptive Variables**: Strictly filtered out features like `score`, `view_count`, and `answer_count`. Because these metrics accumulate after the question is posted, they leak the outcome (`target_resolved_7d`). Models were strictly restricted to data available at the exact moment of posting.
5. **Selecting Logistic Regression as the Baseline**: I chose Logistic Regression because it is highly interpretable, fast to train on 250k+ rows, and provides a clear linear baseline to benchmark Member 5's non-linear, gradient boosted tree (XGBoost) approach against.

---

## Reviews I Gave
- **Member 1 (#2, #3, #4, #17, #27, #40, #49, #64, #77, #79, #81, #83, #85, #87, #89, #91)**: Actively reviewed and merged the entirety of Member 1's Data Collection, Repository Management, and EDA coverage PRs, ensuring tight synchronisation with the `main` branch.
- **Member 5 (Pending)**: Acting as the designated reviewer for the Phase 4 Advanced Models (XGBoost) and Hyperparameter Tuning PRs.

---

## Problems Faced and How I Solved Them
- **Massive Data Bottlenecks in Memory**: Running pandas apply functions on 316MB of parquet data (300,000+ rows) caused memory and processing delays. I refactored `src/features.py` to utilize vectorized pandas operations (`str.len()`, `.dt.hour`, etc.) instead of slow iterative lambda functions, cutting processing time significantly.
- **Dummy Variable Trap**: The initial feature set failed statsmodels VIF checks with `SingularMatrixWarning`. Diagnosed this as perfect collinearity among the one-hot encoded categories and implemented the `drop='first'` fix in the pipeline.
- **PowerShell Encoding Issues**: Attempting to dynamically generate Jupyter Notebook JSON strings via PowerShell resulted in UTF-16LE encoding errors and syntax crashes. I bypassed terminal string constraints by authoring dedicated Python build scripts (`update_nb.py`) that cleanly load, manipulate, and overwrite the `04_features.ipynb` AST natively in Python.

---

## What I Can Explain in the Viva
- **Temporal Leakage vs Feature Leakage**: I can articulate the difference between data leaking from the future (solved by chronological splits) and outcome leaking from the target (solved by excluding post-creation metrics).
- **Time-Series Cross-Validation Mechanics**: How rolling origins expand the training window step-by-step while maintaining a forward-looking validation block.
- **Multicollinearity and VIF**: The mathematical definition of the dummy variable trap, why it breaks linear models (rank-deficient design matrix), and how Variance Inflation Factor is calculated.
- **Baseline Logistic Regression Metrics**: Interpretation of our 64% Accuracy and 42% Precision, and why Precision/Recall are often more critical than Accuracy in imbalanced prediction tasks.
- **Another Member's Area**: Member 5's XGBoost architecture, boosting intuition, and the specific hyperparameters they tuned to improve upon my baseline model.
