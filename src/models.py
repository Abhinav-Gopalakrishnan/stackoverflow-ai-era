"""Random Forest and gradient boosting inside one scikit-learn pipeline shape.

M5-02 skeleton, extended for M5-07 and M5-08. The pipeline is
``Pipeline([("prep", preprocessor), ("model", estimator)])``. Member 4's saved
preprocessing pipeline (scaling, TF-IDF + SVD) can be passed as ``preprocessor``;
until then ``build_preprocessor`` gives the same shape for the structured features.

Imbalance: Random Forest uses ``class_weight``; XGBoost and LightGBM use
``scale_pos_weight`` = negatives / positives of the training labels.
"""

from __future__ import annotations

import os

import numpy as np
import pandas as pd
from scipy.stats import loguniform, randint
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import TruncatedSVD
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import RandomizedSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.timecv import GAP_DAYS, time_series_folds

NUMERIC_FEATURES = ["title_length", "body_length", "n_code_blocks", "code_ratio", "tag_count",
                    "hour_posted", "weekday_posted", "month_posted", "account_age_days",
                    "other_tags_count", "lagged_tag_volume", "lagged_tag_change"]
BINARY_FEATURES = ["has_error_text", "missing_account_age", "new_account"]
CATEGORICAL_FEATURES = ["question_word"]
FEATURES = NUMERIC_FEATURES + BINARY_FEATURES + CATEGORICAL_FEATURES
TEXT_COLUMN = "title"
KINDS = ("rf", "xgb", "lgbm")           # tree models tuned in M5-07 / M5-08
ALL_KINDS = KINDS + ("logreg",)         # plus the logistic-regression baseline
N_JOBS = int(os.environ.get("M5_JOBS", min(4, os.cpu_count() or 1)))  # all threads can be slower on small data

SEARCH_SPACES = {
    # M5-07: number of trees, depth, minimum leaf size
    "rf": {"model__n_estimators": randint(100, 500),
           "model__max_depth": [6, 10, 16, 24, None],
           "model__min_samples_leaf": randint(1, 60)},
    # M5-08: learning rate, depth, number of trees
    "xgb": {"model__learning_rate": loguniform(0.02, 0.3),
            "model__max_depth": randint(3, 10),
            "model__n_estimators": randint(100, 600)},
    "lgbm": {"model__learning_rate": loguniform(0.02, 0.3),
             "model__max_depth": randint(3, 12),
             "model__n_estimators": randint(100, 600)},
}


class TitleSVD(TruncatedSVD):
    """TruncatedSVD whose output columns are named ``title_tfidf_svd_<i>`` (as in the spec)."""

    def get_feature_names_out(self, input_features=None):
        return np.array([f"title_tfidf_svd_{i}" for i in range(self.n_components)])


def feature_lists(df):
    """Numeric, binary and categorical feature names present in ``df``.

    Lagged tag volume is included only if the columns exist; the multi-hot ``tag_*``
    columns are picked up automatically.
    """
    numeric = [c for c in NUMERIC_FEATURES if c in df.columns]
    binary = [c for c in BINARY_FEATURES if c in df.columns] + \
             sorted(c for c in df.columns if c.startswith("tag_") and c not in NUMERIC_FEATURES)
    return numeric, binary, [c for c in CATEGORICAL_FEATURES if c in df.columns]


_DEVICE_CACHE = []


def xgb_device():
    """``"cuda"`` if a GPU is usable for XGBoost, else ``"cpu"``.

    Controlled by the ``M5_DEVICE`` environment variable: ``auto`` (default: use a GPU if one
    works), ``cuda`` or ``cpu``. A tiny test fit decides, so a missing or unusable GPU quietly
    falls back to the CPU. Only XGBoost uses the GPU; Random Forest, TF-IDF and SVD run on the CPU.
    """
    if _DEVICE_CACHE:
        return _DEVICE_CACHE[0]
    want = os.environ.get("M5_DEVICE", "auto").lower()
    device = "cpu"
    if want in ("auto", "cuda"):
        try:
            import shutil
            import subprocess

            from xgboost import XGBClassifier, build_info

            # XGBoost accepts device="cuda" even without a GPU, so check the driver and the build too
            if not shutil.which("nvidia-smi") or subprocess.run(
                    ["nvidia-smi"], capture_output=True).returncode != 0:
                raise RuntimeError("no NVIDIA GPU found")
            if not build_info().get("USE_CUDA"):
                raise RuntimeError("this XGBoost build has no CUDA support")
            XGBClassifier(device="cuda", n_estimators=1, tree_method="hist").fit(
                np.zeros((4, 2)), [0, 1, 0, 1])
            device = "cuda"
        except Exception as error:  # no GPU, no CUDA build, driver problems
            if want == "cuda":
                print(f"WARNING: M5_DEVICE=cuda but the GPU is not usable ({str(error)[:80]}); using the CPU")
    _DEVICE_CACHE.append(device)
    return device


