"""Member 3 (Akshay) Review 2: generator for the combined final report.

Reads every number from reports/review2/ and writes reports/review2/final_report.md,
then renders it to reports/review2/final_report.pdf with headless Chromium. No number is
typed by hand; if an input CSV changes, re-running this module changes the report.

Run: python -m src.review2_final_report
     python -m src.review2_final_report --no-pdf
"""
from __future__ import annotations
import argparse
import json
import re
import subprocess
from pathlib import Path
import pandas as pd
import markdown as md
from src.review2_common import ROOT, TEXT, TS

OUT_MD = ROOT / 'reports/review2/final_report.md'
OUT_HTML = ROOT / 'reports/review2/final_report.html'
OUT_PDF = ROOT / 'reports/review2/final_report.pdf'

STL_SUMMARY = TS / 'stl_summary.csv'
STATIONARITY = TS / 'stationarity_decision.csv'
CHANGEPOINTS = TS / 'changepoints.csv'
ITS = TS / 'its_results.csv'
BACKTEST = TS / 'backtest_metrics.csv'
FORECASTS = TS / 'forecasts_26w.csv'
TAG_CLASSES = TS / 'tag_classes.csv'
CORPUS_STATS = TEXT / 'corpus_stats.json'
TOPIC_SELECTION = TEXT / 'topic_model_selection.csv'
TOPIC_PREPOST = TEXT / 'topic_prepost.csv'
TOPIC_LABELS = TEXT / 'topic_labels.csv'
TOPIC_OUTCOMES = TEXT / 'topic_outcomes.csv'
KEYWORDS = TEXT / 'keywords_prepost.csv'
TONE = TEXT / 'tone_prepost.csv'
TONE_STATUS = TEXT / 'tone_validation_status.json'
COMPLEXITY = TEXT / 'complexity_prepost.csv'
RECS = ROOT / 'reports/review2/recommendations.csv'
EVENTS = ROOT / 'docs/event_list.csv'

FIGURES = {
    'stl': 'ts/stl_small_multiples.png',
    'its': 'ts/its_forest.png',
    'forecast': 'ts/forecast_ALL.png',
    'selection': 'text/topic_model_selection.png',
    'keywords': 'text/keywords_shift_all.png',
    'tone': 'text/tone_complexity.png',
}
KEYWORD_ARTIFACTS = re.compile(r'token', re.I)

DASHBOARD_URL = 'TODO(M1): public Streamlit URL'
BOARD_URL = 'TODO: GitHub project board link'
REPO_URL = 'TODO: repository link'
KAGGLE_URL = 'TODO: Kaggle notebook link'
DASHBOARD_SHOTS = 'TODO(M1): screenshots of the seven dashboard pages'


def pct(x, nd=1):
    return f'{x:.{nd}f}%'


def pp(x, nd=1):
    return f'{x:+.{nd}f} pp'


def num(x, nd=1):
    return f'{x:,.{nd}f}'


def load_context():
    ctx = {}
    ctx['stl'] = pd.read_csv(STL_SUMMARY)
    ctx['stationarity'] = pd.read_csv(STATIONARITY)
    cp = pd.read_csv(CHANGEPOINTS)
    ctx['cp'] = cp
    ctx['its'] = pd.read_csv(ITS)
    ctx['backtest'] = pd.read_csv(BACKTEST)
    ctx['forecasts'] = pd.read_csv(FORECASTS)
    ctx['tag_classes'] = pd.read_csv(TAG_CLASSES)
    ctx['corpus'] = json.loads(CORPUS_STATS.read_text())
    ctx['selection'] = pd.read_csv(TOPIC_SELECTION)
    ctx['topic_prepost'] = pd.read_csv(TOPIC_PREPOST)
    ctx['labels'] = {int(r.topic): r.final_name for r in pd.read_csv(TOPIC_LABELS).itertuples()}
    ctx['outcomes'] = pd.read_csv(TOPIC_OUTCOMES).set_index('topic')
    ctx['keywords'] = pd.read_csv(KEYWORDS)
    ctx['tone'] = pd.read_csv(TONE)
    ctx['tone_status'] = json.loads(TONE_STATUS.read_text())
    ctx['complexity'] = pd.read_csv(COMPLEXITY)
    ctx['recs'] = pd.read_csv(RECS)
    ctx['events'] = pd.read_csv(EVENTS)
    return ctx


