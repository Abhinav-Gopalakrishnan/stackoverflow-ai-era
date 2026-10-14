"""Member 3 (Akshay) Review 2: combined insight matrix and stakeholder recommendations.

Joins Method 1 (M5 forecast class, M3 interrupted time series), Method 2 (M4 topics and
keywords, M2 tone and complexity) and the Review 1 resolved-rate tables into one row per
study tag, then writes the time-series + text-mining recommendations behind dashboard
page 6. Every recommendation cites at least one time-series number and one text-mining
number.

Run: python -m src.review2_m3_insights
"""
from __future__ import annotations
import argparse
import datetime as dt
import re
from pathlib import Path
import numpy as np
import pandas as pd
from src.review2_common import ROOT, TEXT, TS, write_json

TAGS_CSV = TS / 'tag_classes.csv'
ITS_CSV = TS / 'its_results.csv'
TONE_CSV = TEXT / 'tone_prepost.csv'
COMPLEXITY_CSV = TEXT / 'complexity_prepost.csv'
TOPIC_PREPOST_CSV = TEXT / 'topic_prepost.csv'
TOPIC_LABELS_CSV = TEXT / 'topic_labels.csv'
TOPIC_OUTCOMES_CSV = TEXT / 'topic_outcomes.csv'
KEYWORDS_CSV = TEXT / 'keywords_prepost.csv'
FORECASTS_CSV = TS / 'forecasts_26w.csv'
MONTHLY_TAG_TABLES = ROOT / 'data/processed/monthly_tag_tables.csv'
SHAP_TOP_CSV = ROOT / 'reports/review1/m5/shap_top.csv'

OUT_MATRIX = ROOT / 'reports/review2/insight_matrix.csv'
OUT_RECS = ROOT / 'reports/review2/recommendations.csv'
OUT_MANIFEST = ROOT / 'reports/review2/insight_matrix_manifest.json'

PER_TAG_KEYWORD_SCOPE = ('python', 'javascript', 'powerbi')
COMPLEXITY_METRICS = {
    'complexity_prose_words_change': ('prose_words', 'median'),
    'complexity_code_lines_change': ('code_lines', 'median'),
    'complexity_version_flag_change': ('version_flag', 'mean'),
}
PRE_END = pd.Timestamp('2022-10-31')
POST_START = pd.Timestamp('2023-01-01')
STAKEHOLDERS = ('Q&A platform product team', 'developer-forum managers', 'DevRel teams')


def load_tags():
    tc = pd.read_csv(TAGS_CSV)
    tags = [t for t in tc['tag'] if t != 'ALL']
    if len(tags) != len(set(tags)) or not tags:
        raise ValueError('Unexpected tag universe in tag_classes.csv')
    return tags


def _weighted_mean(values, weights):
    v = pd.to_numeric(values, errors='coerce').to_numpy(float)
    w = pd.to_numeric(weights, errors='coerce').to_numpy(float)
    keep = np.isfinite(v) & np.isfinite(w) & (w > 0)
    if not keep.any():
        return np.nan
    return float(np.average(v[keep], weights=w[keep]))


def _resolved_rates(monthly):
    def for_tag(tag):
        m = monthly[(monthly.tag == tag) & (~monthly.low_sample)].copy()
        pre = m[m.month <= PRE_END]
        post = m[m.month >= POST_START]
        return (_weighted_mean(pre.resolved_rate_7d, pre.est_questions),
                _weighted_mean(post.resolved_rate_7d, post.est_questions))
    return for_tag


def _topic_strings(keywords, topic_prepost, labels):
    def for_tag(tag):
        if tag in PER_TAG_KEYWORD_SCOPE:
            k = keywords[keywords.tag_scope == tag]
            rising = k[k.direction == 'rising'].sort_values('rank').term.dropna().astype(str).head(5)
            falling = k[k.direction == 'falling'].sort_values('rank').term.dropna().astype(str).head(5)
            scope = f'per-tag keywords ({tag})'
            return '; '.join(rising), '; '.join(falling), scope
        rising = topic_prepost[topic_prepost.change > 0].sort_values('change', ascending=False).head(3)
        falling = topic_prepost[topic_prepost.change < 0].sort_values('change').head(3)
        up = '; '.join(labels[t] for t in rising.topic)
        down = '; '.join(labels[t] for t in falling.topic)
        return up, down, 'overall topics (fallback)'
    return for_tag