def build_preprocessor(numeric=NUMERIC_FEATURES, binary=BINARY_FEATURES,
                       categorical=CATEGORICAL_FEATURES, text=None, svd_components=100,
                       max_features=5000):
    """Scale numeric, pass binary, one-hot categorical; fitted on training data only.

    With ``text="title"`` the title is also vectorised (TF-IDF on unigrams and bigrams,
    up to ``max_features`` terms) and reduced with TruncatedSVD to ``svd_components``.
    Because it is a pipeline step, it is refitted on the training rows of every fold.
    """
    parts = [("num", StandardScaler(), list(numeric)),
             ("bin", "passthrough", list(binary)),
             ("cat", OneHotEncoder(handle_unknown="ignore"), list(categorical))]
    if text:
        parts.append(("text", Pipeline([
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_features=max_features,
                                      min_df=5, sublinear_tf=True)),
            ("svd", TitleSVD(n_components=svd_components, n_iter=4, random_state=42))]), text))
    return ColumnTransformer(parts, verbose_feature_names_out=False)


def scale_pos_weight(y):
    """Negatives / positives, for XGBoost and LightGBM."""
    y = np.asarray(y)
    return float((y == 0).sum() / max((y == 1).sum(), 1))


def _estimator(kind, y_train=None, random_state=42, **params):
    """Estimator with sensible defaults; ``params`` override them."""
    if kind == "logreg":
        defaults = dict(class_weight="balanced", max_iter=2000, C=1.0)
        return LogisticRegression(**{**defaults, **params})
    if kind == "rf":
        defaults = dict(n_estimators=200, min_samples_leaf=5, n_jobs=N_JOBS,
                        class_weight="balanced_subsample", random_state=random_state)
        return RandomForestClassifier(**{**defaults, **params})
    weight = 1.0 if y_train is None else scale_pos_weight(y_train)
    defaults = dict(n_estimators=300, learning_rate=0.1, n_jobs=N_JOBS, scale_pos_weight=weight,
                    random_state=random_state)
    if kind == "xgb":
        from xgboost import XGBClassifier

        defaults.update(max_depth=6, eval_metric="aucpr", tree_method="hist", device=xgb_device())
        return XGBClassifier(**{**defaults, **params})
    if kind == "lgbm":
        from lightgbm import LGBMClassifier

        defaults.update(max_depth=-1, verbose=-1)
        return LGBMClassifier(**{**defaults, **params})
    raise ValueError(f"kind must be one of {ALL_KINDS}")


def build_pipeline(kind, y_train=None, preprocessor=None, random_state=42, memory=None, **params):
    """Fresh, unfitted ``Pipeline([("prep", ...), ("model", ...)])``.

    ``memory`` (a directory) caches the fitted preprocessing step, so a search over
    model settings does not refit TF-IDF + SVD for every candidate.
    """
    prep = preprocessor if preprocessor is not None else build_preprocessor()
    return Pipeline([("prep", prep),
                     ("model", _estimator(kind, y_train, random_state, **params))], memory=memory)


def fit_pipeline(pipe, X, y, sample_weight=None):
    """Fit, passing ``sampling_weight`` to the estimator only."""
    if sample_weight is None:
        return pipe.fit(X, y)
    return pipe.fit(X, y, model__sample_weight=np.asarray(sample_weight))


def predict_score(pipe, X):
    """Predicted probability of the positive class (resolved)."""
    return pipe.predict_proba(X)[:, 1]


def majority_scores(y_train, n):
    """Constant score for the majority-class baseline."""
    return np.full(n, float(np.mean(y_train)))


def tune(kind, X, y, dates, n_iter=20, n_splits=5, gap_days=GAP_DAYS, sample_weight=None,
         preprocessor=None, scoring="average_precision", random_state=42, n_jobs=1, memory=None):
    """RandomizedSearchCV with date-based time-series folds (training period only).

    ``dates`` must align row by row with ``X``. Returns the fitted search; the
    best parameters are in ``search.best_params_``.
    """
    folds = time_series_folds(dates, n_splits, gap_days)
    pipe = build_pipeline(kind, y, preprocessor, random_state, memory)
    search = RandomizedSearchCV(pipe, SEARCH_SPACES[kind], n_iter=n_iter, cv=folds,
                                scoring=scoring, refit=True, random_state=random_state,
                                n_jobs=n_jobs)
    if sample_weight is None:
        return search.fit(X, y)
    return search.fit(X, y, model__sample_weight=np.asarray(sample_weight))


def fit_with_early_stopping(kind, X_train, y_train, X_val, y_val, preprocessor=None,
                            rounds=50, sample_weight=None, random_state=42, **params):
    """XGBoost or LightGBM with early stopping on the validation period (M5-08)."""
    if kind not in ("xgb", "lgbm"):
        raise ValueError("early stopping applies to xgb and lgbm only")
    prep = (preprocessor if preprocessor is not None else build_preprocessor()).fit(X_train)
    model = _estimator(kind, y_train, random_state, **params)
    Xt, Xv = prep.transform(X_train), prep.transform(X_val)
    weight = None if sample_weight is None else np.asarray(sample_weight)
    if kind == "xgb":
        model.set_params(early_stopping_rounds=rounds)
        model.fit(Xt, y_train, sample_weight=weight, eval_set=[(Xv, y_val)], verbose=False)
        best = int(model.best_iteration) + 1
    else:
        import lightgbm as lgb

        model.fit(Xt, y_train, sample_weight=weight, eval_X=Xv, eval_y=y_val,
                  eval_metric="average_precision",
                  callbacks=[lgb.early_stopping(rounds, verbose=False)])
        best = int(model.best_iteration_)
    return Pipeline([("prep", prep), ("model", model)]), best


