# Topic analysis: viva

- Measured selection: NMF k=15; document NPMI -0.0270, diversity 0.735, three-seed stability 0.788.
- Both families use 75,814 identical training IDs, a shared vocabulary and 20,000 disjoint reference questions. Document NPMI is explicitly different from sliding-window c_npmi.
- Transformed 302,026 questions; 0 zero-vocabulary records have no assigned topic.
- Names are automatic top-term descriptions; independent human naming agreement is unavailable. Old model IDs/names are archived.
- Largest decreases: T8 Arrays and object manipulation: -1.80 pp (95% CI -1.96 to -1.66); T13 Collections and programming operations: -1.66 pp (95% CI -1.83 to -1.49); T1 Dataframe rows and columns: -1.04 pp (95% CI -1.24 to -0.81)
- Largest increases: T12 Docker containers and images: +1.28 pp (95% CI +1.13 to +1.43); T9 Android development and builds: +1.06 pp (95% CI +0.88 to +1.23); T11 API requests and responses: +0.86 pp (95% CI +0.68 to +1.05)
- These are changes within the observed collection. They do not demonstrate AI offloading, topic difficulty or causal effects. Keyword rankings remain a separate saved analysis.

- Why three seeds? To measure sensitivity to initialisation.
- Why bootstrap? To estimate question-sampling uncertainty while retaining historic weights.
- Is NPMI accuracy? No; it measures term cooccurrence coherence.
