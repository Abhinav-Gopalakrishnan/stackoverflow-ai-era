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

## Phase 1 measured outcome

Completed 36 actual fits on 75,814 training IDs and 20,000 disjoint reference IDs.
The fixed rule selects NMF k=15: document-NPMI -0.027001, diversity 0.735111,
stability 0.788062. LDA's best mean coherence is higher, but all LDA candidates
fail the stability threshold. Low/negative coherence is a semantic-quality limitation,
not an accuracy result. All 302,026 questions and 14 tag groups are exported.
Old topic names/AI annotations are archived; new names are automatic, with numerical
and screenshot-boilerplate mixtures flagged. Artifact checks and all eight topic tests pass.

## Phase 2 integration outcome

37 current dashboard exports (2.618 MiB); seven application pages including dataset
and locked classifier evidence. Period/date/tag interactions alter observation charts;
fixed-model pages disable irrelevant controls. ITS units are weekly, topic intervals
use percentage points, and AI/human provenance remains separate. Semantic tests,
the full 146-test suite and all seven pages in a clean minimal dependency environment pass.

## Phase 3 notebook outcome

The complete notebook covers Units 1–3, data preview/validation, the locked classifier,
both advanced methods, actual comparisons and combined recommendations. All three
notebooks execute without errors (17, 7 and 7 code cells). Kernel metadata remains
portable `python3`. Unsupported causal/AI-offloading claims and the incorrect STL
headline are corrected. Original classifier test results remain unchanged.

## Phase 4 report and package preparation outcome

The report embeds all six figures, renders to eight pages and keeps the contribution
table intact. Five original member summaries link actual PRs; integration corrections
retain their actual author. Recommendations use current tag-specific topics and
explicit units/caveats. Official rubric/template copies are unchanged. Dataset schema,
40-row preview, validation/checksum, local-app guide, screenshots and package builder
are supplied. The existing M4 reference deck now reads the measured results.

## Phase 5 final verification outcome

147 tests pass (five reported library warnings) in an isolated copy. The 37 exported
CSVs match their actual sources before any test fixture rewrites them. Seven pages
pass with minimal app dependencies and without the full data; an explicit separate
run also passes without API credentials. Three notebooks execute without errors.
All eight report pages, six embedded figures and the corrected two-slide M4 reference
were visually inspected. Desktop captures cover seven pages plus a mobile view.
The last review removes numeric/path/URL placeholders from business-facing keyword
views (raw rankings retained) and corrects the language-scope statement. Merge follows
this verified commit; final presentation/rehearsal and the disclosed two-human protocol
deviation remain outside the completed implementation corrections.
