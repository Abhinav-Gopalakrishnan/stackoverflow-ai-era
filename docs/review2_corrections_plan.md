# Review 2 readiness corrections

Baseline: main 41bcd40. Presentation deadline: 19 October 2026, 20:00 Asia/Kolkata.
All corrections use branch `corrections`, separate phase commits and one integration PR.

## Phase order and completion gates

1. **Reproducible topic evaluation.** Fit every NMF/LDA candidate on the same actual stratified training sample, evaluate disjoint held-out text, use three seeds, retain measured scores and convergence evidence. Select by the written rule. Regenerate topic weights, terms, examples, weighted trends/outcomes and topic-by-tag data; label any AI-generated names as AI.
2. **Application integration.** Export current results and provenance; connect supported tag/date/period controls, explicitly disable unsupported controls, correct weekly ITS units, and show both Unit 2 and Unit 3 results. Verify real interactions and fresh-clone launch.
3. **Notebooks and scientific interpretation.** Generate the complete Units 1–3 notebook from saved results, including final-data sample, validation, classifier comparison and two Unit 3 methods. Remove unsupported causal claims and stale takeaways. Execute all submission notebooks.
4. **Report and submission package.** Regenerate data-linked recommendations and a figure-complete PDF; finish all five contribution summaries, direct evidence links, dataset sample/validation/files manifest and local demo instructions. Include reference rubric/template without editing the originals. Record AI-assisted validation limits and optional work accurately.
5. **Final verification and merge.** Run the existing suite and targeted interaction/data-consistency checks in isolation, inspect the report and app, update board evidence/status honestly, push the correction branch, open one PR and merge only after the readiness checks pass. Preserve actual history and do not fabricate approvals or human annotations.

## Fixed boundaries

- Existing classification test results remain locked; do not tune on the examined test period.
- Time-series model selection remains 2024 H2, with the separate 2025–26 rolling backtest.
- AI annotations remain AI; the original two-human annotation requirement is an explicit protocol deviation, not a completed human check.
- Public hosting and Kaggle publication were in the internal plan; the official rubric also accepts a locally runnable dashboard and source code. Provide a working local demo and honest availability status.
- New final presentation creation follows this correction pass; existing member slides must not contain stale values.
