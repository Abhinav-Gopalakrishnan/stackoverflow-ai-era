# Error analysis: 30 confident errors on the test period (M5-14)

Method: `docs/error_analysis_design.md`. From the test period (Jul 2025 to Jul 2026, 16,695 questions) the XGBoost model's most confident errors were sampled: 15 false positives (predicted resolved, actually not accepted within 7 days) and 15 false negatives (predicted unresolved, actually accepted within 7 days). Each question was read at its link and given one main reason (`error_annotation_sheet.csv`, columns `likely_reason` and `evidence`). Titles only are shown, each linked to the original question (CC BY-SA 4.0).

## Reasons found

| Error type | Main reason | Count |
|---|---|---|
| False positive | Answered but not accepted | 10 |
| False positive | No answer received (niche database or library) | 4 |
| False positive | Accepted 4 hours after the 7-day cut-off (172 h) | 1 |
| False negative | New asker account (0 days old), accepted within hours | 8 |
| False negative | No code block | 2 |
| False negative | Android tag together with error text | 2 |
| False negative | Long body with error text | 1 |
| False negative | Error text not detected by the feature | 1 |
| False negative | High-visibility question without code (41,576 views) | 1 |

## Patterns

1. **False positives are mostly about the asker, not the question.** 10 of 15 got answers, many within minutes, but the asker never accepted one. Acceptance depends on the asker returning, and nothing the model sees at posting time describes that. This is the same limit as using acceptance as a proxy for resolved. 4 more had no answer at all and were niche (GridDB, DolphinDB, a BSON library question). One was accepted 4 hours after the 7-day cut-off, a boundary effect of the 168-hour rule.
2. **False negatives are mostly brand-new accounts.** 8 of 15 were asked by accounts created the same day, and 7 of those 8 were accepted within 4 hours. The model has learned that new accounts are accepted less often, and its overall error rate for new accounts is lower than for other askers (0.31 against 0.50), but the new askers who do come back resolve fast.
3. **Feature limits show up.** One false negative contains "Fatal error in launcher" but the error-text pattern is case-sensitive (`Error:`), so `has_error_text` was 0. Questions without a code block, or with an android tag plus error text, were pushed down although they were resolved.
4. **Visibility is not available at posting time.** The most viewed false negative (41,576 views, score 23) was resolved because it became popular, which a posting-time model cannot know.

## What would help (not done in Review 1)
- Make the error-text pattern case-insensitive and add "exception" and "fatal" variants.
- Add asker-history features if they can be obtained without leakage (a new account that returns is the missing signal).
- Treat answers accepted just after 168 hours with a sensitivity check on the window length.

All of these are associated patterns in 30 examples, not proof of cause. The `auto_hint` column in the sheet is the earlier rule-based guess; the reasons above were assigned after reading each question.
