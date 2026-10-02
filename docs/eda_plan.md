# Exploratory Data Analysis (EDA) Plan

This document maps out every planned EDA chart, target research question, required data assets, visualization specifications, and task owner assignments. All charts generated in `notebooks/03_eda.ipynb` must answer a specific research question and include a written takeaway.

---

## 1. Planned EDA Visualizations & Mapping Matrix

| Chart ID | Target Research Question | Required Data Assets & Source | Visualization Type & Parameters | Task Owner |
| :---: | :--- | :--- | :--- | :---: |
| **EDA-01** | How did weekly question volume change per tag from 2019 to 2026, and where do key milestone events align? | Complete weekly tag counts (`Member 1`: `tag_week_count` / `filter=total` API endpoint) | **Small Multiples Line Chart**<br>12 subplots (one per tag) with logarithmic y-axis and vertical event overlays (`docs/event_list.csv`). | Member 1 |
| **EDA-02** | How did the 7-day resolution rate (`target_resolved_7d`) change before vs after November 2022 across tags? | Cleaned question table (`Member 2`: `creation_date`, `target_resolved_7d`, `tags`, `post_ai`) | **Grouped Bar Chart & Trend Overlay**<br>Pre- vs. Post-AI comparison of 7-day resolution percentage per tag with 95% confidence intervals. | Member 3 |
| **EDA-03** | How does time to accepted answer vary by technology tag, and how skewed are answer response windows? | Cleaned question table (`Member 2`: `hours_to_accept`, `tags`, `accepted_answer_id`) | **Log-Scale Box Plot / Violin Plot**<br>Distribution of `hours_to_accept` grouped by tag using log10 scale to handle long-tail delays. | Member 3 |
| **EDA-04** | Do questions containing code blocks, error tracebacks, or longer bodies get resolved more frequently? | Cleaned question table (`Member 2`: `n_code_blocks`, `code_ratio`, `has_error_text`, `body_len`, `target_resolved_7d`) | **Stacked Bar / Bin Analysis Charts**<br>Resolution percentage broken down by presence of error text (`has_error_text`) and code ratio bins. | Member 3 |
| **EDA-05** | Does asker account age (user tenure) at the time of posting relate to question resolution success? | Cleaned question table (`Member 2`: `account_age_days`, `first_question`, `target_resolved_7d`) | **Binned Bar Chart & Continuous KDE**<br>Resolution rate by account tenure brackets (e.g., `<1d`, `1-30d`, `30-365d`, `1y+`) and first-time asker indicator. | Member 3 |
| **EDA-06** | Which posting hours and weekdays yield the fastest answers and highest resolution rates? | Cleaned question table (`Member 2`: `hour`, `weekday`, `hours_to_accept`, `target_resolved_7d`) | **Weighted Heatmap**<br>7x24 Matrix (Weekday vs UTC Hour) color-coded by median `hours_to_accept` and resolution rate. | Member 3 |
| **EDA-07** | How balanced is the target class (`target_resolved_7d`) overall and across pre- and post-AI time periods? | Cleaned question table (`Member 2`: `target_resolved_7d`, `post_ai`) | **Proportional Stacked Bar Chart**<br>Class balance ratio (Resolved vs. Unresolved) split by pre-AI (2019–Nov 2022) and post-AI (Dec 2022–2026). | Member 3 |
| **EDA-08** | What is the overall API collection coverage and tag sampling validation against baseline totals? | Raw collection logs & counts (`Member 1`: `logs/collection_log.csv`, cross-check comparison table) | **Coverage Line & Area Chart**<br>Sampled question volume vs. complete weekly count totals over time. | Member 1 |

---

## 2. Implementation Guidelines

1. **Notebook Execution:** All visualizations will be authored in `notebooks/03_eda.ipynb`.
2. **Chart Presentation Standards:**
   * Every chart must feature an explicit title stating the analytical takeaway (e.g., *"Resolution rates dropped 14% post-AI across 9 of 12 tags"*) rather than a generic descriptive header.
   * Annotations for key milestone dates (`ChatGPT Launch`, `Stack Overflow ChatGPT Ban`, etc.) must be consistently overlaid where applicable.
