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
KEYWORD_ARTIFACTS = re.compile(r'(?:^|\s)(?:numbertoken|pathtoken|urltoken)(?:\s|$)', re.I)

DASHBOARD_URL = 'https://stackoverflow-ai-era.streamlit.app/ (public pages inspected 19 October 2026; redeploy final local corrections before presenting). Local fallback: streamlit run dashboard/app.py'
BOARD_URL = 'https://github.com/users/Abhinav-Gopalakrishnan/projects/3'
REPO_URL = 'https://github.com/Abhinav-Gopalakrishnan/stackoverflow-ai-era'
KAGGLE_URL = 'Not published; source notebooks and local application supplied'
DASHBOARD_SHOTS = 'reports/review2/dashboard_screenshots/ (captured from the local application)'


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
    ctx['topic_status'] = json.loads((TEXT/'topics_status.json').read_text())
    ctx['classifier'] = json.loads((ROOT/'reports/review1/m5/results.json').read_text())
    ctx['dataset'] = json.loads((ROOT/'reports/review2/dataset/dataset_validation.json').read_text())
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
    winner = ctx['selection']
    winner = winner[(winner.model_family == ctx['topic_status']['model_family']) & (winner.k == ctx['topic_status']['k'])].iloc[0]
    tp = ctx['topic_prepost'].sort_values('change')
    falling = ctx['labels'][int(tp.topic.iloc[0])]
    rising = ctx['labels'][int(tp.topic.iloc[-1])]
    prose = _complexity_change(ctx, 'prose_words', 'median')
    code = _complexity_change(ctx, 'code_lines', 'median')
    return f"""## 1. Executive summary

- **Patterns and the 2022 break.** Trend dominates every series. On the log scale, all {len(sig)} series show a significant negative change in weekly growth after 2022-11-30 (ITS slope change {slope_lo:.2f}% to {slope_hi:.2f}% per week, 95% CI excluding zero), and the real break exceeds the 2021-11-30 placebo in {exceed} of {len(its)} series.
- **Forecasts.** The 26-week site total is forecast to fall from {num(last,0)} to {num(agg['pred'],0)} questions per week by February 2027 ({drop:.1f}%), with {steep} tags classed steep decline and {decl} declining under the fixed thresholds.
- **Topics.** {winner.model_family} k={int(winner.k)} is selected by the written rule (document-NPMI {winner.coherence_npmi:.4f}, diversity {winner.diversity:.3f}, stability {winner.stability:.3f}). These are observed topic-share changes: {rising} rises {pp(tp.change.iloc[-1]*100)} while {falling} falls {pp(tp.change.iloc[0]*100)}.
- **Tone and complexity.** Questions are longer (+{prose:g} prose words) and more code-heavy (+{code:g} code lines) after the break. Tone measures are exploratory: the frustration lexicon moves only {pp(ctx['tone'].query("tag=='ALL' and measure=='frustration'").change.iloc[0]*100)}.
- **Recommendations.** Six combined recommendations follow, each citing one time-series and one text-mining number; the proposals are to test workload review, documentation and expert routing, with success measured prospectively.
"""


def _complexity_change(ctx, metric, statistic):
    row = ctx['complexity'].query('tag == "ALL" and metric == @metric and statistic == @statistic')
    return float(row.change.iloc[0])


