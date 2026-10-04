# Error Analysis Design (M5-04)

Goal: understand *why* the final model is confidently wrong, using 30 hand-annotated errors from the test period. Code: `src/error_analysis.py`.

## Sampling method

1. Take the final model's predictions on the **test period**, with the threshold tuned on validation.
2. **False positive** = predicted resolved (`p >= threshold`) but actually unresolved. **False negative** = predicted unresolved (`p < threshold`) but actually resolved.
3. Confidence = distance of the predicted probability from the threshold. Rank each error type by confidence, highest first.
4. Keep the top 25% of each ranked list (at least 15 rows) as the pool, then draw **15 at random** from each pool with seed 42. Total: 15 false positives + 15 false negatives.
5. Run once after the final test evaluation. The sample is for explanation only; nothing is tuned from it.

Why confident errors: borderline errors are noise. Errors the model is sure about point to a missing signal or a systematic pattern.

## Annotation sheet

One row per sampled question, written with `write_annotation_sheet`:

| Column | Content |
|---|---|
| `error_type` | false_positive or false_negative |
| `question_id` | for lookup |
| `title` | question title (title only, see licence) |
| `tags` | tags, `;`-separated |
| `predicted_probability` | model's probability of resolved |
| `actual_outcome` | resolved or unresolved |
| `link` | `https://stackoverflow.com/q/<question_id>` |
| `likely_reason` | filled in by hand |

Fill `likely_reason` after reading the question at its link. Use short, repeatable labels (for example: "very short title", "rare tag", "no code or error text", "asker never returned", "answer given but not accepted", "duplicate or off-topic") so patterns can be counted.

## Summarising patterns

- `summarise_reasons(sheet)`: counts of each reason by error type.
- `error_rate_by(df, y, p, threshold, column, bins)`: error rate by title length band, tag count, code present, etc., to check whether a hand-found pattern holds across the whole test set, not just the 30.

## Licence and ethics

Stack Overflow content is CC BY-SA 4.0. The sheet and any slide show **titles only, each linked to the original question**, with a licence notice. Raw question text is never published; user IDs are not included.