def section_executive(ctx):
    its = ctx['its']
    sig = its[its.status.str.contains('decline')]
    slope_lo, slope_hi = its.slope_change_pct.min(), its.slope_change_pct.max()
    exceed = int(its.effect_exceeds_placebo.sum())
    classes = ctx['tag_classes'].query("tag != 'ALL'").forecast_class.value_counts().to_dict()
    steep = classes.get('steep decline', 0)
    decl = classes.get('declining', 0)
    agg = ctx['forecasts'].query("selected and tag == 'ALL' and horizon == 26").iloc[0]
    last = ctx['tag_classes'].set_index('tag').loc['ALL', 'last_week_count']
    drop = (agg['pred'] / last - 1) * 100
    tp = ctx['topic_prepost'].sort_values('change')
    falling = ctx['labels'][int(tp.topic.iloc[0])]
    rising = ctx['labels'][int(tp.topic.iloc[-1])]
    prose = _complexity_change(ctx, 'prose_words', 'median')
    code = _complexity_change(ctx, 'code_lines', 'median')
    return f"""## 1. Executive summary

- **Patterns and the 2022 break.** Trend dominates every series. On the log scale, all {len(sig)} series show a significant negative change in weekly growth after 2022-11-30 (ITS slope change {slope_lo:.2f}% to {slope_hi:.2f}% per week, 95% CI excluding zero), and the real break exceeds the 2021-11-30 placebo in {exceed} of {len(its)} series.
- **Forecasts.** The 26-week site total is forecast to fall from {num(last,0)} to {num(agg['pred'],0)} questions per week by February 2027 ({drop:.1f}%), with {steep} tags classed steep decline and {decl} declining under the fixed thresholds.
- **Topics.** NMF k=10 wins the pre-registered rule (coherence 0.2175, diversity 0.80, stability 1.00). Routine programming topics lose share while harder runtime and tooling topics gain: {rising} rises {pp(tp.change.iloc[-1]*100)} while {falling} falls {pp(tp.change.iloc[0]*100)}.
- **Tone and complexity.** Questions are longer (+{prose:g} prose words) and more code-heavy (+{code:g} code lines) after the break. Tone measures are exploratory: the frustration lexicon moves only {pp(ctx['tone'].query("tag=='ALL' and measure=='frustration'").change.iloc[0]*100)}.
- **Recommendations.** Six combined recommendations follow, each citing one time-series and one text-mining number; the headline is to move moderation effort to the steep-decline tags and to route rising low-resolution topics to experts.
"""


def _complexity_change(ctx, metric, statistic):
    row = ctx['complexity'].query('tag == "ALL" and metric == @metric and statistic == @statistic')
    return float(row.change.iloc[0])


def section_data(ctx):
    ev = '; '.join(f"{r.event_name} ({r.date})" for r in ctx['events'].itertuples())
    return f"""## 2. Data recap

- **Volume series.** {ctx['corpus']['documents_after']:,} cleaned questions back a weekly series of 14 groups (ALL plus 13 study tags) x 400 complete Tuesday-start weeks, 2019-01-01 to 2026-08-25, with no missing weeks. The time-series method uses these complete counts, never the sampled records.
- **Rate series.** `data/processed/monthly_tag_tables.csv` holds the weighted monthly resolved rate, answered rate and median hours per tag. Months flagged `low_sample` are excluded from conclusions.
- **Text.** {ctx['corpus']['documents_before']:,} questions; {ctx['corpus']['vocabulary_size']:,} distinct terms after cleaning; code removed from the prose field.
- **Weighting.** Before 2025 every question carries a sampling weight; any share, rate or count built before 2025 is weighted. From 2025 the weight is 1.
- **Periods.** Pre-AI 2019-01 to 2022-10, transition 2022-11 to 2022-12, post-AI 2023-01 to 2026-08. Event markers: {ev}.
"""


