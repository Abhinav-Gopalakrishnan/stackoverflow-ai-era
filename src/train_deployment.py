"""Build v2 once using frozen XGBoost settings; never overwrite Review 1 evidence.

Training <2024-12-25; calibration Jan–Mar 2025; threshold April–June 23 2025.
August 2026 is the additional classifier evaluation, already explored by Unit 3;
it is retrospective, not a blind prospective trial. No July 2025–July 2026 scores
are recomputed. Re-running requires --replace and is recorded as a new build.
"""
import argparse
import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score, precision_score, recall_score, f1_score, brier_score_loss, confusion_matrix
from src import models
from src.build_features import build_features, DEFAULT_TAGS
from src.evaluate import tune_threshold
from src.predict import ROOT, MODEL_DIR, TARGET_DESCRIPTION

OUT = ROOT/'reports/final_validation'

def metrics(y, p, threshold):
    y=np.asarray(y); pred=p>=threshold
    return dict(n=len(y),positive_rate=float(y.mean()),pr_auc=float(average_precision_score(y,p)),
        roc_auc=float(roc_auc_score(y,p)) if len(np.unique(y))>1 else None,
        precision=float(precision_score(y,pred,zero_division=0)),recall=float(recall_score(y,pred,zero_division=0)),
        f1=float(f1_score(y,pred,zero_division=0)),brier=float(brier_score_loss(y,p)))

