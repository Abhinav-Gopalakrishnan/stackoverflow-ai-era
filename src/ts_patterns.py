"""M3 Review 2 Method 1 patterns: STL decomposition and stationarity testing.

Run: python -m src.ts_patterns [--task stl|stationarity|all]

STL and ADF/KPSS both work on the log1p weekly counts (`log_count`) used by M5 for all
14 series. STL components are additive and sum back to `log_count`. Seasonal strength,
the named within-year dip and the differencing decision are descriptive summaries or
test outcomes, not causal claims.
"""
from __future__ import annotations
import argparse
import warnings
from pathlib import Path
import numpy as np
import pandas as pd

from src.review2_common import TS, write_json

PERIOD = 52
EXPECTED_WEEKS = 400
EXPECTED_SERIES = 14
SIGNIFICANCE = 0.05


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


def _tests(x: np.ndarray, tag: str, series: str) -> tuple[list[dict], float, float]:
    """Run ADF and KPSS on one series; return result rows and their p-values."""
    from statsmodels.tsa.stattools import adfuller, kpss
    x = np.asarray(x, float)
    rows = []
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        adf = adfuller(x, regression='c', autolag='AIC', result_object=True)
    adf_note = 'reject favours stationarity'
    for w in caught:
        adf_note += '; ' + str(w.message)
    rows.append({'tag': tag, 'series': series, 'test': 'ADF', 'null_hypothesis': 'unit root (non-stationary)',
                 'statistic': adf.statistic, 'p_value': adf.pvalue, 'lags': adf.lags, 'n_obs': adf.nobs,
                 'crit_1pct': adf.critical_values['1%'], 'crit_5pct': adf.critical_values['5%'],
                 'crit_10pct': adf.critical_values['10%'],
                 'reject_5pct': bool(adf.pvalue < SIGNIFICANCE), 'note': adf_note})
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        kp = kpss(x, regression='c', nlags='auto', result_object=True)
    note = 'reject favours non-stationarity'
    for w in caught:
        note += '; ' + str(w.message)
    rows.append({'tag': tag, 'series': series, 'test': 'KPSS', 'null_hypothesis': 'stationary',
                 'statistic': kp.statistic, 'p_value': kp.pvalue, 'lags': kp.lags, 'n_obs': len(x),
                 'crit_1pct': kp.critical_values['1%'], 'crit_5pct': kp.critical_values['5%'],
                 'crit_10pct': kp.critical_values['10%'],
                 'reject_5pct': bool(kp.pvalue < SIGNIFICANCE), 'note': note})
    return rows, adf.pvalue, kp.pvalue


def verdict(adf_p: float, kpss_p: float) -> str:
    """Combine ADF and KPSS at the 5% level for one transform."""
    if adf_p < SIGNIFICANCE and kpss_p > SIGNIFICANCE:
        return 'stationary'
    if adf_p >= SIGNIFICANCE and kpss_p <= SIGNIFICANCE:
        return 'non-stationary'
    return 'conflicting evidence'


def differencing_decision(level_verdict: str, diff_verdict: str, adf_level_p: float) -> tuple[str, str]:
    """Translate the two verdicts into a differencing order with a written reason."""
    if level_verdict == 'stationary':
        return 'd=0', 'ADF rejects a unit root and KPSS does not reject stationarity at the level'
    if level_verdict == 'non-stationary':
        reason = 'ADF cannot reject a unit root and KPSS rejects level stationarity'
        if diff_verdict == 'non-stationary':
            reason += '; the first difference also tests non-stationary'
        return 'd=1', reason
    if diff_verdict == 'stationary':
        return 'd=1 (ambiguous)', 'level tests conflict, but the first difference is stationary'
    if adf_level_p < SIGNIFICANCE:
        return 'd=0 (ambiguous)', 'level tests conflict, yet ADF rejects a unit root at the level'
    return 'd=1 (ambiguous)', 'level tests conflict and ADF cannot reject a unit root'


def stationarity() -> pd.DataFrame:
    """ADF and KPSS on the level and first difference of all 14 log-count series."""
    s = load_series()
    rows = []
    decisions = []
    for tag, sub in s.groupby('tag', sort=True):
        sub = sub.sort_values('week_start')
        level = sub['log_count'].to_numpy(float)
        diff = np.diff(level)
        lvl_rows, adf_level_p, kpss_level_p = _tests(level, tag, 'level')
        dif_rows, adf_diff_p, kpss_diff_p = _tests(diff, tag, 'first_difference')
        rows += lvl_rows + dif_rows
        level_verdict = verdict(adf_level_p, kpss_level_p)
        diff_verdict = verdict(adf_diff_p, kpss_diff_p)
        decision, rationale = differencing_decision(level_verdict, diff_verdict, adf_level_p)
        decisions.append({'tag': tag, 'adf_level_p': adf_level_p, 'kpss_level_p': kpss_level_p,
                          'adf_diff_p': adf_diff_p, 'kpss_diff_p': kpss_diff_p,
                          'level_verdict': level_verdict, 'diff_verdict': diff_verdict,
                          'differencing_decision': decision, 'rationale': rationale})

    out = pd.DataFrame(rows)
    dec = pd.DataFrame(decisions)
    TS.mkdir(parents=True, exist_ok=True)
    out.to_csv(TS / 'stationarity.csv', index=False)
    dec.to_csv(TS / 'stationarity_decision.csv', index=False)
    write_json(TS / 'stationarity_manifest.json', {
        'adf': 'adfuller, regression=c, autolag=AIC; null = unit root',
        'kpss': 'kpss, regression=c, nlags=auto; null = level stationary',
        'transformations': 'level = log1p weekly count; first_difference = level.diff()',
        'significance': SIGNIFICANCE,
        'verdict_rule': 'stationary if ADF rejects and KPSS does not; non-stationary if ADF does not reject and KPSS rejects; else conflicting',
        'decision_rule': 'd=0 on a stationary level; d=1 on a non-stationary level; conflicting levels use the first difference and the ADF level result, labelled ambiguous',
        'series': int(dec.tag.nunique()), 'rows': len(out),
        'interpretation': 'decisions support the fixed d=1 used by the M5 SARIMAX backtest; conflicting cases are reported, not hidden',
    })
    print(dec[['tag', 'level_verdict', 'diff_verdict', 'differencing_decision']].to_string(index=False))
    return dec


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


def main() -> None:
    parser = argparse.ArgumentParser(description='Review 2 Method 1 patterns (M3): STL and stationarity')
    parser.add_argument('--task', choices=['stl', 'stationarity', 'all'], default='all')
    args = parser.parse_args()
    if args.task in ('stl', 'all'):
        run()
    if args.task in ('stationarity', 'all'):
        stationarity()


if __name__ == '__main__':
    main()