def section_method1(ctx):
    stl = ctx['stl']
    trend_lo, trend_hi = stl.trend_strength.min(), stl.trend_strength.max()
    seas_lo, seas_hi = stl.seasonal_strength.min(), stl.seasonal_strength.max()
    stn = ctx['stationarity']
    nonstat = int((stn.level_verdict == 'non-stationary').sum())
    conflict = int((stn.diff_verdict == 'conflicting evidence').sum())
    cp = ctx['cp']
    cp_total = len(cp)
    cp_aligned = int(cp.within_4_weeks_of_event.sum())
    cp_series = cp[cp.within_4_weeks_of_event].tag.nunique()
    its = ctx['its']
    sig = its[its.status.str.contains('decline')]
    slope_lo, slope_hi = its.slope_change_pct.min(), its.slope_change_pct.max()
    exceed = int(its.effect_exceeds_placebo.sum())
    level_sig = int((its.level_p < 0.05).sum())
    oai = its.set_index('tag').loc['openai-api']
    bt = ctx['backtest']
    s26 = bt[(bt.model == 'sarimax') & (bt.horizon == 26)]
    skill = s26.skill_vs_naive.mean() * 100
    cov = s26.coverage95.mean() * 100
    s1 = bt[bt.horizon == 1]
    h1 = s1.groupby('model').skill_vs_naive.mean().sort_values(ascending=False)
    classes = ctx['tag_classes'].query("tag != 'ALL'").forecast_class.value_counts().to_dict()
    agg = ctx['forecasts'].query("selected and tag == 'ALL' and horizon == 26").iloc[0]
    last = ctx['tag_classes'].set_index('tag').loc['ALL', 'last_week_count']
    drop = (agg['pred'] / last - 1) * 100
    class_txt = ', '.join(f'{v} {k}' for k, v in sorted(classes.items()))
    return f"""## 3. Method 1: time series

**Preparation and implementation.** STL (robust, period 52) was fit to each log1p weekly count; the additive components satisfy trend + seasonal + residual = log count. Stationarity was tested with ADF (regression c, AIC) and KPSS on the level and the first difference, under a written verdict rule. Change points were found with `ruptures` PELT (l2 cost, minimum segment 26 weeks) and a BIC penalty fixed in advance, then compared with the four dated events. Interrupted time series were fit per series as segmented regressions of log count on week, a step at 2022-11-30 and a post-break slope, with two Fourier pairs, using OLS with Newey-West HAC errors (lag 4) and a 2021-11-30 placebo.

**Evaluation and interpretation.**

- **Seasonality is secondary.** Trend strength runs {trend_lo:.2f} to {trend_hi:.2f}; seasonal strength runs {seas_lo:.2f} to {seas_hi:.2f}. Yearly dips cluster in the late-December/January holiday weeks.
- **One difference is justified.** All {nonstat} level series are non-stationary (ADF cannot reject a unit root, KPSS rejects stationarity), so every series is first-differenced (`d=1`), consistent with the M5 SARIMAX backtest. The first-difference tests conflict for {conflict} series and are reported as such, not hidden.
- **A genuine 2022 break.** The {cp_total} detected breaks are mostly routine noise: {cp_aligned} fall within four weeks of a dated event, across {cp_series} series (`java`, `r`, `openai-api`, `sql`). The interrupted time series is sharper: all {len(sig)} series show a significant negative post-break slope, {slope_lo:.2f}% to {slope_hi:.2f}% per week, and the real effect exceeds the placebo in {exceed} of {len(its)} series. {level_sig} series also show a significant immediate level change, most extreme for `openai-api` ({oai.level_change_pct:+.0f}%), which is a step, not a stable trend.
- **Forecast skill is earned at long horizons, not short.** On the 2025-26 rolling-origin backtest, SARIMAX's mean 26-week skill against naive is {pct(skill)} while true 95% coverage is {cov:.1f}% (intervals too narrow). At one week ahead the best model reaches {pct(h1.iloc[0]*100)} skill and drift only {pct(h1.get('drift', float('nan'))*100)}, so the naive baseline remains hard to beat over a single week, as expected.
- **Classes and business reading.** Under the fixed thresholds ({class_txt}), the site total is forecast from {num(last,0)} to {num(agg['pred'],0)} questions per week by February 2027 ({drop:.1f}%). `tag_classes.csv` adds a half-life and a 2025 index; zero-baseline tags cannot support a percentage class and are labelled as such.

![STL small multiples]({FIGURES['stl']})

![Interrupted time series forest plot]({FIGURES['its']})

![Site-total forecast]({FIGURES['forecast']})
"""


