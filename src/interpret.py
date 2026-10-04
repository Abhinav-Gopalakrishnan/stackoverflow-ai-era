"""SHAP interpretation for fitted tree pipelines (M5-11, M5-12).

Works on a ``Pipeline([("prep", ...), ("model", tree_model)])`` as built in
``src/models.py``. SHAP values are for the positive class (resolved): a
positive value pushes the question towards "resolved".
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def shap_frame(pipe, X, max_rows=2000, seed=42):
    """Return ``(shap_df, features_df)`` on a random sample of ``X``, columns = prepared features."""
    import shap

    if len(X) > max_rows:
        X = X.sample(max_rows, random_state=seed)
    prep, model = pipe[:-1], pipe.steps[-1][1]
    Xt = prep.transform(X)
    if hasattr(Xt, "toarray"):
        Xt = Xt.toarray()
    names = list(prep.get_feature_names_out())
    values = shap.TreeExplainer(model).shap_values(Xt)
    if isinstance(values, list):
        values = values[-1]
    values = np.asarray(values)
    if values.ndim == 3:  # (rows, features, classes) -> positive class
        values = values[:, :, -1]
    return (pd.DataFrame(values, columns=names, index=X.index),
            pd.DataFrame(Xt, columns=names, index=X.index))


def top_features(shap_df, k=5):
    """Mean absolute SHAP value of the ``k`` most important features."""
    return shap_df.abs().mean().sort_values(ascending=False).head(k)


def compare_top_features(tables, k=5):
    """Rank of each feature in each window or target.

    ``tables`` maps a name (e.g. ``"2021 H2"``, ``"2025 H2"``) to a ``shap_df``.
    Returns features in the top ``k`` of any table, with ranks (NaN = outside the top ``k``).
    """
    ranks = {}
    for name, shap_df in tables.items():
        top = top_features(shap_df, k)
        ranks[name] = pd.Series(range(1, len(top) + 1), index=top.index)
    return pd.DataFrame(ranks).sort_values(list(ranks), na_position="last")


def plot_summary(shap_df, features_df, path=None):
    """SHAP summary (beeswarm) plot."""
    import matplotlib.pyplot as plt
    import shap

    shap.summary_plot(shap_df.to_numpy(), features_df, show=False)
    fig = plt.gcf()
    fig.tight_layout()
    if path:
        fig.savefig(path, dpi=120, bbox_inches="tight")
    return fig


def plot_dependence(shap_df, features_df, features, path=None):
    """One SHAP dependence plot per feature in ``features``."""
    import matplotlib.pyplot as plt
    import shap

    fig, axes = plt.subplots(1, len(features), figsize=(4.5 * len(features), 3.8), squeeze=False)
    for ax, name in zip(axes[0], features):
        shap.dependence_plot(name, shap_df.to_numpy(), features_df, interaction_index=None,
                             ax=ax, show=False)
    fig.tight_layout()
    if path:
        fig.savefig(path, dpi=120, bbox_inches="tight")
    return fig
