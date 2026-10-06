# Exploratory Data Analysis (EDA) Plan

This document maps out every planned EDA chart, target research question, required data assets, visualization specifications, and task owner assignments. All charts generated in `notebooks/03_eda.ipynb` must answer a specific research question and include a written takeaway.

---

## 1. Planned EDA Visualizations & Mapping Matrix

| Chart ID | Target Research Question | Required Data Assets & Source | Visualization Type & Parameters | Task Owner |
| :---: | :--- | :--- | :--- | :---: |
| **EDA-01** | How did weekly question volume change per tag (2019–2026), and how do milestones, site-wide share, and the OpenAI-API contrast align? | Complete weekly tag counts (`Member 1`: `tag_week_count`, `weekly_counts.csv`, `docs/event_list.csv`) | **Line charts for total volume and site-wide volume share & Small Line Charts for tag volumes**<br>Selected tags' total, 12-subplot log-scale small multiples, site-wide share, and OpenAI-API contrast line with event overlays. | Member 3 |
| **EDA-02** | What is the class balance for both targets, how do monthly weighted resolution rates vary by tag, and how did acceptance habits shift over time? | Cleaned question table & monthly weighted tables (`Member 2`: `target_resolved_7d`, `target_answered_7d`, `accepted_given_answered`, `post_ai`) | **Bar Chart, Small Line Charts & Comparison Table**<br>Pre/post-Nov 2022 comparison, monthly rates with low-sample months greyed out, and dual-target class balance. | Member 3 |
| **EDA-03** | How do time-to-accepted-answer and time-to-first-answer distributions and monthly weighted medians vary overall, by tag, and pre/post-November 2022? | Cleaned question table (`Member 2`: `hours_to_accept`, `hours_to_first_answer`, `tags`, `post_ai`) | **Log-Scale Distributions & Monthly Weighted Medians**<br>Log-scale violin plots overall and by tag, plus pre/post-cutoff monthly median trendlines. | Member 3 |
| **EDA-04** | Do code blocks, error text, body length bands, number of tags, and question words impact question resolution frequency? | Cleaned question table (`Member 2`: `n_code_blocks`, `code_ratio`, `has_error_text`, `body_len`, `n_tags`, `question_word`, `target_resolved_7d`) | **Bar Charts with Absolute Counts**<br>Resolution rate bar charts across structural and linguistic features, displaying sample counts directly on each bar. | Member 3 |
| **EDA-05** | Does asker account age, new account status (<7 days), or posting hour/weekday affect resolution success? | Cleaned question table (`Member 2`: `account_age_days`, `first_question`, `hour`, `weekday`, `target_resolved_7d`) | **Binned Bar Charts & Weighted Heatmap**<br>Resolution rate by tenure brackets and new account flags, plus a 7x24 UTC weighted weekday-hour heatmap. | Member 3 |
| **EDA-06** | Which features exhibit statistically significant relationships with resolution success, and what are their effect sizes? | Cleaned question table (`Member 2`: all feature columns and targets) | **Statistical Tables & Correlation Heatmap**<br>Chi-square tests (categorical), Mann-Whitney tests (lengths), and numeric correlation matrix reporting effect sizes and p-values. | Member 3 |
| **EDA-07** | What are the top-5 actionable insights for feature engineering? | Sampling manifest & collected counts (`Member 3`: EDA notebook outputs) | **Structured Insight List**<br>A top-5 insights list at the end of the EDA notebook, each linked to a feature for Member 4 to build or check. | Member 3 |
| **EDA-08** | What is the overall API collection coverage and tag sampling validation? | Yearly collected question count by tag and collected versus total counts by month for sampled months | **Small Multiple Lines Chart & Area Chart**<br>Collected question volume per year per tag and sampled question volume vs. complete weekly count totals over time. | Member 1 |

---

## 2. Implementation Guidelines

1. **Notebook Execution:** All visualizations will be authored in `notebooks/03_eda.ipynb`.
2. **Chart Presentation Standards:**
   * Every chart must feature an explicit title stating the analytical takeaway (e.g., *"Resolution rates dropped 14% post-AI across 9 of 12 tags"*) rather than a generic descriptive header.
   * Annotations for key milestone dates (`ChatGPT Launch`, `Stack Overflow ChatGPT Ban`, etc.) must be consistently overlaid where applicable.
