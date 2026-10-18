# Review 2 evidence and remaining presentation work

Official reference: `docs/review2_reference/Review_2_Requirements_and_Rubrics .docx` (20 marks, 15-minute team presentation). Final verification outcomes are recorded in `verification.json`, `test_results.txt` and `completion_checks.json`.

| Rubric requirement | Concrete evidence |
|---|---|
| Overall validated dataset; Units 1–3 | `dataset/dataset_validation.json`, `dataset/dataset_schema.csv`, `dataset/final_dataset_sample.csv`, `docs/data_dictionary.md`, complete notebook |
| Method 1 preparation/implementation (2) | Separate API weekly totals, complete bins, STL/ADF/KPSS/PELT/ITS, `src/ts_patterns.py`, `src/ts_forecast.py`, `ts/` manifests |
| Method 1 evaluation/comparison/interpretation (3) | Fixed validation selection, separate rolling backtest, three baselines/ETS/SARIMAX, matched origins, MASE/skill/coverage, failures and diagnostics |
| Method 2 preparation/implementation (2) | Prose/code separation, technical vocabulary, shared train/reference IDs, NMF/LDA, keywords, tone and complexity |
| Method 2 evaluation/comparison/interpretation (3) | 36 measured fits, exact document-NPMI/diversity/stability, per-seed evidence, weighted bootstrap, one-human-reference tone evaluation with AI provenance |
| Combined insights/recommendations (2) | `insight_matrix.csv`, `recommendations.csv`, `src/review2_m3_insights.py`: tag-specific evidence, action/stakeholder/KPI/caveat |
| Interactive application (5) | Seven local Streamlit pages, source-matched exports, meaningful control tests, captured screenshots, `docs/dashboard_deploy.md` |
| Contribution history and understanding (part of 3) | Five `contribution_member*.md` summaries, actual linked PR history, board, viva notes and submission guide |

## Explicit deviations and limitations

- Original internal-plan two-human tone adjudication and topic naming are **not completed**. AI labels are not human labels; issue #126 remains open. VADER accuracy is only 36% against the available single human reference. Current topic names are automatic descriptions.
- Exact document-cooccurrence NPMI replaces sliding-window c_npmi. The change is disclosed; old illustrative comparison rows and topic names are archived, not used as current evidence.
- Topic coherence is not classification accuracy, and automatically named topics are exploratory. No inference of AI offloading or difficulty from topic share alone.
- Forecast intervals under-cover; zero-baseline percentage classes remain undefined. Associations do not establish causal AI effects.
- The full 302 MiB final dataset is supplied separately with a checksum. Git contains its sanitized sample/schema and enough aggregates to run the app/notebooks.
- No verified public deployment, Kaggle publication or recorded video is claimed. A locally runnable application satisfies the official application format requirement.

## What happens after corrections

1. Build the new final presentation with the official template, covering the complete Units 1–3 workflow and emphasizing the two Unit 3 methods, evaluation, live app and individual contributions.
2. Rehearse the 15-minute team presentation and each member's viva explanations. Individual understanding and live demonstration marks cannot be completed by repository edits.
3. Attach the new presentation and separate full-dataset bundle to the evaluator submission. Use the source/results ZIP and checksum manifest generated under ignored `submission/`.

Original member decks are supporting references; they are not the new final team presentation. The corrected M4 reference replaces its obsolete topic values. Issue #122 tracks the final presentation stage.
