# Initial Business Findings (Review 1)

This document translates exploratory data analysis (EDA) insights into actionable business findings for forum managers, community leads, and developer platform executives. 

---

### Finding 1: Code-Inclusive Questions Improve Resolution Efficiency

* **Supporting Metric:** Questions containing explicit code blocks achieve a **~43% 7-day resolution rate**, compared to only **~31%** for text-only questions (a 12 percentage point resolution advantage). Additionally, concise posts under 500 characters achieve a **~43% resolution rate**, whereas detailed posts exceeding 3,000 characters drop to **~30%**.
* **Target Stakeholder:** Developer Forum Product Managers & Technical Community Operations Teams.
* **Suggested Action:** Implement smart post-creation UX prompts. When a user drafts a question exceeding 1,000 characters without a code block, automatically suggest inserting a minimal reproducible code snippet. Introduce an inline "Code Assistant" widget during post creation to help users extract concise code blocks before publishing.

---

### Finding 2: Response Delays and Lower Acceptance Rates Post-2022

* **Supporting Metric:** Comparing the pre-November 2022 period to the post-2022 period, the overall 7-day resolution rate dropped from **44.1% to 35.8%**, and the probability of an answered question being marked as accepted (`accepted_given_answered`) fell from **57.0% down to 50.1%**. Furthermore, median time to accept an answer lengthened from **~0.84 hours (~50 minutes) to ~2.60 hours**.
* **Target Stakeholder:** Developer Support Leads & Community Knowledge Base Operations.
* **Suggested Action:** Re-engage askers via automated, time-decayed notification triggers. For questions that receive an answer within 2 hours, dispatch automated email or app reminders at 24-hour and 72-hour intervals asking the author to verify and accept the resolution if valid. Track `accepted_given_answered` as a core health KPI to distinguish platform abandonment from answer quality issues.

---

### Finding 3: New Account Onboarding Friction and Timing-Based Routing

* **Supporting Metric:** Accounts under 7 days old achieve a **~33% 7-day resolution rate**, whereas user accounts older than 7 days plateau at a significantly higher **~42% resolution rate**. Meanwhile, resolution rates exhibit strong operational variance across the week, peaking during weekend off-peak hours (up to **47.2%** on late Saturday UTC) versus weekday lows of **~38%**.
* **Target Stakeholder:** Forum Onboarding Engineers & Community Support Triage Teams.
* **Suggested Action:** Implement targeted triage for newcomer posts. Automatically route questions posted by users with tenure under 7 days to dedicated community moderators or a "First Responder" review queue. Balance weekday support coverage by establishing automated SLA alerts during low-throughput UTC weekday windows.

---

### Finding 4: Structural Volume Shifts Associated with AI Tool Adoption

* **Supporting Metric:** Following late 2022, total question volume across core tags experienced a steep decline, while site-wide exhaustive census collection in 2025 captured ~45,000 total questions—matching the volume captured by a 6.5–7.5% sample in earlier years. This reflects a **~90% structural drop in site-wide question generation** relative to pre-2023 volume baselines.
* **Target Stakeholder:** Platform Strategy Executives & Developer Relations (DevRel) Directors.
* **Suggested Action:** Shift platform strategy from high-volume basic Q&A triage to high-value, complex domain indexing. Reposition platform tooling toward tracking emergent tech stacks (e.g., fast-growing frameworks like `fastapi` or `openai-api`) where automated LLMs lack updated local context, and incentivize expert verification on intricate multi-tag questions.

---

*Note on Licensing & Data Privacy:* Example questions cited in this analysis are represented solely by title and direct URL link to comply with Stack Exchange CC BY-SA 4.0 licensing and privacy guidelines.

---

# Model findings (Member 5 section for `initial_findings.md`)

**What the model offers a support-forum manager.** An XGBoost model, trained on questions up to December 2024 and scored once on 16,695 questions from July 2025 to July 2026, ranks questions by their chance of getting an accepted answer within 7 days. It is better than no skill but the gain is modest: PR-AUC 0.43 against 0.30 for a no-skill ranking, ROC-AUC 0.65.

1. **Flagging 20% of questions catches 24% of the unresolved ones** (1.2 times random flagging, which catches 20%). Stakeholder: support-forum manager. Action: use the score to prioritise which questions experts see first, not to decide outcomes.
2. **The strongest signals are tag volume in the previous 4 weeks, asker account age, share of code in the body.** Higher asker account age, share of code in the body, number of code blocks are associated with more accepted answers. Brand-new accounts and questions with no code blocks are the least often resolved; the effect levels off for older accounts. Resolution rises with some code, then falls again for questions that are almost all code. Error text, longer titles and longer bodies are associated with fewer accepted answers in the test period; the r tag with more, python and android with fewer. Tag volume stays in one narrow, low range in the test period (volume has fallen since 2022), so it stands in for the period and tag mix, not for the question itself. Stakeholder: community or product team. Action: prompt askers to add code to their question before posting; do not assume error text helps, because it is associated with fewer accepted answers here.
3. **The share of resolved questions fell, but the model's ranking quality did not.** The share resolved is 42% in test windows before November 2022 and 33% after, while mean ROC-AUC is 0.64 before and 0.65 after across 11 half-year windows. PR-AUC falls from 0.56 to 0.47, which follows the lower base rate (PR-AUC minus base rate: 0.14 before, 0.14 after). The drop in resolution is associated with the period around November 2022 but is not proof of cause. Stakeholder: analytics lead. Action: track the resolution rate itself over time.
4. **The ranking is similar for a second target.** Predicting any answer within 7 days gives ROC-AUC 0.67 (accepted answer: 0.65); PR-AUC is not comparable because 71% of questions get an answer within 7 days against 30% an accepted one.

**Limits.** An accepted answer within 7 days is a strict proxy for resolved because it depends on the asker returning. Gains over a no-skill ranking are modest, and the three real models differ only slightly. Recent data (2025 onwards) is smaller than the sampled early years. Only 13 tags are covered. AI-related statements say 'associated with' or 'consistent with', never 'caused'.