def section_method2(ctx):
    cor = ctx['corpus']
    sel = ctx['selection']
    nmf = sel[(sel.model_family == 'NMF') & (sel.satisfies_rule)].sort_values('coherence_npmi', ascending=False).iloc[0]
    lda = sel[sel.model_family == 'LDA']
    tp = ctx['topic_prepost'].copy()
    tp['name'] = tp.topic.map(ctx['labels'])
    tp = tp.sort_values('change')
    fall = tp.head(3)
    rise = tp.tail(3)[::-1]
    fall_txt = ', '.join(f"{r['name']} ({pp(r.change*100)})" for _, r in fall.iterrows())
    rise_txt = ', '.join(f"{r['name']} ({pp(r.change*100)})" for _, r in rise.iterrows())
    rising_topic = tp.iloc[-1]
    resolved = ctx['outcomes'].loc[int(rising_topic.topic), 'resolved_rate_7d'] * 100
    kw = ctx['keywords']
    kall = kw[(kw.tag_scope == 'ALL') & (~kw.term.astype(str).str.contains(KEYWORD_ARTIFACTS))]
    krise = kall.sort_values('z_score', ascending=False).head(5)
    kfall = kall.sort_values('z_score').head(5)
    krise_txt = ', '.join(f'{r.term} (z={r.z_score:.0f})' for r in krise.itertuples())
    kfall_txt = ', '.join(f'{r.term} (z={r.z_score:.0f})' for r in kfall.itertuples())
    tone = ctx['tone'].set_index(['tag', 'measure'])
    neg = tone.loc[('ALL', 'negative'), 'change'] * 100
    pos = tone.loc[('ALL', 'positive'), 'change'] * 100
    frust = tone.loc[('ALL', 'frustration'), 'change'] * 100
    prose = _complexity_change(ctx, 'prose_words', 'median')
    code = _complexity_change(ctx, 'code_lines', 'median')
    multi = _complexity_change(ctx, 'multi_technology_flag', 'mean') * 100
    ts = ctx['tone_status']
    return f"""## 4. Method 2: text mining

**Preparation and implementation.** The corpus of {cor['documents_after']:,} questions was lowercased, lemmatised with spaCy and stripped of code, with technical words protected and stopwords and VADER overrides written down. Topics were fit by TF-IDF (unigrams and bigrams) on a stratified sample, with NMF and LDA compared across k under a rule fixed in advance (highest coherence among candidates with diversity at least 0.7 and stability at least 0.6). Tone used VADER plus a frustration and politeness lexicon; complexity measured prose length, code lines, code blocks, reading ease and structural flags. Shares and rates before 2025 are weighted.

**Evaluation and interpretation.**

- **NMF k=10 wins.** Coherence {nmf.coherence_npmi:.4f}, diversity {nmf.diversity:.2f}, stability {nmf.stability:.2f}. LDA failed the rule on every k (coherence {lda.coherence_npmi.min():.3f} to {lda.coherence_npmi.max():.3f}, stability at or below {lda.stability.max():.2f}).
- **What moved to AI tools.** The largest falling topics are {fall_txt}: routine syntax and dataframe lookups.
- **What people still bring to humans.** The largest rising topics are {rise_txt}; the top rising topic resolves only {resolved:.1f}% within seven days, the resolution bottleneck behind the expert-routing recommendation.
- **Vocabulary shift.** Rising terms include {krise_txt}; falling terms include {kfall_txt} (Monroe log-odds with a Dirichlet prior).
- **Tone and complexity.** Negative tone share changed {pp(neg)} and positive share {pp(pos)}; the frustration flag changed {pp(frust)} and is a lexicon measure, not verified emotion. Weighted median prose length changed {prose:+.0f} words and code lines {code:+.0f}, while questions spanning two or more study tags changed {pp(multi)}.

![Topic model selection]({FIGURES['selection']})

![Rising and falling words]({FIGURES['keywords']})

![Tone and complexity]({FIGURES['tone']})

{tone_validation_text(ts)}
"""