def run(replace=False):
    if (MODEL_DIR/'pipeline.joblib').exists() and not replace:
        raise RuntimeError('Release exists. Use --replace only for an intentional, documented rebuild.')
    MODEL_DIR.mkdir(parents=True,exist_ok=True); OUT.mkdir(parents=True,exist_ok=True)
    print('Loading cleaned questions and building shared features',flush=True)
    q=pd.read_parquet(ROOT/'data/processed/questions_clean_v1.parquet')
    weekly=pd.read_csv(ROOT/'data/processed/weekly_counts.csv')
    f=build_features(q,weekly); del q
    t=f.created_at; train=f[t<'2024-12-25']; cal=f[(t>='2025-01-01')&(t<'2025-04-01')]
    val=f[(t>='2025-04-08')&(t<'2025-06-24')]; test=f[(t>='2026-08-01')&(t<'2026-09-01')]
    numeric,binary,categorical=models.feature_lists(f)
    columns=numeric+binary+categorical+['title']; target='target_resolved_7d'
    from src.leakage import assert_no_leakage
    assert_no_leakage(columns)
    old=json.loads((ROOT/'reports/review1/m5/results.json').read_text())
    params=old['tuning']['xgb']['best_params'].copy(); params['n_estimators']=old['tuning']['xgb']['trees_after_early_stopping']
    pipe=models.build_pipeline('xgb',train[target],models.build_preprocessor(numeric,binary,categorical,text='title'),**params)
    print(f'Fitting frozen settings on {len(train):,} rows',flush=True)
    models.fit_pipeline(pipe,train[columns],train[target],train.sampling_weight)
    pc=pipe.predict_proba(cal[columns])[:,1]
    calibrator=LogisticRegression(C=1e6,random_state=42).fit(pc.reshape(-1,1),cal[target])
    pv=pipe.predict_proba(val[columns])[:,1]; cv=calibrator.predict_proba(pv.reshape(-1,1))[:,1]
    threshold=float(tune_threshold(val[target],cv))
    pt=pipe.predict_proba(test[columns])[:,1]; ct=calibrator.predict_proba(pt.reshape(-1,1))[:,1]
    evaluation=[]
    for split,d,raw,p in [('threshold_validation',val,pv,cv),('august_2026',test,pt,ct)]:
        for name,scores in [('raw',raw),('sigmoid_calibrated',p)]:
            evaluation.append(dict(split=split,variant=name,threshold=threshold if name!='raw' else old['chosen']['threshold'],
                **metrics(d[target],scores,threshold if name!='raw' else old['chosen']['threshold'])))
    pd.DataFrame(evaluation).to_csv(OUT/'classifier_metrics.csv',index=False)
    cm=confusion_matrix(test[target],ct>=threshold,labels=[0,1])
    pd.DataFrame(cm,index=['Actual proxy negative','Actual proxy positive'],columns=['Predicted negative','Predicted positive']).to_csv(OUT/'confusion.csv')
    scored=test[['question_id','created_at','tags','new_account','missing_account_age',target]].copy()
    scored['probability']=ct
    rows=[]
    for name,mask in [('all',np.ones(len(test),bool))]+[(f'{c}={v}',test[c].eq(v).to_numpy()) for c in ['new_account','missing_account_age'] for v in [0,1]]+[(tag,test['tag_'+tag].eq(1).to_numpy()) for tag in DEFAULT_TAGS]:
        if mask.sum():rows.append(dict(group=name,**metrics(test.loc[mask,target],ct[mask],threshold)))
    pd.DataFrame(rows).to_csv(OUT/'subgroups.csv',index=False)
    bins=pd.cut(ct,np.linspace(0,1,11),include_lowest=True)
    pd.DataFrame({'bin':bins,'predicted':ct,'observed':test[target].to_numpy()}).groupby('bin',observed=True).agg(
        n=('observed','size'),predicted=('predicted','mean'),observed=('observed','mean')).to_csv(OUT/'calibration.csv')
    captures=[]; negative=(test[target].to_numpy()==0)
    for fraction in [.05,.1,.2,.3,.5]:
        k=max(1,int(np.ceil(len(test)*fraction))); found=int(negative[np.argsort(ct,kind='stable')[:k]].sum())
        captures.append(dict(review_fraction=fraction,n_reviewed=k,n_unresolved_found=found,capture_rate=found/max(negative.sum(),1),
            precision_unresolved=found/k,random_expected=k*negative.mean()))
    pd.DataFrame(captures).to_csv(OUT/'capture.csv',index=False)
    names=pipe['prep'].get_feature_names_out(); gain=pipe['model'].feature_importances_
    pd.DataFrame({'feature':names,'gain':gain}).sort_values('gain',ascending=False).to_csv(OUT/'feature_gain.csv',index=False)
    path=MODEL_DIR/'pipeline.joblib';joblib.dump(dict(pipeline=pipe,calibrator=calibrator),path,compress=3)
    metadata=dict(version='resolution-v2',built_utc=pd.Timestamp.now(tz='UTC').isoformat(),target=TARGET_DESCRIPTION,
        threshold=threshold,input_columns=columns,study_tags=DEFAULT_TAGS,model_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        supported_start='2019-02-26T00:00:00+00:00',supported_end='2026-08-31T23:59:59+00:00',
        training_rows=len(train),calibration_rows=len(cal),threshold_rows=len(val),evaluation_rows=len(test),
        training_end_exclusive='2024-12-25',calibration_period='2025-01-01 to 2025-03-31',threshold_period='2025-04-08 to 2025-06-23',
        evaluation_period='August 2026; additional retrospective classifier evaluation, already explored in Unit 3',
        hyperparameters=params,python=platform.python_version(),packages={p:importlib.metadata.version(p) for p in ['numpy','pandas','scikit-learn','xgboost','joblib']},
        input_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ['data/processed/questions_clean_v1.parquet','data/processed/weekly_counts.csv']},
        limitations=['Retrospective question text may include later edits; original revisions were not reconstructed.',
        'Seven-day purge does not recover unavailable acceptance-event times.',
        'Calibration fitted Jan–Mar 2025 can drift in later periods; inspect August calibration.',
        'Historical demonstration only; current-date predictions require refreshed history and validation.'])
    (MODEL_DIR/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print(json.dumps(evaluation,indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--replace',action='store_true');run(p.parse_args().replace)