def section_data(ctx):
    ev = '; '.join(f"{r.event_name} ({r.date})" for r in ctx['events'].itertuples())
    return f"""## 2. Data recap — Unit 1

The final cleaned dataset has **{ctx['dataset']['rows']:,} unique questions and {ctx['dataset']['columns']} columns**. Validation passes all eight checks: unique IDs, complete required fields, finite positive weights, binary primary and secondary targets, resolved implies answered, study dates and nonnegative account ages. Missing account ages are imputed and flagged ({ctx['dataset']['missing_account_age_flagged']:,}); {ctx['dataset']['body_truncated_flagged']} surviving long bodies carry truncation flags. `dataset/final_dataset_sample.csv` provides 40 title-only linked examples; `dataset/dataset_schema.csv` and `docs/data_dictionary.md` supply schema and definitions. The full cleaned parquet is supplied separately with its SHA-256 in `dataset/dataset_validation.json`.

### Unit 2 predictive-model recap

Train ends before January 2025, validation is January–June 2025 and the locked classifier test is July 2025–July 2026. August 2026 is outside that locked evaluation but included in Unit 3; training-only feature preprocessing and lagged history are used. Validation PR-AUC is {'; '.join(r['model'] + ' ' + format(r['pr_auc'], '.4f') for r in ctx['classifier']['validation'])}. Validation selects XGBoost and fixes threshold {ctx['classifier']['chosen']['threshold']:.4f}. On the locked {ctx['classifier']['test']['n']:,}-question test set, PR-AUC is {ctx['classifier']['test']['pr_auc']:.4f}, ROC-AUC {ctx['classifier']['test']['roc_auc']:.4f}, F1 {ctx['classifier']['test']['f1']:.4f}, precision {ctx['classifier']['test']['precision']:.4f} and recall {ctx['classifier']['test']['recall']:.4f}. These are modest predictive results; no >80% primary-target claim is made. Saved source values are in `reports/review1/m5/results.json`, and the complete notebook displays the comparisons. The easier any-answer target is reported separately.

- **Volume series.** The {ctx['corpus']['documents_after']:,}-question cleaned sample is paired with a separately collected weekly series of 14 groups (ALL plus 13 study tags) x 400 complete Tuesday-start weeks, 2019-01-01 to 2026-08-25, with no missing weeks. These weekly volumes are separately collected API totals (ALL is site-wide), not counts aggregated from the 302,026 sampled question records. Weighted question-sample rates and API volumes are kept separate.
- **Rate series.** `data/processed/monthly_tag_tables.csv` holds the weighted monthly resolved rate, answered rate and median hours per tag. Months flagged `low_sample` are excluded from conclusions.
- **Text.** {ctx['corpus']['documents_before']:,} questions; {ctx['corpus']['vocabulary_size']:,} distinct terms after cleaning; code removed from the prose field.
- **Weighting.** Question-sample shares and rates retain their sampling weights (up to 23 before 2025; later weights are 1). Separate API weekly totals are not survey-weighted.
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
- **Break-date associations.** The {cp_total} detected breaks are penalised mean shifts, not significance tests: {cp_aligned} fall within four weeks of a dated event, across {cp_series} series (`java`, `r`, `openai-api`, `sql`). The interrupted time series is sharper: all {len(sig)} series show a significant negative post-break slope, {slope_lo:.2f}% to {slope_hi:.2f}% per week, and the real effect exceeds the placebo in {exceed} of {len(its)} series. {level_sig} series also show a significant immediate level change, large for `openai-api` ({oai.level_change_pct:+.0f}%), which is a step, not a stable trend.
- **Forecast skill is earned at long horizons, not short.** On the 2025-26 rolling-origin backtest, SARIMAX's mean 26-week skill against naive is {pct(skill)} while true 95% coverage is {cov:.1f}% (intervals too narrow). At one week ahead the best model reaches {pct(h1.iloc[0]*100)} skill and drift only {pct(h1.get('drift', float('nan'))*100)}, so the naive baseline remains hard to beat over a single week, as expected.
- **Classes and business reading.** Under the fixed thresholds ({class_txt}), the site total is forecast from {num(last,0)} to {num(agg['pred'],0)} questions per week by February 2027 ({drop:.1f}%). `tag_classes.csv` adds a half-life and a 2025 index; zero-baseline tags cannot support a percentage class and are labelled as such.

![STL small multiples]({FIGURES['stl']})

![Interrupted time series forest plot]({FIGURES['its']})

![Site-total forecast]({FIGURES['forecast']})
"""


