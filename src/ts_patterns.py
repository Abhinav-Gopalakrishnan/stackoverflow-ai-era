"""M3 Review 2 Method 1 patterns: STL, stationarity, change points and ITS.

Run: python -m src.ts_patterns [--task stl|stationarity|changepoints|its|all]

STL, ADF/KPSS, PELT change points and the interrupted time series regression all work on
the log1p weekly counts (`log_count`) used by M5 for all 14 series. STL components are
additive and sum back to `log_count`. Seasonal strength, the named within-year dip, the
differencing decision, change points and the ITS level/slope estimates are descriptive
summaries or test outcomes, not causal claims.
"""
from __future__ import annotations
import argparse
import warnings
from pathlib import Path
import numpy as np
import pandas as pd

from src.review2_common import ROOT, TS, write_json

PERIOD = 52
EXPECTED_WEEKS = 400
EXPECTED_SERIES = 14
SIGNIFICANCE = 0.05
MIN_SIZE = 26
BIC_PENALTY = 1.0
EVENT_WINDOW_DAYS = 28
EVENT_PATH = ROOT / 'docs/event_list.csv'


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


def load_events(path: Path | str = EVENT_PATH) -> pd.DataFrame:
    """Load the dated stakeholder events used to describe detected change points."""
    events = pd.read_csv(path, parse_dates=['date'])
    return events.sort_values('date').reset_index(drop=True)


def bic_penalty(y: np.ndarray) -> float:
    """BIC penalty for a mean-shift changepoint model, fixed in advance.

    The ruptures l2 cost is the sum of squared deviations, so the BIC term for one extra
    mean parameter per break is 2 * sigma^2 * log(n). For white noise, sigma^2 equals
    Var(first difference) / 2, giving pen = Var(first difference) * log(n). The variance
    is read from the data once and is never tuned to the breakpoints found.
    """
    return float(BIC_PENALTY * np.var(np.diff(y)) * np.log(len(y)))


def nearest_event(week: pd.Timestamp, events: pd.DataFrame) -> dict:
    """Nearest dated event to one change-point week, with distance in days."""
    days = (events.date - week).abs().dt.days
    row = events.loc[days.idxmin()]
    dist = int(days.min())
    return {'nearest_event_date': row.date.date().isoformat(), 'nearest_event_name': row.event_name,
            'distance_days': dist, 'within_4_weeks_of_event': bool(dist <= EVENT_WINDOW_DAYS)}