def build_insight_matrix():
    tags = load_tags()
    tc = pd.read_csv(TAGS_CSV).set_index('tag')
    its = pd.read_csv(ITS_CSV).set_index('tag')
    tone = pd.read_csv(TONE_CSV)
    frust = tone[tone.measure == 'frustration'].set_index('tag')
    comp = pd.read_csv(COMPLEXITY_CSV)
    keywords = pd.read_csv(KEYWORDS_CSV)
    topic_prepost = pd.read_csv(TOPIC_PREPOST_CSV)
    labels = {int(r.topic): r.final_name for r in pd.read_csv(TOPIC_LABELS_CSV).itertuples()}
    monthly = pd.read_csv(MONTHLY_TAG_TABLES)
    monthly['month'] = pd.to_datetime(monthly['month'])
    resolved = _resolved_rates(monthly)
    topics = _topic_strings(keywords, topic_prepost, labels)

    rows = []
    for tag in tags:
        base = tc.loc[tag]
        m3 = its.loc[tag]
        fr = frust.loc[tag]
        rr_pre, rr_post = resolved(tag)
        up, down, scope = topics(tag)
        row = {
            'tag': tag,
            'forecast_class': base.forecast_class,
            'change_26w_pct': base.change_26w_pct,
            'half_life_weeks': base.half_life_weeks,
            'load_index_vs_2025': base.load_index_vs_2025,
            'its_level_change_pct': m3.level_change_pct,
            'its_level_p': m3.level_p,
            'its_slope_change_pct': m3.slope_change_pct,
            'its_slope_p': m3.slope_p,
            'its_status': m3.status,
            'its_exceeds_placebo': m3.effect_exceeds_placebo,
            'rising_topics': up,
            'falling_topics': down,
            'topic_evidence_scope': scope,
            'frustration_change': fr.change * 100,
            'frustration_lower95': fr.lower95 * 100,
            'frustration_upper95': fr.upper95 * 100,
            'resolved_rate_pre': rr_pre,
            'resolved_rate_post': rr_post,
            'resolved_rate_change': rr_post - rr_pre,
        }
        for col, (metric, statistic) in COMPLEXITY_METRICS.items():
            sel = comp[(comp.tag == tag) & (comp.metric == metric) & (comp.statistic == statistic)]
            if len(sel) != 1:
                raise ValueError(f'complexity row missing for {tag}/{metric}/{statistic}')
            change = float(sel.change.iloc[0])
            row[col] = change * 100 if metric in ('version_flag', 'error_text_flag', 'why_how_flag') else change
        rows.append(row)
    return pd.DataFrame(rows)


def _steepest(matrix, n):
    d = matrix.sort_values('its_slope_change_pct').head(n)
    return ', '.join(f'{r.tag} {r.its_slope_change_pct:+.2f}%/wk' for r in d.itertuples())


