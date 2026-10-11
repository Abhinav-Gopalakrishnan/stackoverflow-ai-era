"""M3 Review 2: STL decomposition, seasonal strength and named yearly dips.

Run: python -m src.ts_patterns

STL is fitted on log1p weekly counts (the same `log_count` used by M5) for all 14
series. Components are additive and sum back to `log_count`. Seasonal strength and
the named within-year dip are descriptive summaries, not causal claims.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd

from src.review2_common import TS, write_json

PERIOD = 52
EXPECTED_WEEKS = 400
EXPECTED_SERIES = 14


def load_series(path: Path | str = TS / 'series_long.csv') -> pd.DataFrame:
    """Load and validate the prepared weekly series (14 tags x 400 weeks)."""
    s = pd.read_csv(path, parse_dates=['week_start'])
    if len(s) != EXPECTED_WEEKS * EXPECTED_SERIES:
        raise ValueError(f'Expected {EXPECTED_WEEKS * EXPECTED_SERIES} rows, found {len(s)}')
    if s.tag.nunique() != EXPECTED_SERIES:
        raise ValueError(f'Expected {EXPECTED_SERIES} tags, found {s.tag.nunique()}')
    if s.log_count.isna().any():
        raise ValueError('log_count contains missing values')
    for tag, sub in s.groupby('tag'):
        sub = sub.sort_values('week_start')
        if len(sub) != EXPECTED_WEEKS:
            raise ValueError(f'{tag}: expected {EXPECTED_WEEKS} weeks, found {len(sub)}')
        if not sub.week_start.diff().dropna().eq(pd.Timedelta(days=7)).all():
            raise ValueError(f'{tag}: weeks are not evenly spaced')
    return s.sort_values(['tag', 'week_start']).reset_index(drop=True)


def fit_stl(sub: pd.DataFrame):
    """STL on the log1p count with a fixed 52-week yearly period."""
    from statsmodels.tsa.seasonal import STL
    y = sub.set_index('week_start')['log_count'].asfreq('7D')
    return STL(y, period=PERIOD, robust=True).fit()


def strength(resid: np.ndarray, component: np.ndarray) -> float:
    """FPP3 strength of a component: max(0, 1 - Var(resid) / Var(component + resid))."""
    denom = np.var(component + resid)
    if denom <= 0:
        return 0.0
    return float(max(0.0, 1.0 - np.var(resid) / denom))


def month_of_phase(phase: int) -> str:
    """Approximate calendar month for an STL seasonal phase (origin 2019-01-01)."""
    date = pd.Timestamp('2019-01-01') + pd.Timedelta(days=7 * int(phase))
    return date.strftime('%B')


def yearly_dip(seasonal: np.ndarray) -> dict:
    """Name the recurring within-year dip from the mean seasonal profile.

    The profile is averaged by STL phase 0..51 so the 52-week period is exact.
    The dip is the lowest phase expanded cyclically over consecutive negative
    phases, which handles the December-to-January wrap.
    """
    phase_of_week = np.arange(len(seasonal)) % PERIOD
    profile = np.array([seasonal[phase_of_week == p].mean() for p in range(PERIOD)])
    trough = int(np.argmin(profile))
    if profile[trough] >= 0:
        return {'peak_phase': int(np.argmax(profile)), 'trough_phase': trough,
                'dip_start_phase': trough, 'dip_end_phase': trough, 'dip_name': 'no seasonal dip'}
    start = trough
    while profile[(start - 1) % PERIOD] < 0 and (start - 1) % PERIOD != trough:
        start = (start - 1) % PERIOD
    end = trough
    while profile[(end + 1) % PERIOD] < 0 and (end + 1) % PERIOD != start:
        end = (end + 1) % PERIOD
    window = [(start + i) % PERIOD for i in range((end - start) % PERIOD + 1)]
    order = {m: i for i, m in enumerate(
        ['January', 'February', 'March', 'April', 'May', 'June', 'July',
         'August', 'September', 'October', 'November', 'December'])}
    months = sorted({month_of_phase(p) for p in window}, key=order.get)
    return {'peak_phase': int(np.argmax(profile)), 'trough_phase': trough,
            'dip_start_phase': start, 'dip_end_phase': end, 'dip_name': ' / '.join(months)}


def run() -> pd.DataFrame:
    s = load_series()
    components = []
    summary = []
    for tag, sub in s.groupby('tag', sort=True):
        sub = sub.sort_values('week_start').reset_index(drop=True)
        res = fit_stl(sub)
        components.append(pd.DataFrame({
            'tag': tag,
            'week_start': res.observed.index,
            'log_count': res.observed.to_numpy(),
            'trend': res.trend.to_numpy(),
            'seasonal': res.seasonal.to_numpy(),
            'resid': res.resid.to_numpy(),
        }))
        resid = res.resid.to_numpy()
        dip = yearly_dip(res.seasonal.to_numpy())
        summary.append({
            'tag': tag,
            'n_weeks': len(sub),
            'seasonal_strength': strength(resid, res.seasonal.to_numpy()),
            'trend_strength': strength(resid, res.trend.to_numpy()),
            'peak_phase': dip['peak_phase'],
            'peak_month': month_of_phase(dip['peak_phase']),
            'trough_phase': dip['trough_phase'],
            'trough_month': month_of_phase(dip['trough_phase']),
            'dip_start_phase': dip['dip_start_phase'],
            'dip_end_phase': dip['dip_end_phase'],
            'dip_name': dip['dip_name'],
        })

    comp = pd.concat(components, ignore_index=True)
    summ = pd.DataFrame(summary).sort_values('seasonal_strength', ascending=False).reset_index(drop=True)
    TS.mkdir(parents=True, exist_ok=True)
    comp.to_csv(TS / 'stl_components.csv', index=False)
    summ.to_csv(TS / 'stl_summary.csv', index=False)
    make_figure(comp, summ)
    write_json(TS / 'stl_manifest.json', {
        'model': 'statsmodels STL, robust=True, period=52',
        'input': 'log1p weekly counts (series_long.csv log_count)',
        'series': len(summ), 'weeks_per_series': EXPECTED_WEEKS,
        'component_identity': 'trend + seasonal + resid = log_count (additive)',
        'seasonal_strength': 'max(0, 1 - Var(resid) / Var(seasonal + resid))',
        'trend_strength': 'max(0, 1 - Var(resid) / Var(trend + resid))',
        'dip_definition': 'lowest mean seasonal phase expanded cyclically over negative phases; months approximate, origin 2019-01-01',
        'interpretation': 'descriptive; seasonality is small relative to the 2022 level change, association is not causation',
    })
    return summ


def make_figure(comp: pd.DataFrame, summ: pd.DataFrame) -> None:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    tags = list(summ.tag)
    fig, axes = plt.subplots(4, 4, figsize=(16, 13), sharex=True)
    axes = axes.ravel()
    for ax, tag in zip(axes, tags):
        sub = comp[comp.tag.eq(tag)].sort_values('week_start')
        ax.plot(sub.week_start, sub.log_count, color='#B0BEC5', lw=0.8, label='log count')
        ax.plot(sub.week_start, sub.trend, color='#DD7F21', lw=1.6, label='STL trend')
        ss = summ.loc[summ.tag.eq(tag), 'seasonal_strength'].iloc[0]
        ax.set_title(f'{tag}  (seasonal strength {ss:.2f})', fontsize=10)
        ax.grid(alpha=0.3)
    for ax in axes[len(tags):]:
        ax.axis('off')
    axes[0].legend(fontsize=8, loc='lower left')
    fig.suptitle('All 14 series share a sharp late-2022 level drop; within-year seasonality is small',
                 fontsize=13, y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.985))
    fig.savefig(TS / 'stl_small_multiples.png', dpi=150)
    plt.close(fig)


if __name__ == '__main__':
    argparse.ArgumentParser(description='STL patterns for Review 2 Method 1 (M3-20)').parse_args()
    run()
