"""Additional evaluation assets, with original Review 1/2 results preserved."""
from pathlib import Path
import json
import shutil
import hashlib
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/final_validation'
DATA=ROOT/'dashboard/data'

def calibrate_intervals():
    b=pd.read_csv(ROOT/'reports/review2/ts/backtest_predictions.csv')
    # Labels must have matured by the calibration cutoff; evaluation origins are later.
    development=b[b.target_week<'2026-01-01'].copy()
    evaluation=b[b.origin>='2026-01-01'].copy()
    rows=[];tag_rows=[]
    for (model,h),d in development.groupby(['model','horizon']):
        radius=np.maximum(np.log1p(d.upper95)-d.log_pred,1e-6)
        residual=abs(np.log1p(d.actual)-d.log_pred)/radius
        factor=max(1.,float(np.quantile(residual,.95,method='higher')))
        e=evaluation[(evaluation.model==model)&(evaluation.horizon==h)].copy()
        r=np.maximum(np.log1p(e.upper95)-e.log_pred,1e-6)
        e['adjusted_lower']=np.expm1(np.clip(e.log_pred-factor*r,0,50))
        e['adjusted_upper']=np.expm1(np.clip(e.log_pred+factor*r,0,50))
        e['raw_covered']=e.actual.between(e.lower95,e.upper95)
        e['adjusted_covered']=e.actual.between(e.adjusted_lower,e.adjusted_upper)
        rows.append(dict(model=model,horizon=h,calibration_n=len(d),evaluation_n=len(e),inflation=factor,
            original_coverage=float(e.raw_covered.mean()),adjusted_coverage=float(e.adjusted_covered.mean())))
        for tag,g in e.groupby('tag'):
            tag_rows.append(dict(tag=tag,model=model,horizon=h,n=len(g),original_coverage=g.raw_covered.mean(),adjusted_coverage=g.adjusted_covered.mean(),inflation=factor))
    pd.DataFrame(rows).to_csv(OUT/'interval_calibration.csv',index=False)
    pd.DataFrame(tag_rows).to_csv(OUT/'interval_coverage_by_tag.csv',index=False)
    (OUT/'interval_protocol.json').write_text(json.dumps(dict(
        calibration='Backtest outcomes with target_week before 2026-01-01; pool study tags within model/horizon',
        evaluation='Origins from 2026-01-01; no evaluation outcomes used to fit inflation',
        method='95th percentile of absolute log error divided by original log interval half-width; minimum factor 1',
        limitations='Retrospective diagnostic with overlapping horizons and non-exchangeable time-series errors. Does not guarantee future 95% coverage. No model selection repeated.'),indent=2))

def review_packet():
    examples=pd.read_csv(ROOT/'reports/review2/text/topic_examples.csv')
    labels=pd.read_csv(ROOT/'reports/review2/text/topic_labels.csv')
    sample=examples.groupby('topic',sort=False).head(5).merge(labels[['topic','final_name']],on='topic')
    for col in ['reviewer','human_confirmed','label_fits','mixed_topic','suggested_label','reason']:
        sample[col]=''
    packet=OUT/'topic_human_review.csv'
    if not packet.exists():sample.to_csv(packet,index=False)
    status={'status':'pending_human_review','completed_rows':0,'required_rows':len(sample),
            'instruction':'Read linked questions and enter your own judgements. AI annotations are not independent human review.'}
    if not (OUT/'human_review_status.json').exists():
        (OUT/'human_review_status.json').write_text(json.dumps(status,indent=2))

def tag_examples():
    scores_path=ROOT/'data/processed/question_topics_v2.parquet'
    meta_path=ROOT/'data/processed/question_metadata_for_topics.parquet'
    if not scores_path.exists() or not meta_path.exists():
        return  # The committed export supports a clone without private inputs.
    scores=pd.read_parquet(scores_path)
    meta=pd.read_parquet(meta_path,columns=['question_id','title','tags','link'])
    d=meta.merge(scores,on='question_id',validate='one_to_one')
    from src.build_features import DEFAULT_TAGS
    examples=[]
    for tag in ['ALL']+DEFAULT_TAGS:
        selected=d if tag=='ALL' else d[d.tags.map(lambda tags:tag in tags)]
        for topic,g in selected[selected.dominant_topic.ge(0)].groupby('dominant_topic'):
            top=g.nlargest(5,f'topic_weight_{topic}')
            for r in top.itertuples():
                examples.append(dict(tag=tag,topic=topic,question_id=r.question_id,title=r.title,link=r.link))
    pd.DataFrame(examples).to_csv(OUT/'topic_examples_by_tag.csv',index=False)

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    calibrate_intervals();review_packet();tag_examples()
    mapping={f'v2_{name}.csv':OUT/f'{name}.csv' for name in ['classifier_metrics','confusion','subgroups','calibration','capture','feature_gain']}
    mapping.update({f'{name}.csv':OUT/f'{name}.csv' for name in ['interval_calibration','interval_coverage_by_tag','topic_human_review','topic_examples_by_tag']})
    mapping.update({'backtest_predictions.csv':ROOT/'reports/review2/ts/backtest_predictions.csv',
                    'stationarity_decision.csv':ROOT/'reports/review2/ts/stationarity_decision.csv',
                    'residual_checks.csv':ROOT/'reports/review2/ts/residual_checks.csv'})
    sources={}
    for name,path in mapping.items():
        shutil.copy2(path,DATA/name)
        sources[name]={'source':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    (OUT/'export_manifest.json').write_text(json.dumps(sources,indent=2))
    oldfiles=list((ROOT/'reports/review1/m5').glob('*'))+list((ROOT/'reports/review2/text').glob('*'))
    manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in oldfiles if p.is_file()}
    baseline=OUT/'original_evidence_sha256.json'
    if not baseline.exists():baseline.write_text(json.dumps(manifest,indent=2))

if __name__=='__main__':run()