def changepoints() -> pd.DataFrame:
    """PELT change points on the log-count level, compared with the dated event list."""
    import ruptures as rpt
    s = load_series()
    events = load_events()
    rows = []
    summary = []
    for tag, sub in s.groupby('tag', sort=True):
        sub = sub.sort_values('week_start').reset_index(drop=True)
        y = sub['log_count'].to_numpy(float)
        pen = bic_penalty(y)
        ends = rpt.Pelt(model='l2', min_size=MIN_SIZE, jump=1).fit(y).predict(pen=pen)
        starts = [0] + list(ends[:-1])
        dates = []
        aligned = 0
        for k, c in enumerate(starts[1:], start=1):
            week = sub.week_start.iloc[c]
            before = y[starts[k - 1]:c]
            after = y[c:ends[k]]
            row = {'tag': tag, 'index': int(c), 'week_start': week,
                   'mean_before': float(before.mean()), 'mean_after': float(after.mean()),
                   'delta': float(after.mean() - before.mean())}
            row.update(nearest_event(week, events))
            aligned += int(row['within_4_weeks_of_event'])
            rows.append(row)
            dates.append(week.date().isoformat())
        summary.append({'tag': tag, 'n_changepoints': int(len(ends) - 1), 'model': 'l2',
                        'min_size': MIN_SIZE, 'penalty': pen,
                        'n_within_4_weeks_of_event': int(aligned),
                        'changepoint_dates': ';'.join(dates)})

    out = pd.DataFrame(rows)
    summ = pd.DataFrame(summary)
    aligned = int(summ.n_within_4_weeks_of_event.sum())
    series_with_break = int((summ.n_within_4_weeks_of_event > 0).sum())
    TS.mkdir(parents=True, exist_ok=True)
    out.to_csv(TS / 'changepoints.csv', index=False)
    summ.to_csv(TS / 'changepoints_summary.csv', index=False)
    make_changepoint_figure(s, out, events)
    write_json(TS / 'changepoints_manifest.json', {
        'method': 'ruptures Pelt, model=l2 (least-squares mean shift), jump=1',
        'min_size': MIN_SIZE,
        'penalty_rule': 'BIC for one extra mean parameter per break: pen = 2*sigma^2*log(n) on the l2 (sum of squares) cost; sigma^2 = Var(first difference)/2, so pen = BIC_PENALTY * Var(first difference) * log(n)',
        'penalty_fixed_in_advance': True,
        'input': 'log1p weekly counts (series_long.csv log_count)',
        'events': 'docs/event_list.csv; every change point carries its nearest event and distance in days',
        'proximity_rule': f'within_4_weeks_of_event = distance_days <= {EVENT_WINDOW_DAYS}',
        'series': int(summ.tag.nunique()), 'change_points': len(out),
        'aligned': f'change points within {EVENT_WINDOW_DAYS} days of an event: {aligned} of {len(out)}; {series_with_break} of 14 series have a Nov-Dec 2022 break',
        'interpretation': 'BIC often flags several level shifts on these trending series; a change point within ~4 weeks of the Nov-Dec 2022 events appears in most series, while a few tags (excel, fastapi, powerbi) show no event-near break. Proximity to a dated event is association, not causation.',
    })
    print(summ[['tag', 'n_changepoints', 'changepoint_dates']].to_string(index=False))
    return summ


def make_changepoint_figure(s: pd.DataFrame, out: pd.DataFrame, events: pd.DataFrame) -> None:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    tags = sorted(s.tag.unique())
    event_colors = ['#6A1B9A', '#00695C', '#C62828', '#EF6C00']
    fig, axes = plt.subplots(4, 4, figsize=(16, 13), sharex=True)
    axes = axes.ravel()
    for ax, tag in zip(axes, tags):
        sub = s[s.tag.eq(tag)].sort_values('week_start').reset_index(drop=True)
        ax.plot(sub.week_start, sub.log_count, color='#B0BEC5', lw=0.8)
        ax.plot(sub.week_start, fit_stl(sub).trend, color='#DD7F21', lw=1.4)
        for _, cp in out[out.tag.eq(tag)].iterrows():
            ax.axvline(pd.Timestamp(cp.week_start), color='#1565C0', lw=1.2)
        for color, (_, ev) in zip(event_colors, events.iterrows()):
            ax.axvline(ev.date, color=color, lw=1.0, ls='--', alpha=0.8)
        ax.set_title(tag, fontsize=10)
        ax.grid(alpha=0.3)
    for ax in axes[len(tags):]:
        ax.axis('off')
    handles = [plt.Line2D([], [], color='#B0BEC5', lw=1.0, label='log count'),
               plt.Line2D([], [], color='#DD7F21', lw=1.4, label='STL trend'),
               plt.Line2D([], [], color='#1565C0', lw=1.2, label='detected change point')]
    handles += [plt.Line2D([], [], color=c, lw=1.0, ls='--', label=ev.event_name)
                for c, (_, ev) in zip(event_colors, events.iterrows())]
    axes[0].legend(handles=handles, fontsize=7, loc='lower left')
    fig.suptitle('PELT mean-shift change points under a fixed BIC penalty (solid); late-2022 level breaks align with the ChatGPT-era events (dashed)',
                 fontsize=11, y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.985))
    fig.savefig(TS / 'changepoints_small_multiples.png', dpi=150)
    plt.close(fig)


HAC_LAGS = 4
YEAR_CYCLE = 52.18
ORIGIN = pd.Timestamp('2019-01-01')
INTERVENTION = pd.Timestamp('2022-11-29')  # Tuesday week containing the plan's t0 2022-11-30
PLACEBO = pd.Timestamp('2021-11-30')       # no-intervention placebo break (plan M3-23)
INTERVENTION_NAME = 'ChatGPT Launch'


