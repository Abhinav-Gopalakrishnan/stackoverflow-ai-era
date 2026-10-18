"""Record current handoff checks without overwriting original human labels.

Run the read-only artifact checks by default. Use --run-tests explicitly for pytest.
"""
import argparse
import json
import re
import subprocess
import sys
from datetime import datetime,timezone
import pandas as pd
from src.review2_common import ROOT,TS,TEXT,write_json


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run-tests',action='store_true');args=parser.parse_args()
    result=subprocess.run([sys.executable,str(ROOT/'scripts/check_review2_submission.py')],cwd=ROOT,text=True,capture_output=True,check=True)
    evidence=json.loads(result.stdout)
    series=pd.read_csv(TS/'series_long.csv')
    assert len(series)==5600 and series.groupby('tag').size().eq(400).all()
    forecasts=pd.read_csv(TS/'forecasts_26w.csv');selected=forecasts[forecasts.selected]
    assert len(selected)==364 and selected.groupby('tag').size().eq(26).all()
    assert selected.week_start.min()=='2026-09-01' and selected.week_start.max()=='2027-02-23'
    bp=pd.read_csv(TS/'backtest_predictions.csv')
    assert (pd.to_datetime(bp.training_last_week)<pd.to_datetime(bp.origin)).all()
    if args.run_tests:
        result=subprocess.run([sys.executable,'-m','pytest','tests','-q','--disable-warnings','--tb=short'],cwd=ROOT,text=True,capture_output=True)
        (ROOT/'reports/review2/test_results.txt').write_text(result.stdout+result.stderr)
        result.check_returncode()
    tests=ROOT/'reports/review2/test_results.txt'
    summary=re.findall(r'\d+ passed[^\n]*',tests.read_text())[-1] if tests.exists() else 'Not supplied'
    status={'checked_utc':datetime.now(timezone.utc).isoformat(),'local_implementation':'complete under disclosed protocol deviations',
        'checks':evidence['checks']+['14 x 400 weekly bins; 364 selected forecasts; all backtest cutoffs precede origin'],
        'test_evidence':summary,'test_mode':'Saved full-suite evidence; rerun only with --run-tests',
        'human_validation':json.loads((TEXT/'tone_validation_status.json').read_text())['status'],
        'protocol_deviations':['Original two-human tone adjudication/topic naming not completed; issue126 open','Document-cooccurrence NPMI replaces sliding-window c_npmi'],
        'pending':['New final team presentation, rehearsal and live delivery'],
        'not_claimed':['Independent second-human labels/approval','Optional GRU and classifier what-if extension','Public hosting','Kaggle publication','Recorded video']}
    write_json(ROOT/'reports/review2/completion_checks.json',status)
    print(json.dumps(status,indent=2))

if __name__=='__main__':main()