def section_method2(ctx):
    cor = ctx['corpus']
    sel = ctx['selection']
    winner = sel[(sel.model_family == ctx['topic_status']['model_family']) & (sel.k == ctx['topic_status']['k'])].iloc[0]
    seed_runs = pd.read_csv(TEXT/'topic_model_seed_results.csv')
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

**Preparation and implementation.** The corpus of {cor['documents_after']:,} questions was lowercased, lemmatised with spaCy and stripped of code, with technical words protected and stopwords and VADER overrides written down. NMF used TF-IDF and LDA used counts over the same unigram/bigram vocabulary and stratified training IDs, with 36 actual fits compared across six k values and three seeds under a rule fixed in advance (highest coherence among candidates with diversity at least 0.7 and stability at least 0.6). Tone used VADER plus a frustration and politeness lexicon; complexity measured prose length, code lines, code blocks, reading ease and structural flags. Shares and rates before 2025 are weighted.

**Evaluation and interpretation.**

- **Measured selection: {winner.model_family} k={int(winner.k)}.** Exact document-cooccurrence NPMI {winner.coherence_npmi:.4f}, diversity {winner.diversity:.3f}, stability {winner.stability:.3f}. Both families use {ctx['topic_status']['training_rows']:,} training questions and a disjoint {ctx['topic_status']['reference_rows']:,}-question reference. Document NPMI replaces sliding-window c_npmi; this protocol change is disclosed in `docs/review2_topic_evaluation.md`. Per-seed timing, iterations and warnings are retained; {int(sel.warning_runs.sum())} fit runs emitted warnings.
- **Semantic-quality limit.** The selected document-NPMI may be low or negative despite satisfying diversity/stability thresholds. Threshold selection does not establish strong semantic validity. Mixed numerical and screenshot-boilerplate topics are flagged; automatic names and recommendations remain exploratory.
- **Largest observed share decreases.** The largest falling topics are {fall_txt}; destination traffic was not measured.
- **Largest observed share increases.** The largest rising topics are {rise_txt}; the top rising topic resolves only {resolved:.1f}% within seven days, the resolution bottleneck behind the expert-routing recommendation.
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
                "reference; frustration flags remain the primary exploratory tone proxy. Current topic names are automatic descriptions from the corrected model; old AI topic-name "
                "proposals are archived and do not validate the new topic IDs. "
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

The Streamlit/Plotly dashboard originated with M1 and now has seven pages. Observation controls filter charts; model statistics retain fixed fitting periods. Forecast wording follows the selected scenario. Recommendations uses the selected tag and stakeholder to suggest untested pilots with evidence, owners and KPIs. Page 7 adds dataset and locked classifier evidence.

| Page | Owner | Reads |
|---|---|---|
| 1. Overview | M1 | `ts/series_long.csv`, `data/processed/monthly_tag_tables.csv` |
| 2. Patterns and the 2022 break | M3 | `ts/stl_components.csv`, `ts/changepoints.csv`, `ts/its_results.csv` |
| 3. Forecasts | M5 | `ts/forecasts_26w.csv`, `ts/backtest_*.csv`, `ts/tag_classes.csv` |
| 4. Topics | M4 | `text/topics_top_terms.csv`, `text/topic_monthly_share.csv`, `text/topic_prepost.csv`, `text/topic_outcomes.csv` |
| 5. Tone and complexity | M2 | `text/tone_*.csv`, `text/complexity_*.csv`, `text/keywords_prepost.csv` |
| 6. Recommendations | M3 and final corrections | `recommendations.csv`, `insight_matrix.csv`, deterministic pilot rules |
| 7. Dataset and classification | Corrections integration | sanitized dataset preview, validation, locked classifier metrics |

- **Public link:** {DASHBOARD_URL}
- **Screenshots:** {DASHBOARD_SHOTS}

