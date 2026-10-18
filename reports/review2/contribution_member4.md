# Member 4 — Nishanth

## Original contribution

[PR #140](https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era/pull/140) supplied topic-model code, weighted topic-prevalence/outcome exports, representative linked examples, keyword-shift analysis, tests and the text-notebook handoff. Source: `src/topics.py`, `src/keywords.py` and `tests/test_topics.py`. PR #170 supplied the earlier member slides.

## Corrections and current evidence

The original topic comparison contained illustrative score rows. The corrections branch replaces those rows with actual NMF/LDA fits on the same training IDs, shared vocabulary, disjoint coherence reference and three seeds. Current metrics, sample sizes, winning model and convergence evidence are read from `topic_model_selection.csv`, `topic_model_seed_results.csv` and `topic_grid_manifest.json`.

The corrected protocol uses exact document-cooccurrence NPMI, explicitly differing from sliding-window c_npmi. New topic IDs receive automatic term descriptions; original human/AI names are not transferred by ID. Old topic outputs/slides are preserved only as superseded archive evidence. Keyword analysis remains a separate result and must not be described as measured migration to AI tools.

Evidence: `reports/review2/text/`, `docs/review2_topic_evaluation.md`, `notebooks/08_text_mining.ipynb`. The corrections are credited to their actual Git author; no independent human naming agreement or new presentation is claimed.
