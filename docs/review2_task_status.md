# M2/M5 status and remaining handoffs

Owner branches are `m2/review2-text-mining` for Rishiikesh first and `m5/review2-forecasting` for Adhikkesh after the M2 PRs are merged. Commit identities have not been changed; no files are staged or committed.

| Plan task | Implementation/result | Remaining input |
|---|---|---|
| M5-20 series preparation and superseded Review 1 note | Complete: series_long.csv, monthly_rates_masked.csv and superseded note | M3 review/actual PR evidence |
| M5-21 baselines, backtest, metrics and tests | Complete: ts_forecast.py; contract tests | M3 review |
| M5-22 damped ETS and intervention SARIMAX | Complete: training-only AIC and 2024 H2 selection | M3 review |
| M5-23 backtest, matched tables, DM, ACF/Ljung–Box | Complete: outputs for 14 series with failed fits reported | M3 review |
| M5-24 forecasts, classes, half-life, load index | Forecasts complete; zero-baseline classes explicitly undefined | M3 ITS estimates for the integrated class/slope presentation |
| M5-25 GRU appendix | Optional; not run or represented as completed | Only run later if needed on the same backtest |
| M5-26 notebook Part B | Complete after real nbconvert execution | M3 adds Part A; M1 integrates final notebook |
| M5-27 Forecasts-page handoff | Complete: data schemas, files and captions | M1 wires dashboard; optional classifier check needs M4 train-only topic features |
| M5-28 slides, findings, summary, viva | Complete after slides are generated and visually checked | Owner rehearsal and actual commit/PR/reviewer links |
| M2-20 corpus, sample, written rules and tests | Complete after full corpus run; checked at 302,026 questions | M4 review |
| M2-21 VADER, technical overrides, phrase flags and monthly shares | Complete; explicitly exploratory | Human validation before claiming classifier quality |
| M2-22 independent tone validation | Code, 200-question sheet and label rule complete | M2 and M3 independent labels and agreed labels are required; no invented accuracy/F1/kappa |
| M2-23 complexity and weighted 95% intervals | Complete: monthly tables and 1,000-question-bootstrap pre/post intervals | M4 review |
| M2-24 second rater for topic names | Cannot begin before M4 topic terms/examples | Nishanth’s trained topics and linked examples |
| M2-25 tone-resolution regression and five findings | Complete: weighted association controlling tag/year; findings label tone as exploratory | Human labels affect validation claims |
| M2-26 notebook Part A | Complete after real nbconvert execution | M4 adds Part B; M1 integrates final notebook |
| M2-27 dashboard page 5 handoff | Complete: files, schemas and captions | M1 wires dashboard; M4 supplies keyword file |
| M2-28 slides, summary and viva | Complete after slides are generated and checked | Human validation numbers must be refreshed later; owner rehearsal |

This document distinguishes implemented local work from reviews and human/other-member inputs. Topic agreement, human tone labels, deployed dashboard, combined report and the complete team notebook are not claimed as finished here.