def build_recommendations(matrix):
    tc = matrix.set_index('tag')
    frust_all = pd.read_csv(TONE_CSV).query("tag == 'ALL' and measure == 'frustration'").change.iloc[0] * 100
    rising = pd.read_csv(TOPIC_PREPOST_CSV)
    rising = rising[rising.change > 0].sort_values('change', ascending=False)
    labels = {int(r.topic): r.final_name for r in pd.read_csv(TOPIC_LABELS_CSV).itertuples()}
    top_rising = labels[int(rising.topic.iloc[0])]
    top_rising_pp = rising.change.iloc[0] * 100
    falling = pd.read_csv(TOPIC_PREPOST_CSV).sort_values('change')
    top_falling = labels[int(falling.topic.iloc[0])]
    outcomes = pd.read_csv(TOPIC_OUTCOMES_CSV).set_index('topic')
    rising_resolved = outcomes.loc[int(rising.topic.iloc[0]), 'resolved_rate_7d']
    shap = pd.read_csv(SHAP_TOP_CSV, index_col=0)
    shap_feat = 'account_age_days'
    shap_val = float(shap.loc[shap_feat, 'mean_abs_shap'])
    fc = pd.read_csv(FORECASTS_CSV)
    fc = fc[fc.selected]
    agg = fc[(fc.tag == 'ALL') & (fc.horizon == 26)].iloc[0]
    oai = tc.loc['openai-api']
    frust_up = matrix[matrix.frustration_change > 0].sort_values('frustration_change', ascending=False)
    frust_up_txt = ', '.join(f'{r.tag} {r.frustration_change:+.1f}pp' for r in frust_up.head(3).itertuples())

    kw = pd.read_csv(KEYWORDS_CSV)
    mig_rx = re.compile(r'version|setup|install|migrat|upgrade|toml|pyproject|update', re.I)
    mig = kw[(kw.direction == 'rising') & kw.term.astype(str).str.contains(mig_rx)]
    mig_parts, mig_tags = [], []
    for tag in PER_TAG_KEYWORD_SCOPE:
        s = mig[mig.tag_scope == tag].sort_values('rank')
        if len(s):
            mig_tags.append(tag)
            mig_parts.append(f"{tag}: " + ', '.join(f'{t} (rank {int(r)})' for t, r in zip(s.term, s['rank'])))
    mig_txt = '; '.join(mig_parts)
    mig_slopes = '; '.join(f'{t} {tc.loc[t, "its_slope_change_pct"]:+.2f}%/wk' for t in mig_tags)

    steep = _steepest(matrix, 3)
    mild = _steepest(matrix, 14).split(', ')[-3:]
    mild = ', '.join(mild)
    declined = int((matrix.forecast_class == 'steep decline').sum())

    rows = [
        {
            'finding': 'Moderate the tags that are still falling fastest, and stop staffing the slower-declining ones.',
            'time_series_evidence': (
                f'ITS post-slope declines are steepest for {steep}; the mildest are {mild} '
                f'(its_results.csv). {declined} of 13 tags are classed steep decline by the 26-week forecast.'),
            'text_mining_evidence': (
                f'Site-wide frustration share changed {frust_all:+.1f}pp after the break (tone_prepost.csv).'),
            'action': 'Reallocate moderation hours from stabilising tags to the steep-decline tags, and refresh the forecast each quarter.',
            'stakeholder': 'Q&A platform product team',
            'kpi_to_track': 'Moderation hours per 1,000 questions on steep-decline tags',
            'caveat': 'The break is associated with, not caused by, AI adoption; slope ranks are model-based.',
        },
        {
            'finding': 'Turn rising setup, version and migration language into a documentation backlog.',
            'time_series_evidence': (
                f'The tags with rising version/setup keywords are still declining: {mig_slopes} (its_results.csv).'),
            'text_mining_evidence': (
                f'Rising per-tag keywords include {mig_txt} (keywords_prepost.csv).'),
            'action': 'Promote these rising version/setup keywords into the DevRel guide backlog for the tags that show them.',
            'stakeholder': 'DevRel teams',
            'kpi_to_track': 'Guides shipped against the rising-keyword backlog',
            'caveat': 'Keyword frequency is a proxy for demand, not a direct measure of documentation need.',
        },
        {
            'finding': 'Route topics that gain share but resolve poorly to an expert queue.',
            'time_series_evidence': (
                f'The {top_rising} topic rises {top_rising_pp:+.2f}pp site-wide (topic_prepost.csv) while '
                f'python post-slope is {tc.loc["python","its_slope_change_pct"]:+.2f}%/wk (its_results.csv).'),
            'text_mining_evidence': (
                f'{top_rising} resolves at {rising_resolved * 100:.1f}% within 7 days (topic_outcomes.csv).'),
            'action': 'Send rising, low-resolution topics to an expert routing queue with topic tags.',
            'stakeholder': 'developer-forum managers',
            'kpi_to_track': '7-day resolved rate and time-to-first-answer on routed topics',
            'caveat': 'NMF topics are coarse; a question can span several topics.',
        },
        {
            'finding': 'Give first-time askers a guided template where frustration is rising and new accounts resolve less.',
            'time_series_evidence': (
                f'Frustration share rose only for {frust_up_txt} and fell slightly site-wide '
                f'({frust_all:+.1f}pp, tone_prepost.csv); python and javascript still decline '
                f'({tc.loc["python","its_slope_change_pct"]:+.2f} and '
                f'{tc.loc["javascript","its_slope_change_pct"]:+.2f}%/wk, its_results.csv).'),
            'text_mining_evidence': (
                f'Review 1 SHAP ranks {shap_feat} second of all features (mean |SHAP| {shap_val:.3f}), so '
                f'account age matters almost as much as tag volume (shap_top.csv).'),
            'action': 'Add a guided question template for first posts, prompted when the frustration flag is set.',
            'stakeholder': 'Q&A platform product team',
            'kpi_to_track': '7-day resolved rate for first posts',
            'caveat': 'The template is a UX intervention; its effect is not identified by the pre/post analysis.',
        },
        {
            'finding': 'Trigger a review when weekly volume leaves the forecast band.',
            'time_series_evidence': (
                f'The 26-week forecast carries a 95% band; for ALL the week-26 band is '
                f'{agg.lower95:.0f}-{agg.upper95:.0f} around {agg.pred:.0f} (forecasts_26w.csv).'),
            'text_mining_evidence': (
                f'Falling topics such as {top_falling} signal where traffic is moving (topic_prepost.csv).'),
            'action': 'Alert the analytics lead when a tag closes a week outside its 95% forecast band.',
            'stakeholder': 'Q&A platform product team',
            'kpi_to_track': 'Shares flagged and reviewed per quarter',
            'caveat': 'Bands are wide for volatile tags, so alerts are a prompt to look, not a conclusion.',
        },
        {
            'finding': 'Treat openai-api as an emerging tag: a step change without a stable trend.',
            'time_series_evidence': (
                f'openai-api shows a {oai.its_level_change_pct:+.0f}% level change but a '
                f'{oai.its_slope_change_pct:+.2f}%/wk post-slope, with a {oai.half_life_weeks:.0f}-week '
                f'half-life and no classifiable 26-week change (its_results.csv, tag_classes.csv).'),
            'text_mining_evidence': (
                'Docker and Android topics also gained share site-wide (topic_prepost.csv), the same emerging-stack pattern.'),
            'action': 'Monitor openai-api monthly and review routing and tagging once a baseline exists.',
            'stakeholder': 'developer-forum managers',
            'kpi_to_track': 'Weekly openai-api volume versus its forecast band',
            'caveat': 'A single level jump does not imply a lasting slope change.',
        },
    ]
    return pd.DataFrame(rows)