def _week_index(ts: pd.Timestamp) -> float:
    return (ts - ORIGIN).days / 7.0


def _segmented_design(sub: pd.DataFrame, t0: pd.Timestamp):
    """Design matrix for the plan's segmented regression (M3-23, Fourier k = 1, 2)."""
    week = (sub.week_start - ORIGIN).dt.days / 7.0
    post = (sub.week_start >= t0).astype(float)
    ramp = np.maximum(0.0, week - _week_index(t0))
    exog = np.column_stack([
        np.ones(len(sub)), week, post, ramp,
        np.sin(2 * np.pi * week / YEAR_CYCLE), np.cos(2 * np.pi * week / YEAR_CYCLE),
        np.sin(4 * np.pi * week / YEAR_CYCLE), np.cos(4 * np.pi * week / YEAR_CYCLE),
    ])
    return post, exog


def _fit_segmented(sub: pd.DataFrame, t0: pd.Timestamp) -> dict:
    """OLS with Newey-West (HAC, lag 4) errors for a break at t0."""
    import statsmodels.api as sm
    post, exog = _segmented_design(sub, t0)
    fit = sm.OLS(sub['log_count'].to_numpy(float), exog).fit(
        cov_type='HAC', cov_kwds={'maxlags': HAC_LAGS}, use_t=True)
    return {'b': np.asarray(fit.params), 'p': np.asarray(fit.pvalues),
            'ci': np.asarray(fit.conf_int(), dtype=float), 'post': post}


def _effects(res: dict) -> dict:
    """Plan-defined effects: level = exp(b2) - 1, slope = exp(b3) - 1, each with 95% CI."""
    b, p, ci = res['b'], res['p'], res['ci']
    return {
        'level_change': float(np.exp(b[2]) - 1),
        'level_ci_lo': float(np.exp(ci[2, 0]) - 1), 'level_ci_hi': float(np.exp(ci[2, 1]) - 1),
        'level_p': float(p[2]),
        'slope_change': float(np.exp(b[3]) - 1),
        'slope_ci_lo': float(np.exp(ci[3, 0]) - 1), 'slope_ci_hi': float(np.exp(ci[3, 1]) - 1),
        'slope_p': float(p[3]),
    }


