"""Build submission notebooks that explain actual saved results without re-fitting."""
from pathlib import Path
import nbformat as nbf
from src.review2_common import ROOT

SETUP="""from pathlib import Path
import json, pandas as pd
from IPython.display import display, Image, Markdown
ROOT=next(p for p in [Path.cwd(), *Path.cwd().parents] if (p/'config.yaml').exists())
TS=ROOT/'reports/review2/ts'
TEXT=ROOT/'reports/review2/text'
def table(path):
    frame=pd.read_csv(ROOT/path)
    display(frame)
    return frame
def figure(path): display(Image(filename=str(ROOT/path)))
"""

def md(text):return nbf.v4.new_markdown_cell(text)
def code(text):return nbf.v4.new_code_cell(text)

def write(name,cells):
    nb=nbf.v4.new_notebook(cells=cells,metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python'}})
    nbf.write(nb,ROOT/'notebooks'/name)


def timeseries():
    return [
    md('## Unit 3 — Method 1: Time Series\nM3 Akshay: STL, stationarity, PELT and ITS. M5 Adhikkesh: forecast design, model selection, backtests and tag classes. Results are observational; event alignment does not establish causation.'),
    code("series=pd.read_csv(TS/'series_long.csv')\nassert len(series)==5600 and series.tag.nunique()==14\nassert series.groupby('tag').size().eq(400).all()\ndisplay(series.groupby('tag').size().rename('complete weeks'))\ndisplay(json.loads((TS/'series_manifest.json').read_text()))"),
    md('### Preparation: complete Tuesday-start weekly counts\nThe 14 weekly series are API total counts for ALL (site-wide) plus 13 study tags, collected separately from the question sample. ALL is not the sum of overlapping tags. Log1p counts support STL, stationarity and forecasting. The final observed complete week starts 2026-08-25; incomplete final weeks are excluded.'),
    code("display(pd.read_csv(TS/'stl_summary.csv'))\nfigure('reports/review2/ts/stl_small_multiples.png')\ns=pd.read_csv(TS/'stationarity_decision.csv')\ndisplay(s)\nprint('Level verdicts:',s.level_verdict.value_counts().to_dict())\nprint('First-difference verdicts:',s.diff_verdict.value_counts().to_dict())"),
    md('### PELT changes and the fixed-date ITS sensitivity check\nPELT uses a fixed penalty and minimum segment length. Its detected breaks are not hypothesis-test significance decisions. ITS models log counts with a launch-date level step, post-break slope and seasonal Fourier terms, using HAC errors. The transformed slope change is in percent per week. The single 2021 placebo cannot rule out all confounding.'),
    code("cp=pd.read_csv(TS/'changepoints.csv');its=pd.read_csv(TS/'its_results.csv')\nprint(f'{len(cp)} PELT breaks; {int(cp.within_4_weeks_of_event.sum())} within four weeks of an event.')\nprint(f'Actual slope magnitude exceeds placebo in {int(its.effect_exceeds_placebo.sum())}/{len(its)} series.')\ndisplay(its)\nfigure('reports/review2/ts/its_forest.png')"),
    md('### Forecast preparation and comparison protocol\nThree baselines: naive, seasonal naive and drift. Compare ETS and SARIMAX. Orders use training data before July 2024; family selection uses 2024 H2. Separate expanding-window backtests cover 2025–26 at 1, 4, 13 and 26 weeks. Each training cutoff precedes its forecast origin. MASE is an error ratio, not accuracy; lower is better.'),
    code("choices=pd.read_csv(TS/'model_choices.csv')\ndisplay(choices)\nprint('Selected model counts:',choices.selected_model.value_counts().to_dict())\ndisplay(pd.read_csv(TS/'validation_metrics.csv'))\nbp=pd.read_csv(TS/'backtest_predictions.csv')\nassert (pd.to_datetime(bp.training_last_week)<pd.to_datetime(bp.origin)).all()\nassert set(bp.horizon)=={1,4,13,26}\nsummary=pd.read_csv(TS/'backtest_summary_matched.csv');display(summary)\nfigure('reports/review2/ts/backtest_skill.png')"),
    md('### Evaluation: comparable origins, failures, coverage and diagnostics\nMatched-origin comparisons prevent a model appearing better by failing on hard cases. Empirical interval coverage is reported against nominal 80/95%; undercoverage is a limitation. Diebold–Mariano comparisons use the selected model versus naive; inspect actual rows and HAC details. They are exploratory with overlapping horizons.'),
    code("display(pd.read_csv(TS/'fit_failures.csv'))\ndisplay(pd.read_csv(TS/'diebold_mariano.csv'))\ndisplay(pd.read_csv(TS/'residual_checks.csv'))\nfigure('reports/review2/ts/acf_ALL.png')"),
    md('### Forecasts and fixed trajectory classes\nForecasts extend 26 weeks to 2027-02-23. Classes use the written thresholds and the validation-selected model. Zero last-week counts make percentage changes undefined. Forecasts are projections conditional on the saved history, not verified future outcomes.'),
    code("fc=pd.read_csv(TS/'forecasts_26w.csv');chosen=fc[fc.selected]\nassert chosen.groupby('tag').size().eq(26).all()\nassert chosen.week_start.max()=='2027-02-23'\ndisplay(pd.read_csv(TS/'tag_classes.csv'))\nfigure('reports/review2/ts/forecast_ALL.png')")]


def textmining():
    return [
    md('## Unit 3 — Method 2: Text Mining\nM2 Rishiikesh: corpus, tone and complexity. M4 Nishanth: original topic and keyword implementation. The corrections branch replaces the old topic comparison with measured runs; original contributions remain attributed in Git history.'),
    md('### Preparation: prose, sampling and disjoint topic reference\nRemove code from the topic prose; preserve technical vocabulary. VADER uses original prose rather than lowercase topic text. Topic training is stratified by half-year; held-out coherence documents are disjoint. NMF uses TF-IDF, LDA uses counts over the same vocabulary and training IDs. Shares and rates retain sampling weights.'),
    code("display(json.loads((TEXT/'corpus_stats.json').read_text()))\ngrid=json.loads((TEXT/'topic_grid_manifest.json').read_text());assert grid['status']=='complete'\ndisplay(grid)\nsplit=pd.read_csv(TEXT/'topic_split_manifest.csv')\nprint(split.groupby('split').size())\nassert split.question_id.is_unique\ndisplay(json.loads((TEXT/'tone_method.json').read_text()))"),
    md('### Evaluation: real NMF/LDA comparison, six k values and three seeds\nUse exact document-cooccurrence NPMI on the top 10 terms from the same held-out reference. This differs from sliding-window c_npmi and is explicitly documented. Diversity uses top 25 terms; stability uses cross-seed best-match Jaccard. Selection maximises mean coherence among diversity≥0.7 and stability≥0.6, with a documented best-coherence fallback. Do not interpret coherence as accuracy.'),
    code("selection=pd.read_csv(TEXT/'topic_model_selection.csv');display(selection)\ndisplay(pd.read_csv(TEXT/'topic_model_seed_results.csv'))\nfigure('reports/review2/text/topic_model_selection.png')\nstatus=json.loads((TEXT/'topics_status.json').read_text());display(status)\nprint(f\"Exported {status['model_family']} k={status['k']} using seed {status['selected_export_seed']}\")"),
    md('### Topic interpretation, weighted prevalence and outcomes\nFifteen terms and ten title-only source examples describe each topic. Topic names are automatic term rules, not independent human ratings. IDs are specific to this fitted model. Zero-vocabulary documents have zero topic weights and no dominant topic. Pre/post differences exclude transition; 1,000 question bootstrap resamples retain survey weights. CI units are absolute share differences (multiply by 100 for pp).'),
    code("display(pd.read_csv(TEXT/'topic_labels.csv'))\ndisplay(pd.read_csv(TEXT/'topics_top_terms.csv').head(30))\ndisplay(pd.read_csv(TEXT/'topic_examples.csv').head(20))\ndisplay(pd.read_csv(TEXT/'topic_prepost.csv'))\ndisplay(pd.read_csv(TEXT/'topic_outcomes.csv'))\ndisplay(pd.read_csv(TEXT/'topic_prepost_by_tag.csv').query(\"tag=='python'\"))"),
    md('### Keywords: Monroe log odds with Dirichlet prior\nCompare actual rising and falling terms with effect sizes and frequencies. Technical tokens and templated error language can influence the ranking. Differences describe observed vocabulary, not measured migration to an AI tool.'),
    code("kw=pd.read_csv(TEXT/'keywords_prepost.csv')\ndisplay(kw.query(\"tag_scope=='ALL'\").sort_values('z_score').head(10))\ndisplay(kw.query(\"tag_scope=='ALL'\").sort_values('z_score',ascending=False).head(10))\nfigure('reports/review2/text/keywords_shift_all.png')"),
    md('### Tone validation: one human reference plus disclosed AI annotations\nThe original two-human protocol was not completed. All 200 existing M3 human labels are used for VADER evaluation. AI labels are separate assistance, not human M2 labels or adjudicated gold. Report VADER accuracy/macro F1 and AI–human agreement/kappa separately. The frustration lexicon is an exploratory phrase proxy, not a reliable detector of a person’s emotion.'),
    code("display(json.loads((TEXT/'tone_validation_status.json').read_text()))\ndisplay(pd.read_csv(TEXT/'tone_validation.csv'))\ndisplay(pd.read_csv(TEXT/'tone_confusion.csv'))\ndisplay(pd.read_csv(TEXT/'tone_prepost.csv').query(\"tag=='ALL'\"))"),
    md('### Complexity and uncertainty\nCompare weighted prose words, code lines, reading ease and structural flags with 1,000-resample intervals. Reading ease is imperfect for technical prose. Models of resolution associations control for tags/year but do not identify causal effects.'),
    code("display(pd.read_csv(TEXT/'complexity_prepost.csv').query(\"tag=='ALL'\"))\ndisplay(pd.read_csv(TEXT/'tone_resolution_association.csv'))\nfigure('reports/review2/text/tone_complexity.png')")]


def main():
    intro=[md('# Complete Review 2 — Units 1, 2 and 3\nStack Overflow in the AI Era. This submission reads saved evidence; heavy training is reproduced through the documented source modules. Git clone includes lightweight results and the runnable application. Full cleaned data are supplied separately. No results are recomputed from or tuned against the locked test set.'),code(SETUP)]
    unit1=[md('## Unit 1 — Data Understanding, Preparation and Validation\nStack Exchange API 2.3 collection; 13 study tags from 2019 through August 2026. Sampling weights reflect the historic collection design. The primary target is acceptance within seven days; any answer within seven days is a separate secondary target. Code/body features are computed locally; public examples exclude bodies and user identifiers. See `docs/data_dictionary.md` and collection/cleaning notebooks for field definitions and rules.'),
    code("D=ROOT/'reports/review2/dataset'\nv=json.loads((D/'dataset_validation.json').read_text());assert v['all_passed']\ndisplay(v)\ndisplay(pd.read_csv(D/'dataset_schema.csv'))\ndisplay(pd.read_csv(D/'final_dataset_sample.csv'))"),
    md('### Data scope and processing limits\nQuestion IDs are unique, required fields complete, binary targets valid, weights finite/positive, and resolved implies answered. Missing account ages are imputed and flagged; long bodies are truncated and flagged. The preview is deterministic across observed years. The question-sample ALL group contains each collected question once. Weekly volume ALL is a separate site-wide API total, not an aggregation of the sampled questions. Detailed original cleaning is in `02_cleaning.ipynb`.'),
    code("import matplotlib.pyplot as plt\ns=table('reports/review2/ts/series_long.csv')\nall_series=s[s.tag.eq('ALL')]\nax=all_series.plot(x='week_start',y='count',figsize=(10,3),legend=False,title='Project ALL weekly count (complete weeks)');ax.set_ylabel('Questions');plt.show()")]
    unit2=[md('## Unit 2 — Predictive Modelling and Locked Evaluation\nPredict accepted answer within seven days. Chronological splits are train before 2025-01-01, validation 2025-01-01–2025-06-30 and locked test 2025-07-01–2026-07-31. August 2026 questions are outside the locked classifier evaluation but included in Unit 3. Training-only title TF-IDF/SVD and lagged history avoid future leakage. Compare majority, logistic regression, random forest and XGBoost. Select by validation PR-AUC, tune threshold for validation F1, then report the saved test result once. PR-AUC is appropriate for an imbalanced target; none of these scores is percentage accuracy.'),
    code("m=ROOT/'reports/review1/m5'\nr=json.loads((m/'results.json').read_text())\ndisplay(pd.DataFrame(r['split']).T)\ndisplay(r['chosen'])\ncomparison=pd.read_csv(m/'model_comparison_val.csv');display(comparison)\ncomparison.plot.bar(x='model',y=['pr_auc','roc_auc','f1'],figsize=(9,4),title='Validation comparison');plt.show()\ntest=pd.read_csv(m/'test_metrics.csv');display(test)\nassert int(test.iloc[0]['n'])==16695\ndisplay(pd.read_csv(m/'shap_top.csv'))"),
    md('### Interpretation and limitations\nPerformance is modest under temporal drift. The easier any-answer target must not be substituted for the primary accepted-answer target to claim >80%. SHAP describes fitted-model associations, not causal importance. Older Review 1 “100−MAPE accuracy” forecasting claims were test-tuned and are superseded by the Unit 3 training-only backtest.')]
    end=[md('## Combined Business Insights and Application\nThe recommendations connect one time-series finding and one text-mining finding, with an action, stakeholder, measurable KPI and limitation. They are proposals for evaluation, not demonstrated intervention effects.'),code("display(pd.read_csv(ROOT/'reports/review2/insight_matrix.csv'))\ndisplay(pd.read_csv(ROOT/'reports/review2/recommendations.csv'))"),md('## Reproduce, Demonstrate and Submit\n- Run the saved dashboard: `pip install -r dashboard/requirements.txt` then `streamlit run dashboard/app.py`.\n- Source modules, full-data access, package checksums and limitations: `docs/review2_submission_guide.md`.\n- Technical protocol change: `docs/review2_topic_evaluation.md`.\n- Rubric evidence and all five contributions: `reports/review2/readiness_checklist.md`.\n- The new presentation is a subsequent task. Public hosting and Kaggle publication are not claimed. The official Review 2 rubric accepts a locally runnable application.\n- AI assistance is disclosed; the two-human annotation requirement remains an explicit internal-plan deviation.')]
    write('review2_main.ipynb',intro+unit1+unit2+timeseries()+textmining()+end)
    write('07_timeseries.ipynb',[md('# Review 2 — Time Series'),code(SETUP)]+timeseries())
    write('08_text_mining.ipynb',[md('# Review 2 — Text Mining'),code(SETUP)]+textmining())
    print('Built complete submission notebook and two method notebooks.')

if __name__=='__main__':main()
