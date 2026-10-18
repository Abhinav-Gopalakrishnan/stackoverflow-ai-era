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
    per_tag = pd.read_csv(TEXT/'topic_prepost_by_tag.csv')
    label_table = pd.read_csv(TOPIC_LABELS_CSV)
    allowed = set(label_table.loc[~label_table['mixed'].fillna(False).astype(bool), 'topic'])
    def for_tag(tag):
        table = per_tag[(per_tag.tag == tag) & per_tag.topic.isin(allowed)]
        rising = table[table.change > 0].nlargest(3,'change')
        falling = table[table.change < 0].nsmallest(3,'change')
        text = lambda rows: '; '.join(f'{labels[r.topic]} ({r.change*100:+.2f} pp)' for r in rows.itertuples())
        return text(rising), text(falling), f'weighted within-tag topic shifts ({tag}); automatic names'
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
    topics=pd.read_csv(TOPIC_PREPOST_CSV).merge(pd.read_csv(TOPIC_LABELS_CSV),on='topic')
    topics=topics[~topics['mixed'].fillna(False).astype(bool)]
    rise=topics.nlargest(1,'change').iloc[0]
    fall=topics.nsmallest(1,'change').iloc[0]
    outcome=pd.read_csv(TOPIC_OUTCOMES_CSV).set_index('topic').loc[rise.topic]
    tone=pd.read_csv(TONE_CSV).query("tag=='ALL' and measure=='frustration'").iloc[0]
    selected=pd.read_csv(TAGS_CSV).set_index('tag')
    site=selected.loc['ALL']
    bt=pd.read_csv(TS/'backtest_summary_matched.csv').query("model=='sarimax' and horizon==26").iloc[0]
    comp=pd.read_csv(COMPLEXITY_CSV).query("tag=='ALL' and statistic=='median'").set_index('metric')
    kw=pd.read_csv(KEYWORDS_CSV).query("tag_scope=='ALL' and direction=='rising'")
    kw=kw[~kw.term.astype(str).str.contains(r'(?:^|\s)(?:numbertoken|pathtoken|urltoken)(?:\s|$)',regex=True)].nlargest(3,'z_score')
    keyword_text='; '.join(f'{r.term} (z={r.z_score:.1f})' for r in kw.itertuples())
    oai=matrix.set_index('tag').loc['openai-api']
    steep=int(matrix.forecast_class.eq('steep decline').sum())
    rows=[
        dict(finding='Review workload by tag before changing resource allocation.',
            time_series_evidence=f'{steep}/13 study tags meet the fixed steep-decline forecast threshold; ALL changes {site.change_26w_pct:+.1f}% at 26 weeks.',
            text_mining_evidence=f'Global frustration-phrase share changes {tone.change*100:+.2f} pp (95% CI {tone.lower95*100:+.2f} to {tone.upper95*100:+.2f}).',
            action='Compare question counts, queue age and observed moderation workload monthly; pilot allocation changes only after measuring demand.',
            stakeholder='Q&A platform product team',kpi_to_track='Queue age and moderation hours per 1,000 questions',
            caveat='No staffing or effort data were collected; declining traffic does not itself imply less moderation demand.'),
        dict(finding='Test documentation topics suggested by changing vocabulary.',
            time_series_evidence=f'ALL validation-selected 26-week forecast is {site.forecast_week26:.1f} questions/week versus {site.last_week_count:.0f} last observed.',
            text_mining_evidence=f'Top global rising keywords: {keyword_text}.',
            action='Inspect linked questions for these keywords and trial a documentation guide with an explicit success measure.',
            stakeholder='DevRel teams',kpi_to_track='Guide use and repeat-question share before/after a controlled pilot',
            caveat='Keyword shifts are proxies, may reflect technical-token artifacts and do not establish documentation need.'),
        dict(finding='Pilot expert routing for a growing topic and measure resolution.',
            time_series_evidence=f'Python ITS growth-rate shift is {matrix.set_index("tag").loc["python","its_slope_change_pct"]:+.2f}%/week after the fixed launch boundary.',
            text_mining_evidence=f'{rise.final_name}: global share {rise.change*100:+.2f} pp; dominant-topic 7-day resolution {outcome.resolved_rate_7d:.1%} (n={int(outcome.n_questions):,}).',
            action='Use a small expert-routing pilot and compare outcomes against a contemporaneous control queue.',
            stakeholder='developer-forum managers',kpi_to_track='7-day resolution and median first-answer hours in pilot versus control',
            caveat='Automatic topic labels are provisional. A gain in global share does not demonstrate difficulty or migration from AI tools.'),
        dict(finding='Evaluate a clearer question template as an experiment.',
            time_series_evidence=f'ALL projected 26-week volume change is {site.change_26w_pct:+.1f}%; no intervention effect is estimated.',
            text_mining_evidence=f'Global weighted median prose changes {comp.loc["prose_words","change"]:+.0f} words and code {comp.loc["code_lines","change"]:+.0f} lines.',
            action='Trial prompts for expected behaviour, minimal code and version details, with a control group.',
            stakeholder='Q&A platform product team',kpi_to_track='Completion rate, question edits and 7-day resolution under random assignment',
            caveat='Longer text is not proof of greater difficulty. VADER and frustration flags are weak exploratory signals and should not gate users.'),
        dict(finding='Audit forecast calibration before setting automatic alerts.',
            time_series_evidence=f'SARIMAX 26-week matched-origin 95% coverage is {bt.coverage95:.1%}; skill versus naive is {bt.skill_vs_naive:.1%}.',
            text_mining_evidence=f'{fall.final_name} shows a global topic-share change of {fall.change*100:+.2f} pp.',
            action='Track live forecast errors and recalibrate intervals before using them as operational alert thresholds.',
            stakeholder='Q&A platform product team',kpi_to_track='Rolling 80/95% interval coverage and false-alert rate',
            caveat='Current intervals under-cover; their nominal label must not be interpreted as verified reliability.'),
        dict(finding='Monitor emerging tags without percentage classes from a zero baseline.',
            time_series_evidence=f'openai-api ITS level shift {oai.its_level_change_pct:+.1f}%; growth-rate shift {oai.its_slope_change_pct:+.2f}%/week; class: {oai.forecast_class}.',
            text_mining_evidence=f'openai-api within-tag topics: {oai.rising_topics}.',
            action='Review absolute counts and linked topic examples monthly before proposing specialist routing.',
            stakeholder='developer-forum managers',kpi_to_track='Absolute weekly questions and tag-specific resolution rate',
            caveat='Sparse tags and automatic labels make interpretation uncertain; a level step is not a sustained growth trend.')]
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
            'its_slope_change_pct': 'percent change in weekly growth rate',
            'complexity_prose_words_change': 'words (median)',
            'complexity_code_lines_change': 'lines (median)',
            'complexity_version_flag_change': 'percentage points (mean share)',
            'resolved_rate_*': 'fraction of questions resolved within 7 days, weighted by est_questions',
        },
        'inputs': [str(p.relative_to(ROOT)) for p in (
            TAGS_CSV, ITS_CSV, TONE_CSV, COMPLEXITY_CSV, TOPIC_PREPOST_CSV,
            TOPIC_LABELS_CSV, TOPIC_OUTCOMES_CSV, TEXT/'topic_prepost_by_tag.csv', KEYWORDS_CSV, FORECASTS_CSV,
            MONTHLY_TAG_TABLES, SHAP_TOP_CSV)],
        'outputs': [str(OUT_MATRIX.relative_to(ROOT)), str(OUT_RECS.relative_to(ROOT))],
    })
    print(f'insight_matrix.csv: {len(matrix)} rows -> {OUT_MATRIX.relative_to(ROOT)}')
    print(f'recommendations.csv: {len(recs)} rows -> {OUT_RECS.relative_to(ROOT)}')
    print(matrix[['tag', 'forecast_class', 'its_slope_change_pct', 'frustration_change',
                  'resolved_rate_pre', 'resolved_rate_post']].to_string(index=False))


if __name__ == '__main__':
    main()