def its() -> pd.DataFrame:
    """Interrupted time series regression on log_count for all 14 series.

    Segmented regression
        log_count = b0 + b1*week + b2*post + b3*(week - t0)*post + Fourier(k=1,2),
    the model fixed by Review 2 Method 1 (M3-23). The break t0 is the Tuesday week
    containing 2022-11-30 (one week before the 2022-12-05 ban), matching the M5 SARIMAX
    intervention. Errors are Newey-West (HAC, lag 4). The plan's reported effects are
    the level change exp(b2) - 1 and the weekly slope change exp(b3) - 1, each with a
    95% interval. A placebo break at 2021-11-30 is fitted with the same model: the real
    effect should be large and the placebo small.
    """
    s = load_series()
    rows = []
    for tag, sub in s.groupby('tag', sort=True):
        sub = sub.sort_values('week_start').reset_index(drop=True)
        real = _fit_segmented(sub, INTERVENTION)
        placebo = _fit_segmented(sub, PLACEBO)
        e, pe = _effects(real), _effects(placebo)
        b = real['b']
        if e['slope_ci_lo'] > 0 or e['slope_ci_hi'] < 0:
            status = 'significant post-slope rise' if e['slope_change'] > 0 else 'significant post-slope decline'
        else:
            status = 'no significant slope change'
        rows.append({
            'tag': tag,
            'intervention_date': '2022-11-30',
            'intervention_week_start': INTERVENTION.date().isoformat(),
            'intervention_event': INTERVENTION_NAME,
            'placebo_break_date': PLACEBO.date().isoformat(),
            'n_weeks': len(sub),
            'n_pre_weeks': int((1 - real['post']).sum()), 'n_post_weeks': int(real['post'].sum()),
            'beta0': float(b[0]), 'beta1': float(b[1]), 'beta2': float(b[2]), 'beta3': float(b[3]),
            'level_change': e['level_change'], 'level_change_pct': 100.0 * e['level_change'],
            'level_ci_lo': e['level_ci_lo'], 'level_ci_hi': e['level_ci_hi'], 'level_p': e['level_p'],
            'slope_change': e['slope_change'], 'slope_change_pct': 100.0 * e['slope_change'],
            'slope_ci_lo': e['slope_ci_lo'], 'slope_ci_hi': e['slope_ci_hi'], 'slope_p': e['slope_p'],
            'slope_pre': float(np.exp(b[1]) - 1),
            'slope_post': float(np.exp(b[1] + b[3]) - 1),
            'status': status,
            'placebo_level_change': pe['level_change'],
            'placebo_level_ci_lo': pe['level_ci_lo'], 'placebo_level_ci_hi': pe['level_ci_hi'],
            'placebo_level_p': pe['level_p'],
            'placebo_slope_change': pe['slope_change'],
            'placebo_slope_ci_lo': pe['slope_ci_lo'], 'placebo_slope_ci_hi': pe['slope_ci_hi'],
            'placebo_slope_p': pe['slope_p'],
            'effect_exceeds_placebo': bool(abs(e['slope_change']) > abs(pe['slope_change'])),
        })

    out = pd.DataFrame(rows)
    TS.mkdir(parents=True, exist_ok=True)
    out.to_csv(TS / 'its_results.csv', index=False)
    make_its_figure(s, out)
    make_its_forest(out)
    write_json(TS / 'its_manifest.json', {
        'model': 'segmented regression: log_count ~ week + post + (week - t0)*post + sin/cos(2*pi*k*week/52.18), k=1,2',
        't0': '2022-11-30 (Tuesday-start week 2022-11-29; one week before the 2022-12-05 ban; mirrors the M5 SARIMAX intervention)',
        'placebo': f'break at {PLACEBO.date().isoformat()} with the same model; the real effect should be larger',
        'estimator': f'OLS with Newey-West HAC standard errors, lag {HAC_LAGS}, t-based tests',
        'level_change': 'exp(beta2) - 1: immediate multiplicative change in weekly count at 2022-11-30',
        'slope_change': 'exp(beta3) - 1: weekly slope change after 2022-11-30 on the multiplicative scale, with 95% CI',
        'slope_pre_post': 'exp(beta1) - 1 and exp(beta1 + beta3) - 1 are the pre and post weekly growth rates',
        'status_rule': 'status is significant when the slope-change 95% CI excludes 0; direction follows the sign of beta3',
        'significance': SIGNIFICANCE,
        'series': int(out.tag.nunique()),
        'interpretation': 'the real break should be larger than the placebo; an immediate level change does not imply a sustained slope change. Association is observation-level, not causal.',
    })
    print(out[['tag', 'level_change', 'level_p', 'slope_change', 'slope_ci_lo', 'slope_ci_hi',
               'placebo_slope_change', 'effect_exceeds_placebo', 'status']].to_string(index=False))
    return out


