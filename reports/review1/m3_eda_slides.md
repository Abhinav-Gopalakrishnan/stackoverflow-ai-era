# Member 3: Problem Statement & EDA Slides (M3-14)

> **Speaker:** Member 3 (Akshay Krishna, CB.SC.U4CSE23403)  
> **Order:** 1st Speaker (opens the deck; Member 1 follows immediately with collection)  
> **Target Time:** 2.5 minutes  
> **Deliverable:** Content for Team Slide Deck (BA Final Project — Review 1)  
> **Source of every number:** `notebooks/03_eda.ipynb`, executed against `questions_clean_v1.parquet` — volume trends from issue #42, then sections `[M3-07]` to `[M3-12]`

---

## Slide 1: Problem Statement, Objective and Research Questions
**Title (states the finding):** We predict whether a Stack Overflow question is resolved within 7 days, so forum managers can route expert attention before a question stalls

### Key Bullet Points:
- **The problem:** developer Q&A activity is falling fast, and platform managers cannot tell which questions still need a human expert or which tags are heading for abandonment.
- **Business objective:** give community and platform managers a data-driven way to prioritise unresolved questions, allocate moderation effort across shifting tags, and plan documentation and engagement.
- **Primary target — `target_resolved_7d`:** the question receives an **accepted** answer within 7 days (168 hours).
- **Secondary target — `target_answered_7d`:** the question receives **any** answer within 7 days.
- **Review 1 research questions:** (RQ1) which structural characteristics predict 7-day resolution; (RQ2) how the picture changes when any answer counts instead of an accepted one; (RQ3) how volume, resolution rate and median hours-to-answer shifted across tags before and after November 2022.
- **Why this framing:** the two targets are reported together everywhere, because 76.0% of questions get an answer within 7 days but only 42.7% are accepted — acceptance depends on the asker coming back.

### Visual on Slide:
- Left: stakeholder strip — Q&A platform product team, developer-forum managers, DevRel teams.
- Right: two-box target diagram (`target_resolved_7d` 42.7% / `target_answered_7d` 76.0%). *Source: section `[M3-07]` of `03_eda.ipynb`.*

---

## Slide 2: Question Volume Collapsed After Late 2022
**Title (states the finding):** Weekly question volume fell by roughly 90% after November 2022 in every technology we track, with only a brief openai-api surge

### Key Bullet Points:
- **Uniform decline:** python, javascript, java, sql, pandas, reactjs and the rest all show a continuous fall in weekly volume from 2023 onward — this is not one tag losing share, it is the whole platform.
- **Milestone overlay:** Copilot GA (2022-06-21), ChatGPT launch (2022-11-30), Stack Overflow ChatGPT ban (2022-12-05), moderator strike (2023-06-05) are marked on every time axis so the reader can see where the break happens relative to each event.
- **AI interest was a spike, not a new baseline:** `openai-api` volume surges from late 2022 into mid-2023, peaks, then decays along with general activity; `fastapi` gains steady share against legacy frameworks.
- **The sampling caveat, stated up front:** 2019-2024 is roughly a 6.5-7.5% sample of days (1 weekday + 1 weekend day per tag-month); 2025 onward is a 100% census. Raw counts therefore **cannot** be compared across 2025 — every monthly rate in this deck is weighted.

