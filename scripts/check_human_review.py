"""Validate an actual completed review packet; never supply human judgements."""
import argparse
import json
from pathlib import Path
import pandas as pd

def validate(path,packet):
    d=pd.read_csv(path).fillna('');expected=pd.read_csv(packet)
    keys=['topic','question_id']
    if d.duplicated(keys).any() or set(map(tuple,d[keys].to_numpy()))!=set(map(tuple,expected[keys].to_numpy())):
        raise ValueError('Review must contain exactly the packet question/topic pairs.')
    done=(d.reviewer.astype(str).str.strip().ne('')&d.reason.astype(str).str.strip().ne('')&
          d.human_confirmed.astype(str).str.lower().eq('yes')&d.label_fits.isin(['yes','no','uncertain'])&d.mixed_topic.isin(['yes','no','uncertain']))
    return {'status':'complete_self_attested_human_review' if done.all() else 'incomplete',
            'completed_rows':int(done.sum()),'required_rows':len(d),
            'reviewers':sorted(set(d.loc[done,'reviewer'])),
            'label_fit_counts':d.loc[done,'label_fits'].value_counts().to_dict(),
            'limitation':'Reviewer self-attestation; this script cannot independently verify authorship or independence.'}

if __name__=='__main__':
    root=Path(__file__).resolve().parents[1]
    p=argparse.ArgumentParser();p.add_argument('completed_csv',type=Path);p.add_argument('--output',type=Path)
    a=p.parse_args();result=validate(a.completed_csv,root/'reports/final_validation/topic_human_review.csv')
    print(json.dumps(result,indent=2))
    if a.output:a.output.write_text(json.dumps(result,indent=2)+'\n')