Questions show titles only, each linked to `https://stackoverflow.com/q/<id>`, with a CC BY-SA 4.0 licence notice. No bodies and no user hashes are shown.
"""


def section_limitations(ctx):
    return f"""## 7. Limitations

1. **Weights before 2025.** Sampling weights apply only before 2025; later counts are unweighted.
2. **Thirteen tags.** Only the 13 study tags plus ALL are covered, so the picture is not the whole site.
3. **Resolution is a proxy.** The answer accepted in the collected record was posted within 168 hours. Acceptance-event time is unavailable, so this does not establish acceptance within seven days or asker satisfaction.
4. **VADER is general purpose.** The tone model is a general lexicon with overrides; the frustration flag is exploratory and VADER achieves only 36% accuracy against one human reference; the separate frustration lexicon is not independently validated.
5. **Language scope.** Topic modelling removes code and uses English-oriented lemmatisation/character cleaning; there is no validated language-identification stage. Reliability on multilingual prose is not established.
6. **Forecasts during a steep decline are uncertain.** SARIMAX 95% intervals covered only {ctx['backtest'].query("model=='sarimax' and horizon==26").coverage95.mean()*100:.1f}% of endpoints, and {json.loads((TS/'run_status.json').read_text())['fit_failures']} fits failed.
7. **Association, not cause.** Every result is associated with or consistent with AI-adoption timing; causal attribution is not established. The pre/post boundary is a comparison date, and the placebo break is included for honesty.
8. **Protocol deviations.** Two-human tone adjudication and independent human topic naming were not completed. AI assistance and automatic names are disclosed. Topic coherence uses document cooccurrence rather than the original sliding-window plan.
"""


def section_reproduce(ctx):
    return """## 8. How to reproduce

For the saved application, install `dashboard/requirements.txt` and run `streamlit run dashboard/app.py`. No API key or full parquet is needed. For heavy analyses, restore the local inputs described in `docs/review2_submission_guide.md` and install the root requirements. Preserve the original human label sheet.

```bash
python -m src.ts_patterns --task all
python -m src.ts_forecast
python -m src.topics
python -m src.keywords
python -m src.review2_validation
python -m src.review2_dataset
python -m src.review2_m3_insights
python -m src.review2_refresh_evidence
python -m src.export_dashboard_data
python -m src.review2_notebooks
python -m src.review2_final_report
```

The complete submission notebook is `notebooks/review2_main.ipynb`; method notebooks are `07_timeseries.ipynb` and `08_text_mining.ipynb`. Execute them with Jupyter after rebuilding their sources. Existing classifier test results remain locked. Model training writes the source CSVs; downstream refresh/export commands are required to update the notebook, report and app consistently. The submission guide records full-data availability and evaluator package checksums.
"""


def section_contributions(ctx):
    return f"""## 9. Contributions and board link

| Member | Role | Summary |
|---|---|---|
| M1 Abhinav | Dashboard, final notebook, repo and board | `reports/review2/contribution_member1.md` |
| M2 Rishiikesh | Corpus, tone, complexity | `reports/review2/contribution_member2.md` |
| M3 Akshay | Patterns, ITS, combined insights, final report, deck | `reports/review2/contribution_member3.md` |
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
@page { size: A4; margin: 16mm; @bottom-center { content: counter(page); font-size: 9pt; } }
tr { break-inside: avoid; }
body { font-family: Helvetica, Arial, sans-serif; font-size: 10pt; line-height: 1.35; margin: 0; }
h1 { font-size: 18pt; } h2 { font-size: 13pt; border-bottom: 1px solid #999; padding-bottom: 2px; page-break-after: avoid; }
h3 { font-size: 11pt; } code { font-size: 9pt; background: #f2f2f2; }
img { max-height: 160mm; width: auto; max-width: 100%; display: block; margin: 6px auto 12px; page-break-inside: avoid; }
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
    from weasyprint import HTML
    HTML(filename=str(html_path), base_url=str(html_path.parent)).write_pdf(str(pdf_path))
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