### Visual on Slide:
- Left: 12-subplot log-scale small multiples of weekly volume by tag with milestone shading (volume-trends charts, issue #42).
- Right: `openai-api` versus site-wide share line, log scale. *Source: volume-trends charts in `03_eda.ipynb`.*

---

## Slide 3: Answers Still Arrive — They Just Arrive Slower and Get Accepted Less
**Title (states the finding):** Median time to accept rose from 0.84 to 2.60 hours and acceptance given an answer fell from 57.0% to 50.1% after November 2022

### Key Bullet Points:
- **Answered versus resolved:** 76.0% answered within 7 days, 42.7% accepted — the gap is the asker, not the community.
- **Pre/post comparison (weighted):** 7-day resolution 44.1% → 35.8%; 7-day answered 77.0% → 71.0%; `accepted_given_answered` 57.0% → 50.1%.
- **Latency:** median hours to accept went from about **50 minutes** to about **2.6 hours**; median time to first answer was stable under 1 hour before the cutoff and routinely exceeds 2.5-4 hours after it.
- **Distribution shape:** first answers pile up at near-zero log hours, while acceptances have a wide right tail — validation, not answering, is what got slower.
- **Tag variation:** powerbi and android show broader, slower accept distributions than pandas, html, python or javascript.
- **Association, not causation:** the decline is aligned with the post-2022 period; it is not proof that AI assistants caused it.

### Visual on Slide:
- Left: dual-target class balance stacked bars. Right: monthly weighted median response and resolution times with the cutoff line. *Source: sections `[M3-07]` and `[M3-08]` of `03_eda.ipynb`.*

---

## Slide 4: Who Actually Gets an Accepted Answer
**Title (states the finding):** Code blocks, short posts and established accounts resolve ~10 points more often than the alternatives

### Key Bullet Points:
- **Code helps:** questions containing code blocks resolve at about **43%** versus about **31%** without.
- **Error text hurts:** posts carrying exception or traceback text resolve at about **35%** against about **42%** without.
- **Length hurts:** under 500 characters resolves at about **43%**; over 3,000 characters falls to about **30%**.
- **Title phrasing is a weak signal:** leading "python" about 44%, "how" about 42%, first-person "i" about 32% — real, but small.
- **New accounts are penalised:** accounts under 7 days old resolve at about **33%** versus about **42%** once past that mark, and the rate then plateaus across 7-30 days, 30-365 days and over a year.
- **Timing matters operationally:** resolution peaks at **47.2%** late Saturday UTC (hour 21) and 46.8% early Sunday, against weekday lows near 38%.

### Visual on Slide:
- Left: resolution-rate bars by structural feature with absolute counts printed on each bar. Right: weighted 7x24 UTC weekday-by-hour heatmap. *Source: sections `[M3-09]` and `[M3-10]` of `03_eda.ipynb`.*

---

## Slide 5: What the Model Is Allowed to Use
**Title (states the finding):** Significance is guaranteed at n=302,026, so we hand over effect sizes and lagged features, not p-values

### Key Bullet Points:
- **Every feature is significant** (chi-square and Mann-Whitney, all $p < 0.001$) — at this sample size that tells us nothing on its own.
- **What separates signal from noise:** `answer_count` is the strongest correlate found (rank-biserial $-0.35$; Spearman $0.33$ resolved, $0.65$ answered), and it is **forbidden** as a feature because it is only known after answers arrive. Everything else is weak: Cramér's V below 0.11, absolute Spearman below 0.12.
- **The two targets are not independent** (Spearman $0.48$), so the secondary-target check is reported separately rather than as confirmation.
- **Feature hand-off to Member 4:** code and error flags, account-age bracket plus missing-age indicator, hour/weekday/month, **lagged** 4-week tag volume (past weeks only, never current), and title TF-IDF + SVD fitted on training splits only.
- **Business read:** prompt for code, route brand-new askers to first responders, and treat `accepted_given_answered` as a platform health KPI.

### Visual on Slide:
- Left: Spearman correlation heatmap of numeric features against both targets, with the forbidden `answer_count` row marked. Right: top-5 insight to feature mapping table. *Source: sections `[M3-11]` and `[M3-12]` of `03_eda.ipynb`.*

---

## Speaker Notes (2.5 Minutes Delivery)

### Slide 1 Delivery (~40 seconds)
> *"Our question is simple to state and hard to answer: developer question-and-answer activity is collapsing, and forum managers have no way to tell which questions still need a human expert. We built a dataset of Stack Overflow questions from January 2019 to August 2026 and we predict one thing — whether a question gets an accepted answer within seven days. We deliberately track a second target as well, any answer within seven days, because 76% of questions get an answer but only 43% are accepted, and that gap is the asker rather than the community."*

### Slide 2 Delivery (~35 seconds)
> *"The headline context: weekly question volume fell by around 90% after late 2022, and it fell in every language and framework we track, not just in one place. We mark four dated events on every chart so you can see the break relative to Copilot, ChatGPT, the Stack Overflow ban on AI answers, and the moderator strike. One methodological point I want to be explicit about: before 2025 we sampled about 7% of days, from 2025 we collect every day, so raw counts are not comparable across that line — every monthly rate I show is weighted."*

### Slide 3 Delivery (~35 seconds)
> *"Answers still arrive — 76% within seven days — but they arrive later and they are accepted less often. Median time to accept went from about fifty minutes to about two and a half hours, and the share of answered questions that get accepted fell from 57% to 50%. The shape of the distribution is the interesting part: first answers cluster near zero, acceptances have a long tail, so what slowed down is validation, not answering. And to be careful, this is aligned with the post-2022 period; it is not proof of cause."*

### Slide 4 Delivery (~35 seconds)
> *"Who gets answered is fairly predictable. Questions with code blocks resolve about 43% of the time versus 31% without. Posts with error text do worse, about 35%. Shorter posts do better: 43% under 500 characters, 30% above 3,000. Brand-new accounts — under a week old — resolve at 33% versus 42% after that, and the rate then plateaus. Timing is operational rather than technical: resolution peaks on a Saturday night at 47% and dips to 38% on weekday mornings."*

### Slide 5 Delivery (~35 seconds)
> *"Finally, what I hand to the modelling side. With 302,026 rows every feature is significant, so p-values are worthless here and I report effect sizes instead. The strongest correlate in the whole dataset is answer count — and it is banned as a feature, because it only exists after answers arrive; that was the one leakage trap I had to argue for. Everything else is weak on its own, which is why the hand-off is a set of lagged and structural features rather than a single magic variable. Member 1 will now take you through how the data was collected and verified."*