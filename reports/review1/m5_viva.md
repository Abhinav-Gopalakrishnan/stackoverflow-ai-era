# Member 5: viva questions for models, evaluation and findings (M5-VIVA)

Short answers in plain words. The numbers to quote are in `reports/review1/m5/results.json` and the slides.

**1. Is an accepted answer within 7 days the same as resolved?**
No. Acceptance depends on the asker coming back to click accept, so it is a strict proxy. We also model the secondary target (any answer within 7 days) as a check, and our EDA tracks acceptance among answered questions over time.

**2. How did you tune the decision threshold without touching the test set?**
On the validation period only (Jan to Jun 2025), by maximising F1. The test period (Jul 2025 to Jul 2026) was scored once, afterwards, with that frozen threshold. The code refuses a second test run.

**3. How can you compare pre- and post-AI performance if the whole test set is post-AI?**
With rolling-origin evaluation: for each half-year from 2021 H1 to 2026 H1 we train on everything before it (leaving a 7-day gap) and test on that half-year. Ranking quality is stable across November 2022 (mean ROC-AUC 0.64 before, 0.65 after). PR-AUC falls (0.56 to 0.47), but so does the share of questions that get resolved (42% to 33%), and PR-AUC depends on that share; PR-AUC minus the share is 0.14 both before and after. So the model's skill did not change; what changed is how often questions are resolved. We say "associated with", not "caused by".

**4. Why PR-AUC and not accuracy?**
Accuracy hides how the model treats each class and depends on the class balance and on one threshold. PR-AUC looks at precision against recall across all thresholds, so it compares models fairly. We report precision, recall, F1, ROC-AUC and a confusion matrix next to it; accuracy is never reported alone.

**5. How did you handle class imbalance?**
Class weights for Random Forest and logistic regression, `scale_pos_weight` for XGBoost, and PR-AUC as the selection metric. We did not resample, so the test distribution stays realistic.

**6. Why time-series folds and a 7-day gap?**
A random split would let the model learn from the future to predict the past. Folds are cut by date, training always precedes testing, and we drop the 7 days before each boundary because a label is only known 7 days after posting.

**7. What does the capture rate mean for a manager?**
If the team can only act on 20% of questions, flag the 20% with the lowest predicted resolution. The capture rate is the share of all unresolved questions that fall inside that flagged group; random flagging would capture 20%.

**8. How do you know there is no leakage?**
Features are only what is known at posting time. `src/leakage.py` fails on any outcome field, post-posting field, `sampling_weight`, identifier or raw timestamp. Title text (TF-IDF and SVD) is fitted inside the pipeline on training data only, and lagged tag volume uses only complete weekly counts from before the posting week; I cross-checked it against an independent implementation.

**9. What do SHAP values tell you that logistic regression coefficients do not?**
SHAP shows how each feature moves the prediction for each question in a non-linear model, so we can see direction and interactions. The coefficients are one global slope per feature. We compare the two to check the main drivers agree.

**10. What are the limits of the model?**
Acceptance is a proxy for resolved, recent data is smaller than the sampled early years, only 13 tags are covered, and the model predicts association, not cause. A manager should use the score to prioritise, not as a verdict.

**11. The gains look small. Is the model useful?**
Modestly. On the test period the model reaches PR-AUC 0.43 where a no-skill ranking gets 0.30 (the share resolved), and ROC-AUC 0.65. Flagging the 20% of questions with the lowest predicted resolution catches 24% of the unresolved ones against 20% at random, a 1.2x lift. The three real models differ by about 0.01 PR-AUC on validation (logistic regression 0.471, Random Forest 0.473, XGBoost 0.482). We report this honestly: the score can help prioritise, not decide.

**12. Tag volume is the top SHAP feature. Is that leakage?**
No: it uses only the complete weekly counts from the four weeks before the posting week, and I checked it against an independent implementation. But it works largely as a stand-in for which tag and which period a question belongs to (volume has fallen since 2022 and busy tags are resolved less often), so we do not read it as a property of the question.

**13. Member 4's baseline has 64% accuracy. Is that good?**
No. Only 34% of validation questions are resolved, so always predicting "unresolved" has 66% accuracy, which is higher. Under the shared metrics their model has PR-AUC 0.394 against 0.341 for no skill and ROC-AUC 0.579. That is why accuracy is never reported alone.

**14. What did the error analysis show?**
Of 15 confident false positives, 10 were answered (often within minutes) but never accepted, 4 had no answer in a niche area, and 1 was accepted 4 hours after the 7-day cut-off. Of 15 false negatives, 8 came from brand-new accounts that returned and were accepted within hours (7 of 8 within 4 hours). One miss came from a case-sensitive error-text pattern, which is a feature limitation.

**15. Your SHAP plots show error text going with fewer accepted answers. Why not tell askers to add error text?**
Because the association points the other way in the test period: questions with error text are accepted less often, and the logistic regression agrees. It is an association, not proof of cause, so the advice we give is to add code to the question, which is associated with more accepted answers up to a point.

## Numbers to quote
- Data: 293,510 modelled questions (302,026 cleaned minus 8,516 early-2019 questions with no weekly history); train 248,294, validation 28,132, test 16,695.
- Share resolved: 42% train, 34% validation, 30% test.
- Validation PR-AUC: majority 0.341, Member 4 logistic regression 0.394, logistic regression (my features) 0.471, Random Forest 0.473, XGBoost 0.482. Title text adds +0.027 PR-AUC to logistic regression.
- Chosen: XGBoost, 628 trees (early stopping), threshold 0.367 tuned on validation.
- Test (once): precision 0.363, recall 0.771, F1 0.493, PR-AUC 0.431, ROC-AUC 0.655, capture rate 24.1% (lift 1.21x).
- Secondary target (any answer in 7 days): ROC-AUC 0.667 vs 0.655 for the main target.
