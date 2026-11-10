# Final project submission — Team 7

Course: **23CSE452 Business Analytics**, Final Project 2026.

## Required deliverables

| Requirement | Repository location |
|---|---|
| Project overview and team/register details | `README.md` |
| Original and cleaned data, provenance and validation | `data/README.md`, `data/original/`, `data/cleaned/`, `data/submission_manifest.json`, `docs/dataset_documentation.md` |
| Unit 1 collection, preparation and EDA | `notebooks/01_collection.ipynb`, `02_cleaning.ipynb`, `03_eda.ipynb`, `review1_main.ipynb` |
| Unit 2 features, classification and evaluation | `notebooks/04_features.ipynb`, `05_models.ipynb`, `06_evaluation.ipynb`, `reports/review1/m5/`, `reports/final_validation/` |
| Unit 3 Time-Series Analysis and Text Mining | `notebooks/review2_main.ipynb`, `07_timeseries.ipynb`, `08_text_mining.ipynb`, `reports/review2/ts/`, `reports/review2/text/` |
| Cross-method comparison and business recommendations | `reports/review2/insight_matrix.csv`, `reports/review2/recommendations.csv`, final report |
| Interactive application | `dashboard/`, live link below |
| Charts and dashboard evidence | `visualizations/`, `reports/final_validation/screenshots/` |
| Final PDF report | `Final_Project_Report.pdf` |
| Final team presentation | `Final_Project_Presentation.pptx` |
| Dependencies | `requirements.txt`, `dashboard/requirements.txt` |
| Individual contributions | `reports/review2/contribution_member1.md` through `contribution_member5.md`, linked PR history |
| Project management | GitHub Projects link below; historical audit in `reports/review2/board_audit_member1.md` |

## Submission links

- Repository: https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era
- Dashboard: https://stackoverflow-ai-era.streamlit.app/
- Project board: https://github.com/users/Abhinav-Gopalakrishnan/projects/3

**Access action before submission:** the repository is public, but GitHub reports
the project board as private at the final packaging check on 10 November 2026.
The owner must make the board public or grant the evaluator access before relying
on that link. This packaging task does not change remote access settings.

The final issue draft is in `docs/final_submission_issue.md`. Submit **one issue for
Team 7** in the faculty repository after committing and pushing the staged files
to this repository's `main`. No faculty issue is created by the packaging scripts.

## Fresh-clone use

Dashboard only (no credentials or full-data restoration):

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install -r dashboard/requirements.txt
.venv/bin/python -m streamlit run dashboard/app.py
```

Full data and saved analysis:

```bash
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/submission_data.py --verify
.venv/bin/python scripts/submission_data.py --restore
```

The original data shards are directly readable parquet; the cleaned binary parts
must first be restored with the command above. No external data host is required.
Rebuilding NLP models additionally needs the language resources described in
`docs/final_implementation.md`. Saved-result notebooks use the included evidence;
they do not replace full model-training implementations in `src/`.

## Disclosed analytical limitations

The analysis is observational and cannot establish a causal effect of generative AI.
The classifier uses an accepted-answer posting-time proxy, snapshot text can contain
later edits, and the revised August evaluation is retrospective. Forecast bands
under-cover. Topic names are provisional automatic descriptions; the 75-row human
topic-review packet remains incomplete. Tone evaluation has one human reference,
with 36% VADER accuracy; AI annotations are not additional human reviews. Business
benefits are assumptions for proposed pilots, not measured savings.

These limitations are already discussed in the report/presentation. Do not claim
independent two-human validation or mark the human-review worksheets completed.

## Historical documentation

Review 1/2 work plans, earlier report PDFs, member slides and old ZIP packaging
instructions are retained as project history. Use the root final report and
presentation for submission. The final PDF's separate-dataset note describes the
earlier handoff; the current public bundle restores the exact file and checksum
listed there. Some presentation slides describe the earlier seven-page dashboard;
the current release has eight pages, including Predict a Question.
