# Nishanth: Review 2 viva

- **Why did the chosen model win under the fixed rule?**
  The selection rule was fixed in advance before looking at results: select the highest NPMI topic coherence among candidates that meet strict semantic quality gates (topic diversity $\ge 0.70$ and multi-seed stability $\ge 0.60$). NMF consistently outperforms LDA on short, sparse technical texts because its non-negative parts-based representation forms cleaner, non-overlapping clusters without getting trapped in diffuse Dirichlet posteriors.

- **What does NPMI measure?**
  Normalized Pointwise Mutual Information (NPMI) measures how strongly top topic words co-occur in real documents on an independent 20,000-question held-out sample, normalized between -1 (never co-occurring) and +1 (always co-occurring). Higher positive NPMI proves that the model's top keywords represent genuine semantic concepts used together by real developers, rather than mathematical artifacts.

- **Why equal sampling by half-year (5,000 per half-year)?**
  Because Stack Overflow question volume collapsed by ~98% post-2022. If we sampled uniformly across all questions, pre-AI questions (2019–2022) would overwhelm the sample (>85% of data), completely hiding emerging post-AI technologies, frameworks, and modern error patterns. Stratifying by half-year ensures that post-AI technical topics remain equally visible and well-represented in the vector space.

- **What does the bootstrap interval mean for a topic's share change?**
  We run 1,000 question resamples (retaining each question's survey sampling weight) to calculate 95% empirical confidence intervals for the pre-to-post change in topic share. If the 95% interval does not contain zero, the topic's relative rise or fall is statistically robust and not an artifact of random sampling noise.

- **Why Monroe et al. (2008) log-odds with Dirichlet prior for keywords?**
  Raw frequency differences and basic log-odds ratios are heavily biased toward either extremely frequent stopwords or rare outlier terms. The Monroe, Colaresi & Quinn (2008) formulation uses an informative Dirichlet prior derived from the pooled background corpus, shrinking low-frequency noisy words toward the background frequency and computing an exact z-score for statistically significant term shifts.

- **What shifted in developer topics after AI adoption?**
  Basic syntax, routine data structure manipulation, and introductory how-to questions experienced significant volume drops (consistent with developers offloading simple lookup queries to AI assistants). In contrast, setup, environment configuration, multi-technology integration, deployment, and version migration topics retained higher shares and community need.