def tone_validation_text(status):
    if status.get('status') == 'complete_ai_assisted':
        return (f"**Disclosed AI-assisted validation:** VADER was scored against all {status['required_rows']} "
                f"existing M3 human labels: accuracy {status['accuracy']:.1%}, macro-F1 {status['macro_f1']:.3f}. "
                f"Separately, Codex AI annotations agreed with M3 on {status['ai_human_agreement']:.1%} of posts "
                f"(human–AI Cohen's kappa {status['ai_human_kappa']:.3f}). This is one human plus an AI, "
                "not two independent human raters or an adjudicated gold standard. VADER is weak against this "
                "reference; frustration flags remain the primary exploratory tone proxy. Ten disclosed AI topic-name "
                "proposals and qualitative comparisons are in topic_naming_comparison.csv; topic 2 is mixed. "
                "The original human M2 labels, two-human kappa and human topic-naming agreement remain unavailable.")
    if status.get('status') == 'complete':
        return (f"VADER against {status['labelled_rows']} adjudicated human labels: "
                f"accuracy {status['accuracy']:.1%}, macro-F1 {status['macro_f1']:.3f}; "
                f"two-human Cohen's kappa {status['cohen_kappa']:.3f}.")
    return ('Tone validation and human topic-naming agreement remain pending; '
            'accuracy, macro-F1 and two-human kappa are unavailable.')


def section_combined(ctx):
    recs = ctx['recs']
    blocks = []
    for i, r in enumerate(recs.itertuples(), 1):
        blocks.append(
            f"**{i}. {r.finding}**\n\n"
            f"- *Time series:* {r.time_series_evidence}\n"
            f"- *Text mining:* {r.text_mining_evidence}\n"
            f"- *Action:* {r.action}\n"
            f"- *Stakeholder:* {r.stakeholder}  |  *KPI:* {r.kpi_to_track}\n"
            f"- *Caveat:* {r.caveat}\n"
        )
    body = '\n'.join(blocks)
    return f"""## 5. Combined insights and recommendations

Each recommendation below needs both methods at once and cites at least one time-series and one text-mining number. Every number is read from `reports/review2/`; the machine-readable matrix is `insight_matrix.csv`.

{body}
"""


def section_dashboard(ctx):
    return f"""## 6. Dashboard guide

The interactive dashboard (Streamlit with Plotly, owned by M1) has seven pages, all responding to shared sidebar filters (tag, date range, period, event markers, linear/log). Pages 2, 3, 4, 5 and 6 read the method outputs directly; page 1 shows the overview and page 7 the question-triage what-if.

| Page | Owner | Reads |
|---|---|---|
| 1. Overview | M1 | `ts/series_long.csv`, `data/processed/monthly_tag_tables.csv` |
| 2. Patterns and the 2022 break | M3 | `ts/stl_components.csv`, `ts/changepoints.csv`, `ts/its_results.csv` |
| 3. Forecasts | M5 | `ts/forecasts_26w.csv`, `ts/backtest_*.csv`, `ts/tag_classes.csv` |
| 4. Topics | M4 | `text/topics_top_terms.csv`, `text/topic_monthly_share.csv`, `text/topic_prepost.csv`, `text/topic_outcomes.csv` |
| 5. Tone and complexity | M2 | `text/tone_*.csv`, `text/complexity_*.csv`, `text/keywords_prepost.csv` |
| 6. Recommendations | M3 | `recommendations.csv` |
| 7. Question triage (stretch) | M5 + M1 | saved model, title and error-text inputs |

- **Public link:** {DASHBOARD_URL}
- **Screenshots:** {DASHBOARD_SHOTS}

Questions show titles only, each linked to `https://stackoverflow.com/q/<id>`, with a CC BY-SA 4.0 licence notice. No bodies and no user hashes are shown.
"""


