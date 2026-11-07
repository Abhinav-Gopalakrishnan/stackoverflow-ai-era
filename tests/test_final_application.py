import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from src.predict import load_bundle, question_frame, infer, explain
from src.build_features import build_features
from src.run_models import split_by_date
from dashboard.scenarios import routing_scenario

ROOT=Path(__file__).resolve().parents[1]

def question():
    return question_frame('How can I merge two pandas DataFrames?',
        'I need to join two tables using their shared identifier while retaining unmatched rows.',
        "result = left.merge(right, on='id', how='left')",['python','pandas'],'2026-08-15T12:00:00Z',None)

def test_prediction_uses_saved_pipeline_and_fold_imputation():
    bundle,meta=load_bundle();q=question();weekly=pd.read_csv(ROOT/'data/processed/weekly_counts.csv')
    f,raw,p=infer(bundle,meta,q,weekly)
    assert pd.isna(f.account_age_days.iloc[0])
    direct=bundle['pipeline'].predict_proba(f[meta['input_columns']])[:,1]
    np.testing.assert_allclose(raw,direct)
    np.testing.assert_allclose(p,bundle['calibrator'].predict_proba(direct.reshape(-1,1))[:,1])
    assert 0<p[0]<1 and np.isfinite(explain(bundle,meta,f).contribution).all()
    assert not any(c.startswith('target_') for c in f)

def test_no_outcome_input_and_unsupported_dates_rejected():
    bundle,meta=load_bundle();q=question();q['created_at']=pd.Timestamp('2026-11-07',tz='UTC')
    with pytest.raises(ValueError,match='historical'):
        infer(bundle,meta,q,pd.read_csv(ROOT/'data/processed/weekly_counts.csv'))
    with pytest.raises(ValueError):question_frame('short','body','',[],'2026-08-15')

def test_main_split_purges_seven_days():
    f=pd.DataFrame({'created_at':pd.to_datetime(['2024-12-24','2024-12-25','2025-01-01','2025-06-23','2025-06-24','2025-07-01'],utc=True)})
    train,val,test=split_by_date(f)
    assert len(train)==1 and len(val)==2 and len(test)==1

def test_scenario_accounts_for_equal_capacity_costs():
    s=routing_scenario(1000,.2,.7,.24,.2,6,600,500,100)
    assert s['questions_reviewed']==200 and s['additional_identified']==28
    assert s['review_cost']==12000
    assert s['assumed_net_vs_same_capacity_random']==pytest.approx(2700)
    zero=routing_scenario(1000,.2,.7,.24,0,6,600,500,100)
    assert zero['assumed_net_vs_same_capacity_random']==-100
    worse=routing_scenario(1000,.2,.7,.1,.2,6,600,500,100)
    assert worse['assumed_net_vs_same_capacity_random'] < -100
    with pytest.raises(ValueError):routing_scenario(1000,2,.7,.24,.2,6,600,500)
    with pytest.raises(ValueError):routing_scenario(float('nan'),.2,.7,.24,.2,6,600,500)

def test_forecast_units_and_backtest_controls(app_page):
    at=app_page('pages/3_Forecasts.py')
    assert not at.exception
    displayed=next(x.value for x in at.dataframe if 'smape' in x.value.columns)
    original=pd.read_csv(ROOT/'dashboard/data/backtest_metrics_matched.csv').query("tag=='ALL' and horizon==26").set_index('model')
    for r in displayed.itertuples(): assert r.smape==f'{original.loc[r.model,"smape"]:.1f}%'
    assert any(x.label=='First forecast week' for x in at.selectbox)

def test_its_interval_units(app_page):
    at=app_page('pages/2_Patterns_and_2022_Break.py')
    assert not at.exception
    metric=next(m for m in at.metric if m.label=='Immediate Level Shift (Beta 2)')
    assert '15.15%' in metric.proto.help and '63.21%' in metric.proto.help

def test_falling_keywords_strongest_declines(app_page):
    at=app_page('pages/5_Tone_and_Complexity.py')
    assert not at.exception
    chart=json.loads(at.get('plotly_chart')[-1].proto.spec)
    assert 'array' in chart['data'][0]['y']

def test_live_prediction_form_changes_result(app_page):
    at=app_page('pages/8_Predict_a_Question.py')
    next(b for b in at.button if b.label=='Predict').click().run(timeout=30)
    assert not at.exception and at.metric
    first=at.session_state['last_prediction']['probability']
    at.text_input[0].set_value('Why does the Docker container fail to start with an exception?')
    next(b for b in at.button if b.label=='Predict').click().run(timeout=30)
    assert not at.exception
    assert first!=at.session_state['last_prediction']['probability']

def test_empty_period_and_reset(app_page):
    at=app_page('app.py')
    assert not at.exception
    at.radio(key='period_radio').set_value('post').run(timeout=30)
    next(b for b in at.button if b.label=='Reset filters').click().run(timeout=30)
    assert not at.exception and at.radio(key='period_radio').value=='all'

def test_original_evidence_checksums():
    import hashlib
    manifest=json.loads((ROOT/'reports/final_validation/original_evidence_sha256.json').read_text())
    for relative,digest in manifest.items():
        assert hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()==digest,relative

def test_additional_exports_match_sources():
    import hashlib
    manifest=json.loads((ROOT/'reports/final_validation/export_manifest.json').read_text())
    for name,entry in manifest.items():
        exported=(ROOT/'dashboard/data'/name).read_bytes()
        assert exported==(ROOT/entry['source']).read_bytes()
        assert hashlib.sha256(exported).hexdigest()==entry['sha256']

def test_unreviewed_topic_packet_is_not_complete():
    from scripts.check_human_review import validate
    packet=ROOT/'reports/final_validation/topic_human_review.csv'
    result=validate(packet,packet)
    assert result['status']=='incomplete' and result['completed_rows']==0

def test_scenario_success_changes_benefit(app_page):
    at=app_page('pages/6_Recommendations.py')
    before=next(m.value for m in at.metric if m.label=='Assumed net benefit vs random')
    next(s for s in at.slider if s.label=='Assumed intervention success').set_value(0).run(timeout=30)
    after=next(m.value for m in at.metric if m.label=='Assumed net benefit vs random')
    assert not at.exception and before!=after and after=='₹-1,000'

def test_forecast_calibration_does_not_fit_evaluation_outcomes(tmp_path,monkeypatch):
    from src import final_assets
    source=pd.read_csv(ROOT/'reports/review2/ts/backtest_predictions.csv')
    real_read=pd.read_csv
    monkeypatch.setattr(final_assets,'OUT',tmp_path)
    def reader(path,*args,**kwargs):
        if Path(path).name=='backtest_predictions.csv': return source.copy()
        return real_read(path,*args,**kwargs)
    monkeypatch.setattr(pd,'read_csv',reader)
    final_assets.calibrate_intervals()
    original=real_read(tmp_path/'interval_calibration.csv')
    source.loc[source.origin.ge('2026-01-01'),'actual']=1000000000
    final_assets.calibrate_intervals()
    changed=real_read(tmp_path/'interval_calibration.csv')
    np.testing.assert_array_equal(original.inflation,changed.inflation)
    assert not original.adjusted_coverage.equals(changed.adjusted_coverage)
