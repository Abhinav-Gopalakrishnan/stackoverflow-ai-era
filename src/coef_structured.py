"""Interpretable logistic-regression coefficients on the structured features (M4-12 stand-in).

The coefficient table from the full model is dominated by anonymous title-text components.
This fits the same class-weighted logistic regression on the structured features only
(numeric features standardised, so coefficients are comparable) and lists the largest
positive and negative ones in plain words.

    python -m src.coef_structured     # writes reports/review1/m5/logreg_coefficients_structured.csv
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src import models
from src.build_features import build_features
from src.run_models import TARGET, WEIGHT, split_by_date

NAMES = {
    "title_length": "title length", "body_length": "body length", "n_code_blocks": "number of code blocks",
    "code_ratio": "share of code in the body", "tag_count": "number of tags", "hour_posted": "hour posted",
    "weekday_posted": "weekday posted", "month_posted": "month posted", "account_age_days": "asker account age",
    "other_tags_count": "number of other tags", "lagged_tag_volume": "tag volume in the previous 4 weeks",
    "lagged_tag_change": "change in tag volume", "has_error_text": "error text in the question",
    "missing_account_age": "deleted asker account", "new_account": "account created within 7 days of posting",
}


def plain(feature, coefficient):
    name = NAMES.get(feature)
    if name is None and feature.startswith("tag_"):
        name = f"question tagged {feature[4:]}"
    if name is None and feature.startswith("question_word_"):
        name = f"title starts with '{feature[14:]}'"
    name = name or feature
    more = coefficient > 0
    if feature in ("has_error_text", "missing_account_age", "new_account") or feature.startswith(("tag_", "question_word_")):
        return f"{name}: {'more' if more else 'less'} likely to be resolved"
    return f"higher {name}: {'more' if more else 'less'} likely to be resolved"


def run(data="data/processed/questions_clean_v1.parquet", weekly="data/processed/weekly_counts.csv",
        out="reports/review1/m5/logreg_coefficients_structured.csv", k=15):
    feat = build_features(pd.read_parquet(data), pd.read_csv(weekly))
    train, _, _ = split_by_date(feat)
    numeric, binary, categorical = models.feature_lists(train)
    cols = numeric + binary + categorical
    pipe = models.fit_pipeline(models.build_pipeline("logreg", train[TARGET], models.build_preprocessor(numeric, binary, categorical)),
                               train[cols], train[TARGET], train[WEIGHT])
    coef = pd.Series(pipe.steps[-1][1].coef_[0], index=pipe[:-1].get_feature_names_out()).sort_values()
    table = pd.concat([coef.tail(k)[::-1].to_frame("coefficient").assign(direction="positive"),
                       coef.head(k).to_frame("coefficient").assign(direction="negative")])
    table["in_plain_words"] = [plain(f, c) for f, c in zip(table.index, table["coefficient"])]
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    table.round(4).to_csv(out)
    return table


if __name__ == "__main__":
    print(run().round(3).to_string())