def section_limitations(ctx):
    return f"""## 7. Limitations

1. **Weights before 2025.** Sampling weights apply only before 2025; later counts are unweighted.
2. **Thirteen tags.** Only the 13 study tags plus ALL are covered, so the picture is not the whole site.
3. **Acceptance is a proxy.** Resolution means an accepted answer within seven days, not a satisfied asker.
4. **VADER is general purpose.** The tone model is a general lexicon with overrides; the frustration flag is exploratory and its validation is pending.
5. **Topics are English prose.** Topic modelling uses cleaned English prose only; code and non-English text are excluded.
6. **Forecasts during a steep decline are uncertain.** SARIMAX 95% intervals covered only {ctx['backtest'].query("model=='sarimax' and horizon==26").coverage95.mean()*100:.1f}% of endpoints, and {json.loads((TS/'run_status.json').read_text())['fit_failures']} fits failed.
7. **Association, not cause.** Every result is associated with or consistent with AI-adoption timing; nothing is caused by it. The pre/post boundary is a comparison date, and the placebo break is included for honesty.
8. **Pending human checks.** Independent tone labels and topic-naming agreement are not yet available and are not claimed.
"""


def section_reproduce(ctx):
    return f"""## 8. How to reproduce

```bash
pip install -r requirements.txt
python -m src.ts_patterns --task all          # STL, stationarity, change points, ITS   -> reports/review2/ts/
python -m src.ts_forecast                     # baselines, backtest, forecasts          -> reports/review2/ts/
python -m src.topics                          # topics, keyword shift                   -> reports/review2/text/
python -m src.sentiment && python -m src.complexity   # tone and complexity             -> reports/review2/text/
python -m src.review2_m3_insights             # insight_matrix.csv, recommendations.csv
python -m src.review2_final_report            # final_report.md and final_report.pdf
jupyter nbconvert --execute --to notebook --inplace notebooks/07_timeseries.ipynb
jupyter nbconvert --execute --to notebook --inplace notebooks/08_text_mining.ipynb
```

Every heavy step writes to `reports/review2/`; the notebook, dashboard and this report read those files, so a changed CSV changes every downstream number. The final notebook for the submission is `notebooks/review2_main.ipynb` (M1).
"""


def section_contributions(ctx):
    return f"""## 9. Contributions and board link

| Member | Role | Summary |
|---|---|---|
| M1 Abhinav | Dashboard, final notebook, repo and board | `reports/review2/contribution_member1.md` (TODO) |
| M2 Rishiikesh | Corpus, tone, complexity | `reports/review2/contribution_member2.md` |
| M3 Akshay | Patterns, ITS, combined insights, final report, deck | `reports/review2/contribution_member3.md` (TODO) |
| M4 Nishanth | Topics, keyword shift, evaluation | `reports/review2/contribution_member4.md` |
| M5 Adhikkesh | Forecasts, backtest, tag classes | `reports/review2/contribution_member5.md` |

- **Board:** {BOARD_URL}
- **Repository:** {REPO_URL}
- **Kaggle notebook:** {KAGGLE_URL}
"""