GOOD_WORDS = ["dataframe", "merge", "regex", "groupby", "pivot", "typeerror", "index", "loop"]
FILLER_WORDS = ["code", "work", "value", "list", "file", "data", "function", "string", "class",
                "output", "result", "problem", "get", "use", "change", "run"]


def make_synthetic_weekly(tags, seed=42):
    """Weekly counts (tag, week_start, count) in 7-day steps from 2019-01-01, with an ALL row."""
    rng = np.random.default_rng(seed)
    weeks = pd.date_range("2019-01-01", "2026-08-31", freq="7D")
    decline = 1 - 0.5 * (weeks >= pd.Timestamp("2022-11-30")) * np.minimum(
        1, (weeks - pd.Timestamp("2022-11-30")).days / 700)
    rows = []
    for i, tag in enumerate(list(tags) + ["ALL"]):
        level = 30000 if tag == "ALL" else 3000 + 700 * i
        counts = (level * decline * rng.normal(1, 0.05, len(weeks))).round().astype(int)
        rows += list(zip([tag] * len(weeks), weeks, counts))
    return pd.DataFrame(rows, columns=["tag", "week_start", "count"])


def make_synthetic_clean(n=4000, seed=42, tags=None):
    """Synthetic table with the cleaned-dataset columns, for tests and dry runs only.

    Resolution depends on code ratio, error text, account age, body length and a few
    title words; the effect of error text weakens after November 2022 so rolling-origin
    code has something to detect. Never use its numbers as results.
    """
    tags = tags or ["python", "javascript", "java", "sql", "pandas", "reactjs", "android",
                    "excel", "r", "docker", "powerbi", "fastapi", "openai-api"]
    rng = np.random.default_rng(seed)
    start, end = pd.Timestamp("2019-01-01", tz="UTC"), pd.Timestamp("2026-07-31", tz="UTC")
    created = start + pd.to_timedelta(np.sort(rng.uniform(0, (end - start).total_seconds(), n)),
                                      unit="s")
    post_ai = (created >= pd.Timestamp("2022-11-30", tz="UTC")).astype(float)
    n_good = rng.integers(0, 3, n)
    titles = [" ".join(rng.choice(GOOD_WORDS, g).tolist() + rng.choice(FILLER_WORDS, rng.integers(2, 8)).tolist())
              for g in n_good]
    tag_lists = [list(rng.choice(tags, rng.integers(1, 3), replace=False))
                 + (["numpy"] if rng.random() < 0.3 else []) for _ in range(n)]
    df = pd.DataFrame({
        "question_id": np.arange(100000, 100000 + n),
        "created_at": created,
        "title": [("How to " if rng.random() < 0.5 else "") + t for t in titles],
        "tags": tag_lists,
        "n_code_blocks": rng.poisson(1.5, n),
        "code_ratio": rng.beta(2, 5, n),
        "account_age_days": rng.exponential(900, n),
        "has_error_text": rng.binomial(1, 0.3, n).astype(bool),
        "missing_account_age": rng.binomial(1, 0.05, n).astype(bool),
    })
    df["plain_body"] = ["x" * int(m) for m in rng.integers(30, 3000, n)]
    logit = (-2.4 + 1.5 * df["has_error_text"] * (1 - 0.7 * post_ai) + 3.0 * df["code_ratio"]
             + 0.8 * (df["n_code_blocks"] > 0) - 1.0 * (df["account_age_days"] <= 7)
             - 1.0 * (df["plain_body"].str.len() < 400) + 0.7 * n_good + rng.normal(0, 0.3, n))
    df["target_resolved_7d"] = rng.binomial(1, 1 / (1 + np.exp(-logit)))
    df["target_answered_7d"] = np.maximum(df["target_resolved_7d"], rng.binomial(1, 0.6, n))
    df["sampling_weight"] = np.where(created < pd.Timestamp("2025-01-01", tz="UTC"), 4.0, 1.0)
    return df


def make_synthetic_data(n=4000, seed=42):
    """Synthetic feature frame (see ``make_synthetic_clean``), built with ``build_features``."""
    from src.build_features import build_features

    clean = make_synthetic_clean(n, seed)
    return build_features(clean, make_synthetic_weekly(clean.attrs.get("tags") or [
        "python", "javascript", "java", "sql", "pandas", "reactjs", "android", "excel", "r",
        "docker", "powerbi", "fastapi", "openai-api"], seed))
