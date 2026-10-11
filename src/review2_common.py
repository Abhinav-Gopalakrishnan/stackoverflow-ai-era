"""Shared, reproducible definitions for the M2/M5 Review 2 handoffs."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TEXT = ROOT / 'reports/review2/text'
TS = ROOT / 'reports/review2/ts'
SEED = 42

def period(dates):
    d = pd.to_datetime(dates, utc=True)
    return np.where(d < pd.Timestamp('2022-11-01', tz='UTC'), 'pre',
                    np.where(d < pd.Timestamp('2023-01-01', tz='UTC'), 'transition', 'post'))

def write_json(path, obj):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, default=str, allow_nan=False) + '\n')

def question_meta(q):
    d = q[['question_id', 'created_at', 'tags', 'sampling_weight', 'target_resolved_7d']].copy()
    d['created_at'] = pd.to_datetime(d.created_at, utc=True)
    d['period'] = period(d.created_at)
    d['month'] = d.created_at.dt.strftime('%Y-%m')
    return d

def study_groups(d):
    """Full tags, restricted to study tags; ALL includes each question exactly once."""
    import yaml
    tags = yaml.safe_load((ROOT / 'config.yaml').read_text())['study']['tags']
    all_rows = d.copy(); all_rows['tag'] = 'ALL'
    by_tag = d.explode('tags').rename(columns={'tags': 'tag'})
    by_tag = by_tag[by_tag.tag.isin(tags)]
    return pd.concat([all_rows, by_tag], ignore_index=True)

def weighted_median(v, w):
    v, w = np.asarray(v, float), np.asarray(w, float)
    keep = np.isfinite(v) & np.isfinite(w) & (w > 0)
    v, w = v[keep], w[keep]
    if not len(v): return np.nan
    order = np.argsort(v, kind='stable'); v, w = v[order], w[order]
    return float(v[np.searchsorted(w.cumsum(), w.sum() / 2)])

def bootstrap_stat(v, w, kind='median', n_boot=1000, seed=SEED):
    """Question bootstrap, retaining each sampled question's original survey weight.

    Identical (value, weight) cells are compressed; multinomial cell counts are
    exactly equivalent to resampling rows, without allocating n_questions x 1000.
    """
    v, w = np.asarray(v, float), np.asarray(w, float)
    keep = np.isfinite(v) & np.isfinite(w) & (w > 0); v, w = v[keep], w[keep]
    if not len(v): return np.full(n_boot, np.nan)
    cells, counts = np.unique(np.column_stack([v, w]), axis=0, return_counts=True)
    rng = np.random.default_rng(seed); out = []
    for start in range(0, n_boot, 25):
        draws = rng.multinomial(len(v), counts / len(v), size=min(25, n_boot-start))
        mass = draws * cells[:, 1]
        if kind == 'median':
            indexes = (mass.cumsum(axis=1) >= mass.sum(axis=1)[:, None]/2).argmax(axis=1)
            out.extend(cells[indexes, 0])
        else:
            out.extend((mass * cells[:, 0]).sum(axis=1) / mass.sum(axis=1))
    return np.array(out)