def validate(matrix, recs):
    required = {
        'tag', 'forecast_class', 'change_26w_pct', 'its_level_change_pct', 'its_slope_change_pct',
        'rising_topics', 'falling_topics', 'topic_evidence_scope', 'frustration_change',
        'resolved_rate_pre', 'resolved_rate_post', 'resolved_rate_change',
        'complexity_prose_words_change', 'complexity_code_lines_change', 'complexity_version_flag_change',
    }
    missing = required - set(matrix.columns)
    if missing:
        raise ValueError(f'insight_matrix missing columns: {sorted(missing)}')
    if len(matrix) != 13 or matrix.tag.nunique() != 13:
        raise ValueError('insight_matrix must have one row per 13 study tags')
    key = ['forecast_class', 'its_slope_change_pct', 'resolved_rate_post', 'frustration_change']
    if matrix[key].isna().any().any():
        raise ValueError('insight_matrix has NaN in key columns')
    zero = matrix.forecast_class.eq('not classifiable: zero baseline')
    if int(matrix.change_26w_pct.isna().sum()) != int(zero.sum()):
        raise ValueError('change_26w_pct may only be missing for zero-baseline tags')
    if len(recs) != 6:
        raise ValueError('expected 6 recommendations')
    if not set(recs.stakeholder).issubset(set(STAKEHOLDERS)):
        raise ValueError('recommendation uses an unknown stakeholder')
    if recs[['finding', 'time_series_evidence', 'text_mining_evidence', 'action',
             'kpi_to_track', 'caveat']].isna().any().any():
        raise ValueError('recommendations have empty cells')


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    matrix = build_insight_matrix()
    recs = build_recommendations(matrix)
    validate(matrix, recs)
    OUT_MATRIX.parent.mkdir(parents=True, exist_ok=True)
    matrix.to_csv(OUT_MATRIX, index=False)
    recs.to_csv(OUT_RECS, index=False)
    write_json(OUT_MANIFEST, {
        'generated_utc': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
        'rows': int(len(matrix)),
        'tags': list(matrix.tag),
        'pre_post_boundary': {'pre': '<= 2022-10', 'transition': '2022-11..2022-12', 'post': '>= 2023-01'},
        'units': {
            'frustration_*': 'percentage points',
            'complexity_prose_words_change': 'words (median)',
            'complexity_code_lines_change': 'lines (median)',
            'complexity_version_flag_change': 'percentage points (mean share)',
            'resolved_rate_*': 'fraction of questions resolved within 7 days, weighted by est_questions',
        },
        'inputs': [str(p.relative_to(ROOT)) for p in (
            TAGS_CSV, ITS_CSV, TONE_CSV, COMPLEXITY_CSV, TOPIC_PREPOST_CSV,
            TOPIC_LABELS_CSV, TOPIC_OUTCOMES_CSV, KEYWORDS_CSV, FORECASTS_CSV,
            MONTHLY_TAG_TABLES, SHAP_TOP_CSV)],
        'outputs': [str(OUT_MATRIX.relative_to(ROOT)), str(OUT_RECS.relative_to(ROOT))],
    })
    print(f'insight_matrix.csv: {len(matrix)} rows -> {OUT_MATRIX.relative_to(ROOT)}')
    print(f'recommendations.csv: {len(recs)} rows -> {OUT_RECS.relative_to(ROOT)}')
    print(matrix[['tag', 'forecast_class', 'its_slope_change_pct', 'frustration_change',
                  'resolved_rate_pre', 'resolved_rate_post']].to_string(index=False))


if __name__ == '__main__':
    main()
