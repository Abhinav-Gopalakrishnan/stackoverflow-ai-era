# Model findings (Member 5 section for `initial_findings.md`)

**What the model offers a support-forum manager.** A xgboost model, trained on questions up to December 2024 and scored once on 16,695 questions from July 2025 to July 2026, ranks questions by their chance of getting an accepted answer within 7 days (PR-AUC 0.43, ROC-AUC 0.65).

1. **Flagging 20% of questions catches 24% of the unresolved ones** (1.2 times better than random flagging at 20%). Stakeholder: support-forum manager. Action: route the lowest-scored questions to experts.
2. **The strongest signals are tag volume in the previous 4 weeks, asker account age, share of code in the body.** Stakeholder: community or product team. Action: prompt askers to add code or error text before posting.
3. **Accuracy differs before and after November 2022.** Mean rolling-origin PR-AUC is 0.56 before and 0.47 after, across 11 half-year windows; this is associated with, not proof of, a change in how questions are resolved. Stakeholder: analytics lead. Action: retrain regularly rather than keep one fixed model.
4. **The result holds for a second target.** Predicting any answer within 7 days gives PR-AUC 0.83 (accepted answer: 0.43).

**Limits.** An accepted answer within 7 days is a strict proxy for resolved because it depends on the asker returning. Recent data (2025 onwards) is smaller than the sampled early years. Only 13 tags are covered. AI-related statements say 'associated with' or 'consistent with', never 'caused'.
