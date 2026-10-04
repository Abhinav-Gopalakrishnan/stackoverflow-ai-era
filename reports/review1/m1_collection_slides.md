# Member 1: Data Collection & Dataset Overview Slides (M1-16)

> **Speaker:** Member 1 (Abhinav Gopalakrishnan)  
> **Order:** 2nd Speaker (immediately following Member 3's Problem Statement)  
> **Target Time:** 1.5 minutes  
> **Deliverable:** Content for Team Slide Deck (BA Final Project — Review 1)

---

## Slide 1: Data Collection & Sampling Methodology
**Title (states the finding):** Stratified day sampling captures 309,179 questions across 13 tags with 100% census in the post-AI era

### Key Bullet Points:
- **API Architecture & Reliability:**
  - Automated client calling Stack Exchange API v2.3 (`api.stackexchange.com`) with rate-limiting ($0.5\text{s}$ throttle), quota protection, and exponential backoff retry.
  - Resolved transient errors ($2\times \text{HTTP 502 Bad Gateway}$ recovered on retry).
  - Uncovered and fixed the Stack Exchange API `has_more=False` paging bug via page+1 probing, recovering 3,222 questions for `reactjs` and 393 for `docker`.
- **Stratified Day-Level Sampling Design:**
  - **Pre-2025 (2019–2024):** 1 random weekday + 1 random weekend day per tag-month (seed 42) with inverse-probability weights ($w = \text{days in month} / \text{days sampled}$). Accurately reproduces annual volume within $\pm 2\%$.
  - **Post-2025 (2025–2026):** 100% exhaustive census collection for all days to observe the post-ChatGPT collapse without day-sampling variance.
  - **Audit Log Telemetry:** 19,306 requests logged across 2 distinct quota days; 0 raw user IDs exposed.
- **Privacy & Compliance:**
  - Full adherence to CC BY-SA 4.0; all user IDs hashed using SHA-256 + secret `HASH_SALT`. Minimal API filters (`base="none"`) exclude all personal profiles.

### Visual on Slide:
- **Left:** Architecture flow diagram (API $\to$ Cache $\to$ Paging Probe $\to$ Privacy Mask $\to$ Parquet).
- **Right:** Sampling rate bar chart (6.5% pre-2025 $\to$ 100% census 2025+). *Source: Chart 2 of `03_eda.ipynb`.*

---

## Slide 2: Dataset Overview & Cross-Validation
**Title (states the finding):** 8-year population trends match SEDE within 0.01%, confirming a 92% decline in question volume

### Key Bullet Points:
- **Scope & Scale:**
  - **Study Window:** Exactly 2,800 days (`2019-01-01` to `2026-08-31` UTC) = 92 calendar months = 400 non-overlapping 7-day weeks.
  - **Tag Representation:** 13 technology tags spanning high-volume general-purpose (`python`, `javascript`), data analytics (`sql`, `r`, `pandas`), frameworks (`reactjs`, `android`, `docker`), and AI-era entrants (`fastapi`, `openai-api`).
  - **Population Baseline:** 5,600 weekly counts (`filter=total`) across 14 series (13 tags + site-wide `ALL`). Zero missing weeks.
- **SEDE Cross-Validation & Verified Headline Numbers:**
  - **March 2014 Peak:** 207,204 questions/month (historical all-time high).
  - **2022 Pre-AI Baseline:** 1,336,266 questions/year (1.33M site-wide).
  - **2025 Post-AI Volume:** 108,981 questions/year (**91.8% structural decline**).
  - **July 2026:** 1,442 questions/month (**99.3% drop** from 2014 peak).
  - Weekly population sum matches official monthly totals within **0.01%** across all tags (`fastapi`: 0% error; `python`: -0.009%).

### Visual on Slide:
- **Top:** 4-box Headline Metric summary tiles (Peak 2014: 207k $\to$ 2022: 1.33M $\to$ 2025: 108k $\to$ July 2026: 1.4k).
- **Bottom:** Stacked question distribution by tag per year (Chart 1 of `03_eda.ipynb`).

---

## Speaker Notes (1.5 Minutes Delivery)

### Slide 1 Delivery (~45 seconds):
> *"To study question resolution, we built a reproducible collection client against the public Stack Exchange API v2.3 across 2,800 days from January 2019 to August 2026.*  
> *Because collecting 4 million raw questions would exceed API limits, we engineered a stratified sampling scheme: sampling one weekday and one weekend day per month prior to 2025 with inverse-probability weights, and collecting 100% of all days from 2025 onwards to eliminate variance in the AI era.*  
> *During collection, we uncovered a silent API paging bug where `has_more` returned False prematurely on busy days. We implemented a page-plus-one probing rule that recovered over 3,600 missing records across React and Docker.*  
> *Every user ID was immediately hashed with SHA-256 and a secret salt, ensuring strict privacy compliance under CC BY-SA 4.0."*

### Slide 2 Delivery (~45 seconds):
> *"In total, we collected 309,179 detailed question records and 5,600 weekly population counts across 13 target ecosystems.*  
> *To guarantee that our findings are mathematically sound, we cross-validated our weekly counts against Stack Exchange Data Explorer queries. Across all 92 months, our population counts match official SEDE figures within 0.01%.*  
> *These verified headline figures reveal the platform's trajectory: from its historical peak of 207,000 questions a month in 2014, volume stood at 1.33 million in 2022, before collapsing by 92% to 108,000 in 2025, and just 1,442 questions in July 2026.*  
> *With our population verified, Member 2 will explain how these raw records were enriched, cleaned, and labeled."*
