# Corrected topic evaluation protocol

## Data and split

The corpus contains 302,026 question IDs. Fit on up to 5,000 nonempty documents per half-year, using seed 42 and fewer documents where that half-year has fewer than 5,000. The actual training sample is recorded in `topic_split_manifest.csv`; the 80,000 value in the original plan is a maximum, not an achieved sample size. Hold out 20,000 question IDs from the remaining corpus for coherence evaluation. Training and reference IDs must be disjoint.

Both NMF and LDA use exactly the same training IDs, training-fitted vocabulary and held-out reference IDs. TF-IDF uses unigrams/bigrams, min_df=20, max_df=0.4 and at most 30,000 features. NMF uses TF-IDF; LDA uses counts from the identical vocabulary. Topic fitting is unsupervised and deliberately balanced by half-year. Sampling weights are retained for population-share/outcome summaries, not used to pretend that the balanced fit is a population sample.

## Fixed candidate comparison

- Families: NMF (Frobenius loss, coordinate descent, nndsvda initialization) and sklearn LDA (online variational inference).
- Topic counts: 10, 15, 20, 25, 30, 40.
- Seeds: 42, 43, 44, with identical settings within each family.
- Iteration budgets: NMF up to 400, tolerance 1e-4; online LDA 10 passes. These are budgeted comparisons, not a claim that every model is globally optimal. Iterations and warnings remain in the per-seed evidence.
- Coherence: exact **document-cooccurrence NPMI** on each topic's top ten words in the held-out reference, averaged over topics. An unseen word pair receives -1. This implementation is not gensim's sliding-window c_npmi; the definition is disclosed and held fixed across candidates.
- Diversity: unique terms divided by all terms across top-25 topic lists, averaged across seeds.
- Stability: mean best-match Jaccard of top-ten lists across the three pairs of seed runs.
- NMF reconstruction error: measured Frobenius reconstruction error, averaged across seeds; not a directly comparable LDA metric.
- Selection: highest mean reference coherence among candidates with diversity >= 0.70 and stability >= 0.60. If none qualify, take highest coherence and disclose the fallback. No chosen model or result is fixed in advance.

`topic_model_seed_results.csv` contains measured per-seed results. `topic_model_selection.csv` contains their aggregate comparison. `topic_grid_manifest.json` records input fingerprint, dimensions, packages and completion status. Private fitted models and checkpoints are under the ignored `.review2_cache/` directory. Scores in the archive are superseded evidence and are not used for selection.

## Final model and summaries

The selected family/topic count uses the saved seed-42 fit; it is not refitted with different settings. Transform every corpus question with the correct feature representation (TF-IDF for NMF, counts for LDA). Normalize nonzero topic vectors; record and report zero-projection questions instead of assigning them falsely to topic 0.

Export top words, linked title-only examples, question-level topic weights privately, and weighted topic summaries globally and by study tag. Monthly low-sample flags apply when fewer than 30 questions support the tag-month. Pre/post differences exclude November–December 2022. Confidence intervals use 1,000 question bootstrap resamples with the sampled questions' existing survey weights retained. Joint resampling computes all topic-share means from the same draws, avoiding inconsistent independent topic resamples.

Topic outcome rates use dominant-topic membership, original sampling weights, and weighted median hours to first answer among observed response times. They are descriptive, not causal. A topic gaining share need not be gaining absolute question volume.

New model topic IDs must never inherit old topic names or annotations by ID alone. Automatic descriptive names are explicitly marked as suggestions; any later AI interpretation stays identified as AI. No human agreement statistic is generated without human evidence.

## Reproduction

```bash
python -m src.topics                 # measured grid, selected model and exports
python -m src.topics --grid-only     # same measured comparison, with resumable fits
python -m src.topics --transform-only  # reuse matching completed grid/checkpoints
```

The classifier's held-out test period is not reused for tuning. These full-corpus exploratory topic weights must not be added to the classifier without a separate training-only fit.
