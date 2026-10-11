"""M2: per-question complexity and weighted changes with question-bootstrap CIs."""
from __future__ import annotations
import re,html,argparse,json,hashlib
import numpy as np
import pandas as pd
import textstat
from src.review2_common import ROOT,TEXT,question_meta,study_groups,weighted_median,bootstrap_stat,write_json
CONTINUOUS=['prose_words','code_lines','n_code_blocks','tag_count','flesch_reading_ease']
FLAGS=['error_text_flag','why_how_flag','version_flag','multi_technology_flag']

def measurements(q):
    import yaml
    tags=set(yaml.safe_load((ROOT/'config.yaml').read_text())['study']['tags'])
    prose=q.plain_body.fillna('');title=q.title.fillna('').map(html.unescape)
    d=question_meta(q)
    d['prose_words']=prose.str.count(r"\b[\w]+(?:['’-][\w]+)*\b")
    d['code_lines']=q.code_text.fillna('').map(lambda s:sum(bool(line.strip()) for line in s.splitlines()))
    d['n_code_blocks']=q.n_code_blocks;d['tag_count']=q.tags.map(len)
    # textstat measures only the original prose, never lemmatised corpus or code.
    cache=ROOT/'data/processed/.review2_cache';cache.mkdir(exist_ok=True)
    checkpoint=cache/'flesch.npy'
    fingerprint=hashlib.sha256(pd.util.hash_pandas_object(q[['question_id','plain_body']],index=False).to_numpy().tobytes()).hexdigest()
    manifest=cache/'flesch_fingerprint.json'
    if manifest.exists() and json.loads(manifest.read_text())['fingerprint'] != fingerprint:
        raise ValueError('Readability checkpoint belongs to a different input dataset')
    write_json(manifest,{'fingerprint':fingerprint,'rows':len(q)})
    fre=np.load(checkpoint).tolist() if checkpoint.exists() else []
    print(f'Resuming readability at {len(fre):,}',flush=True)
    for i,s in enumerate(prose.iloc[len(fre):],start=len(fre)):
        fre.append(textstat.flesch_reading_ease(s) if d.prose_words.iloc[i]>0 else np.nan)
        if (i+1)%25000==0:
            np.save(checkpoint,np.array(fre));print(f'Readability {i+1:,}',flush=True)
    np.save(checkpoint,np.array(fre))
    d['flesch_reading_ease']=np.round(fre,2)
    d['error_text_flag']=(title+' '+prose).str.contains(r'\b(?:traceback|exception|error|errno|fatal)\b',case=False).astype(int)
    d['why_how_flag']=title.str.contains(r'^\s*(?:why|how)\b',case=False).astype(int)
    d['version_flag']=(title+' '+prose).str.contains(r'\b\d+\.\d+(?:\.\d+)?\b').astype(int)
    d['multi_technology_flag']=q.tags.map(lambda ts:int(len(set(ts)&tags)>=2))
    return d

def summarise(d,n_boot=1000):
    g=study_groups(d);monthly=[];changes=[]
    for (tag,month),s in g.groupby(['tag','month']):
        r={'tag':tag,'month':month,'period':s.period.iloc[0],'n_sampled':len(s),'low_sample':len(s)<30}
        for m in CONTINUOUS:r[m+'_median']=weighted_median(s[m],s.sampling_weight)
        for m in FLAGS:r[m+'_share']=float(np.average(s[m],weights=s.sampling_weight))
        monthly.append(r)
    pd.DataFrame(monthly).to_csv(TEXT/'complexity_monthly.csv',index=False)
    for tag,s in g.groupby('tag'):
        pre=s[s.period.eq('pre')];post=s[s.period.eq('post')]
        for m in CONTINUOUS+FLAGS:
            kind='median' if m in CONTINUOUS else 'mean'
            values=[];boots=[]
            for i,half in enumerate([pre,post]):
                val=weighted_median(half[m],half.sampling_weight) if kind=='median' else float(np.average(half[m],weights=half.sampling_weight))
                values.append(val);boots.append(bootstrap_stat(half[m],half.sampling_weight,kind,n_boot,42+i))
            diff=boots[1]-boots[0]
            changes.append({'tag':tag,'metric':m,'statistic':kind,'pre':values[0],'post':values[1],
                'change':values[1]-values[0],'lower95':float(np.quantile(diff,.025)),'upper95':float(np.quantile(diff,.975)),
                'n_pre':len(pre),'n_post':len(post),'bootstrap_resamples':n_boot})
        print(f'Complexity pre/post intervals: {tag}',flush=True)
    pd.DataFrame(changes).to_csv(TEXT/'complexity_prepost.csv',index=False)
    write_json(TEXT/'complexity_method.json',{'readability':'textstat Flesch reading ease on prose only; technical vocabulary limits interpretation',
        'bootstrap':'1000 question resamples with replacement; retain sampling_weight; compressed identical value/weight cells',
        'periods':'pre <= 2022-10, transition 2022-11/12 excluded from contrast, post >= 2023-01',
        'flags':'case-insensitive error; leading why/how; dotted numeric version; >=2 study tags',
        'empty_prose':'Flesch undefined (NaN), not zero','low_sample':'monthly flag for <30 sampled questions'})

def run():
    TEXT.mkdir(parents=True,exist_ok=True)
    path=ROOT/'data/processed/question_complexity_v1.parquet'
    if path.exists():d=pd.read_parquet(path)
    else:
        q=pd.read_parquet(ROOT/'data/processed/questions_clean_v1.parquet',columns=['question_id','created_at','tags','sampling_weight','target_resolved_7d','title','plain_body','code_text','n_code_blocks'])
        d=measurements(q);d.to_parquet(path,index=False)
    summarise(d)

if __name__=='__main__':run()
