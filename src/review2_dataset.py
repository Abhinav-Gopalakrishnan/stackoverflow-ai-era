"""Publish a small title-only preview, full schema and current dataset checks."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from src.review2_common import ROOT, weighted_median

OUT = ROOT/'reports/review2/dataset'
PATH = ROOT/'data/processed/questions_clean_v1.parquet'


def main():
    df=pd.read_parquet(PATH)
    OUT.mkdir(parents=True,exist_ok=True)
    checks={
        'unique_question_ids': bool(df.question_id.is_unique),
        'required_fields_complete': bool(df[['question_id','title','created_at','sampling_weight','target_resolved_7d']].notna().all().all()),
        'weights_finite_positive': bool((np.isfinite(df.sampling_weight)&df.sampling_weight.gt(0)).all()),
        'resolved_target_binary': bool(df.target_resolved_7d.isin([0,1]).all()),
        'answered_target_binary': bool(df.target_answered_7d.isin([0,1]).all()),
        'resolved_implies_answered': bool((df.target_resolved_7d<=df.target_answered_7d).all()),
        'date_range_in_study': bool(df.created_at.between('2019-01-01','2026-09-01',inclusive='left').all()),
        'account_age_nonnegative': bool(df.account_age_days.ge(0).all())}
    if not all(checks.values()): raise ValueError(checks)
    schema=pd.DataFrame([{'column':c,'dtype':str(df[c].dtype),'missing':int(df[c].isna().sum()),'description_source':'docs/data_dictionary.md'} for c in df])
    schema.to_csv(OUT/'dataset_schema.csv',index=False)
    # Deterministic sample spread across all observed years; no bodies or identifiers.
    cols=['question_id','title','created_at','sampling_weight','n_code_blocks','code_ratio','has_error_text','target_resolved_7d','target_answered_7d']
    sample=df.groupby(df.created_at.dt.year,group_keys=False).sample(n=5,random_state=42)[cols].sort_values('created_at').copy()
    sample['link']='https://stackoverflow.com/q/'+sample.question_id.astype(str)
    sample.to_csv(OUT/'final_dataset_sample.csv',index=False)
    # ALL rates use each collected question once; do not add overlapping tag tables.
    monthly=[]
    for month,g in df.groupby(df.created_at.dt.strftime('%Y-%m')):
        weights=g.sampling_weight
        resolved=float(np.average(g.target_resolved_7d,weights=weights))
        answered=float(np.average(g.target_answered_7d,weights=weights))
        monthly.append(dict(tag='ALL',month=month,n_sampled=len(g),est_questions=float(weights.sum()),
            resolved_rate_7d=resolved,answered_rate_7d=answered,
            accepted_given_answered=resolved/answered if answered else np.nan,
            median_hours_to_accept=weighted_median(g.hours_to_accept,weights),
            median_hours_to_first_answer=weighted_median(g.hours_to_first_answer,weights),low_sample=len(g)<30))
    original=pd.read_csv(ROOT/'reports/review2/ts/monthly_rates_masked.csv')
    pd.concat([original[original.tag.ne('ALL')],pd.DataFrame(monthly)],ignore_index=True).to_csv(OUT/'monthly_rates_with_all.csv',index=False)
    h=hashlib.sha256()
    with PATH.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    status={'file':str(PATH.relative_to(ROOT)),'rows':len(df),'columns':len(df.columns),
        'bytes':PATH.stat().st_size,'sha256':h.hexdigest(),'date_min':str(df.created_at.min()),'date_max':str(df.created_at.max()),
        'weight_min':float(df.sampling_weight.min()),'weight_max':float(df.sampling_weight.max()),
        'missing_account_age_flagged':int(df.missing_account_age.sum()),'body_truncated_flagged':int(df.body_truncated.sum()),
        'checks':checks,'all_passed':all(checks.values()),
        'availability':'Full parquet exists locally and is gitignored; supply it separately with the submission or use the original collection/cleaning pipeline. Git clone alone supports the precomputed dashboard and result notebooks.',
        'license':'Stack Overflow title examples: CC BY-SA 4.0 with canonical links; no body/user hash in public preview.'}
    pd.DataFrame([{k:v for k,v in status.items() if k != 'checks'}]).to_csv(OUT/'dataset_validation.csv',index=False)
    (OUT/'dataset_validation.json').write_text(json.dumps(status,indent=2)+'\n')
    print(json.dumps(status,indent=2))

if __name__=='__main__':main()