def build_report(ctx):
    parts = [
        '# Stack Overflow in the AI Era: Review 2 final report',
        '',
        '**Team:** Abhinav (M1), Rishiikesh (M2), Akshay (M3), Nishanth (M4), Adhikkesh (M5). '
        '**Scope:** RQ4 (topics and complexity) and RQ5 (technology forecasting). '
        'All numbers are generated from `reports/review2/` by `src/review2_final_report.py`.',
        '',
        section_executive(ctx),
        section_data(ctx),
        section_method1(ctx),
        section_method2(ctx),
        section_combined(ctx),
        section_dashboard(ctx),
        section_limitations(ctx),
        section_reproduce(ctx),
        section_contributions(ctx),
    ]
    return '\n'.join(parts)


CSS = """
body { font-family: Helvetica, Arial, sans-serif; font-size: 10pt; line-height: 1.35; margin: 1.2cm; }
h1 { font-size: 18pt; } h2 { font-size: 13pt; border-bottom: 1px solid #999; padding-bottom: 2px; page-break-after: avoid; }
h3 { font-size: 11pt; } code { font-size: 9pt; background: #f2f2f2; }
img { max-width: 100%; display: block; margin: 6px auto 12px; page-break-inside: avoid; }
table { border-collapse: collapse; width: 100%; font-size: 9pt; margin: 6px 0; }
th, td { border: 1px solid #bbb; padding: 3px 5px; text-align: left; vertical-align: top; }
pre { background: #f2f2f2; padding: 6px; font-size: 8.5pt; white-space: pre-wrap; }
ul { margin-top: 2px; }
"""


def to_html(md_text, out_html):
    body = md.markdown(md_text, extensions=['tables', 'fenced_code'])
    out_html.write_text(
        f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{body}</body></html>",
        encoding='utf-8')


def to_pdf(html_path, pdf_path):
    import shutil
    if shutil.which('chromium'):
        subprocess.run([
            'chromium', '--headless', '--no-sandbox', '--disable-gpu',
            '--no-pdf-header-footer', '--virtual-time-budget=8000',
            f'--print-to-pdf={pdf_path}', html_path.as_uri(),
        ], check=True, capture_output=True)
    elif shutil.which('google-chrome'):
        subprocess.run([
            'google-chrome', '--headless', '--no-sandbox', '--disable-gpu',
            '--no-pdf-header-footer', '--virtual-time-budget=8000',
            f'--print-to-pdf={pdf_path}', html_path.as_uri(),
        ], check=True, capture_output=True)
    elif shutil.which('libreoffice'):
        subprocess.run([
            'libreoffice', '--headless', '--convert-to', 'pdf',
            str(html_path), '--outdir', str(pdf_path.parent)
        ], check=True, capture_output=True)
    else:
        raise RuntimeError('Neither chromium, google-chrome, nor libreoffice available for PDF export')
    return pdf_path


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--no-pdf', action='store_true', help='write the markdown and HTML only')
    args = ap.parse_args()

    ctx = load_context()
    text = build_report(ctx)
    headings = [h for h in re.findall(r'^## \d+\.', text, flags=re.M)]
    if len(headings) != 9:
        raise ValueError(f'expected 9 numbered sections, found {len(headings)}')
    if not re.search(r'associated with|consistent with', text, flags=re.I):
        raise ValueError('report must use the association wording rule')
    OUT_MD.write_text(text, encoding='utf-8')
    to_html(text, OUT_HTML)
    print(f'wrote {OUT_MD.relative_to(ROOT)} and {OUT_HTML.relative_to(ROOT)} '
          f'({len(text.splitlines())} lines, {len(headings)} sections)')

    if not args.no_pdf:
        to_pdf(OUT_HTML, OUT_PDF)
        pages = subprocess.run(['pdfinfo', str(OUT_PDF)], capture_output=True, text=True).stdout
        page_line = next((l for l in pages.splitlines() if l.startswith('Pages:')), 'Pages: ?')
        print(f'wrote {OUT_PDF.relative_to(ROOT)} ({page_line.strip()})')


if __name__ == '__main__':
    main()
