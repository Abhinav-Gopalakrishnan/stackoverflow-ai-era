# Member 5: how to run the modelling

Needs `data/processed/questions_clean_v1.parquet` (Member 2; on the team drive, not in Git) and, for lagged tag volume, Member 1's complete weekly counts at `data/processed/weekly_counts.csv` or `data/shared/weekly_counts.csv` (git-ignored; columns `tag, week_start, count`). Until it is merged to main it is on branch `m1/weekly-counts`:
`mkdir -p data/shared && git show origin/m1/weekly-counts:data/processed/weekly_counts.csv > data/shared/weekly_counts.csv`.

```bash
pip install -r requirements.txt python-pptx        # python-pptx is only for the slides
python -m src.run_models                            # about 30-90 minutes; writes reports/review1/m5/
python -m src.run_models --no-rolling               # skip the rolling-origin step (saves most of the time)
python -m src.run_models --full                     # larger tuning search
python -m src.make_slides                           # slides + findings text from the finished run
```

Notes
- The test period is evaluated **once**. A lock file `reports/review1/m5/.test_evaluated` stops a second run. If you must start over, delete the `reports/review1/m5/` folder and say so in the report.
- Without `weekly_counts.csv` the run continues without the two lagged tag-volume features and prints a warning.
- Notebooks `05_models.ipynb` and `06_evaluation.ipynb` display the saved outputs; run the script first.
- Tests: `python tests/test_evaluate.py`, `tests/test_error_leakage.py`, `tests/test_models.py`, `tests/test_pipeline.py`.
- `reports/review1/m5/error_annotation_sheet.csv`: read each of the 30 questions at its link and fill `likely_reason` by hand; `auto_hint` is only a rule-based starting guess.
- GPU: XGBoost uses a GPU automatically when one works (e.g. a Colab T4 runtime); force with `M5_DEVICE=cuda` or `M5_DEVICE=cpu`. Random Forest, TF-IDF and SVD run on the CPU; TPUs are not used. GPU and CPU XGBoost can differ slightly in the last decimals.

After the main run (steps used for Review 1, run locally with the results in `reports/review1/m5/`):
```bash
python -m src.m4_baseline_eval     # Member 4's baseline scored with the shared metrics (needs their features_*.parquet from main)
python -m src.coef_structured      # plain-words logistic-regression coefficients (needs the cleaned parquet and weekly counts)
python -m src.make_slides          # slides + findings; also rebuilds the rolling-origin summary with base rate and ROC-AUC
```
`reports/review1/m5/shap_notes.txt` holds the hand-written reading of the SHAP plots used on the slides; `error_annotation_sheet.csv` has the reasons assigned after reading each of the 30 questions.