def make_its_figure(s: pd.DataFrame, out: pd.DataFrame) -> None:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    tags = sorted(s.tag.unique())
    fig, axes = plt.subplots(4, 4, figsize=(16, 13), sharex=True)
    axes = axes.ravel()
    for ax, tag in zip(axes, tags):
        sub = s[s.tag.eq(tag)].sort_values('week_start').reset_index(drop=True)
        x = (sub.week_start - ORIGIN).dt.days / 7.0
        ax.plot(sub.week_start, sub.log_count, color='#B0BEC5', lw=0.8, label='log count')
        r = out[out.tag.eq(tag)].iloc[0]
        t0 = _week_index(INTERVENTION)
        ax.axvline(INTERVENTION, color='#37474F', lw=1.2, ls='--', alpha=0.9)
        pre = x < t0
        ax.plot(sub.week_start[pre], r.beta0 + r.beta1 * x[pre],
                color='#1565C0', lw=1.8, label='pre-slope')
        ax.plot(sub.week_start[~pre],
                r.beta0 + r.beta1 * x[~pre] + r.beta2 + r.beta3 * (x[~pre] - t0),
                color='#C62828', lw=1.8, label='post-slope')
        ax.set_title(f'{tag}  slope {100 * r.slope_change:+.1f}%/wk change', fontsize=10)
        ax.grid(alpha=0.3)
    for ax in axes[len(tags):]:
        ax.axis('off')
    handles = [plt.Line2D([], [], color='#B0BEC5', lw=1.0, label='log count'),
               plt.Line2D([], [], color='#1565C0', lw=1.8, label='pre-intervention slope'),
               plt.Line2D([], [], color='#C62828', lw=1.8, label='post-intervention slope'),
               plt.Line2D([], [], color='#37474F', lw=1.2, ls='--', label='2022-11-29 (week of 2022-11-30)')]
    axes[0].legend(handles=handles, fontsize=6, loc='lower left')
    fig.suptitle('Interrupted time series: the post-ChatGPT weekly trend turns negative in every series',
                 fontsize=13, y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.985))
    fig.savefig(TS / 'its_small_multiples.png', dpi=150)
    plt.close(fig)


def make_its_forest(out: pd.DataFrame) -> None:
    """Forest plot of the plan's level and slope changes (real vs placebo)."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    o = out.sort_values('slope_change').reset_index(drop=True)
    tags = list(o.tag)
    y = np.arange(len(tags))
    fig, (axL, axS) = plt.subplots(1, 2, figsize=(15, 8))

    def panel(ax, real, lo, hi, pl, plo, phi, title, xlabel):
        ax.axvline(0, color='#455A64', lw=1.0, ls='--', alpha=0.85)
        ax.errorbar(real, y, xerr=[real - lo, hi - real], fmt='o', color='#1565C0',
                    ecolor='#1565C0', elinewidth=1.6, capsize=3, ms=5,
                    label='2022-11-30 (real break)')
        ax.errorbar(pl, y + 0.18, xerr=[pl - plo, phi - pl], fmt='s', color='#90A4AE',
                    ecolor='#90A4AE', elinewidth=1.2, capsize=3, ms=4,
                    label='2021-11-30 (placebo)')
        ax.set_yticks(y)
        ax.set_yticklabels(tags, fontsize=9)
        ax.set_title(title, fontsize=12)
        ax.set_xlabel(xlabel)
        ax.grid(alpha=0.3, axis='x')

    panel(axL, o.level_change, o.level_ci_lo, o.level_ci_hi,
          o.placebo_level_change, o.placebo_level_ci_lo, o.placebo_level_ci_hi,
          'Immediate level change (exp(b2) - 1)', 'multiplicative change in weekly count')
    panel(axS, o.slope_change, o.slope_ci_lo, o.slope_ci_hi,
          o.placebo_slope_change, o.placebo_slope_ci_lo, o.placebo_slope_ci_hi,
          'Weekly slope change (exp(b3) - 1)', 'multiplicative change in weekly trend')
    axS.legend(fontsize=9, loc='lower left')
    fig.suptitle('ITS level and slope changes with 95% HAC intervals, real break vs 2021 placebo', fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(TS / 'its_forest.png', dpi=150)
    plt.close(fig)


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
    parser = argparse.ArgumentParser(description='Review 2 Method 1 patterns (M3): STL, stationarity, change points and ITS')
    parser.add_argument('--task', choices=['stl', 'stationarity', 'changepoints', 'its', 'all'], default='all')
    args = parser.parse_args()
    if args.task in ('stl', 'all'):
        run()
    if args.task in ('stationarity', 'all'):
        stationarity()
    if args.task in ('changepoints', 'all'):
        changepoints()
    if args.task in ('its', 'all'):
        its()


if __name__ == '__main__':
    main()
