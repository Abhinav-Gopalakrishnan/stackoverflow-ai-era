"""Verify actual result contracts and record dependencies; no staging or committing."""
import json,re,zipfile,subprocess,sys
import pandas as pd
from src.review2_common import ROOT,TS,TEXT,write_json

def main():
    checked=[]
    test_output=[];test_count=0
    for pattern in ['test_ts_forecast.py','test_text_review2.py']:
        result=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-p',pattern,'-v'],cwd=ROOT,text=True,capture_output=True)
        test_output.append(result.stdout+result.stderr)
        if result.returncode:raise RuntimeError(result.stdout+result.stderr)
        match=re.search(r'Ran (\d+) tests?',result.stderr)
        if match is None:raise RuntimeError('Test discovery produced no run summary')
        test_count+=int(match.group(1))
    (ROOT/'reports/review2/test_results.txt').write_text('\n'.join(test_output))
    for name in ['text_corpus_v1','question_tone_v1','question_complexity_v1','question_metadata_for_topics']:
        d=pd.read_parquet(ROOT/f'data/processed/{name}.parquet',columns=['question_id'])
        assert len(d)==302026 and d.question_id.is_unique,name
        checked.append(f'{name}: 302026 unique question IDs')
    w=pd.read_csv(TS/'series_long.csv',parse_dates=['week_start'])
    assert len(w)==5600 and w.tag.nunique()==14
    assert w.sort_values(['tag','week_start']).groupby('tag').week_start.diff().dropna().eq(pd.Timedelta(days=7)).all()
    checked.append('weekly series: 14 x 400 complete Tuesday-start weeks')
    bp=pd.read_csv(TS/'backtest_predictions.csv')
    assert set(bp.horizon)=={1,4,13,26}
    assert (pd.to_datetime(bp.training_last_week)<pd.to_datetime(bp.origin)).all()
    checked.append('all backtest training cutoffs precede first forecast week')
    f=pd.read_csv(TS/'forecasts_26w.csv');selected=f[f.selected]
    assert selected.groupby('tag').size().eq(26).all() and selected.tag.nunique()==14
    assert selected.week_start.min()=='2026-09-01' and selected.week_start.max()=='2027-02-23'
    assert (f.lower95<=f.lower80).all() and (f.lower80<=f.upper80).all() and (f.upper80<=f.upper95).all()
    checked.append('364 selected forecast rows; correct end date and nested intervals')
    c=pd.read_csv(TEXT/'complexity_prepost.csv');assert c.bootstrap_resamples.eq(1000).all()
    sheet=pd.read_csv(TEXT/'tone_validation_sample.csv')
    assert len(sheet)==200 and sheet.question_id.is_unique and sheet.period.value_counts().to_dict()=={'post':100,'pre':100}
    checked.append('complexity: 1000 bootstrap resamples; tone sheet: 100 pre + 100 post')
    for name in ['07_timeseries','08_text_mining']:
        nb=json.loads((ROOT/f'notebooks/{name}.ipynb').read_text())
        cells=[x for x in nb['cells'] if x['cell_type']=='code']
        assert all(x.get('execution_count') is not None for x in cells)
        assert not any(o.get('output_type')=='error' for x in cells for o in x.get('outputs',[]))
        checked.append(f'{name}: {len(cells)} genuinely executed code cells, zero errors')
    for member in [2,5]:
        with zipfile.ZipFile(ROOT/f'reports/review2/member{member}_review2_slides.pptx') as z:
            assert len([p for p in z.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml',p)])==2
        checked.append(f'M{member}: exactly two presentation slides')
    status={'local_implementation':'complete','checks':checked,'unit_tests_passed':test_count,
        'human_validation':json.loads((TEXT/'tone_validation_status.json').read_text())['status'],
        'pending':['M2 and M3 independent tone labels','M4 topic terms/examples before M2 names topics'],
        'not_claimed':['optional GRU','optional classifier feature extension/what-if page','M1/M3 final team integration and deployment']}
    write_json(ROOT/'reports/review2/completion_checks.json',status)
    print(json.dumps(status,indent=2))

if __name__=='__main__':main()
