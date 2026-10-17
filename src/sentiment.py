"""M2: prose tone, explicit technical neutralisation and honest human validation.
Run python -m src.sentiment; later python -m src.sentiment --validate PATH_TO_LABEL_SHEET.
"""
from __future__ import annotations
import argparse,html,re
import numpy as np
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sklearn.metrics import accuracy_score,f1_score,cohen_kappa_score,confusion_matrix
from src.review2_common import ROOT,TEXT,question_meta,study_groups,write_json
NEUTRAL_TECH=['kill','fatal','execute','master','abort','dead','failed','exception','error']
FRUSTRATION=r'\burgent\b|\basap\b|\bstuck\b|\bfrustrat\w*\b|\bfor (?:hours|days)\b|\bdesperate\b|\bnothing works\b|\bplease help\b'
POLITENESS=r'\bthanks\b|\bthank you\b|\bappreciat\w*\b'
LABEL_RULE="Label the human asker's emotional tone as negative (expressed frustration/anger/distress), positive (expressed satisfaction/optimism/gratitude), or neutral (factual technical question without clear emotion). Technical error words alone are neutral. Do not use answer outcomes or the model score. Read the title and original question prose, ignoring code. Label independently before comparing."

def analyzer():
    a=SentimentIntensityAnalyzer();a.lexicon.update({x:0. for x in NEUTRAL_TECH});return a

def tone_scores(texts):
    a=analyzer();scores=[]
    for i,s in enumerate(texts):
        scores.append(a.polarity_scores(s)['compound'])
        if (i+1)%50000==0:print(f'Tone {i+1:,}',flush=True)
    return np.array(scores)

def validate(sheet_path):
    # AI assistance is disclosed and never inserted into the human-label columns.
    if (TEXT/'tone_ai_annotations.csv').exists():
        from src.review2_validation import summarize_tone
        return summarize_tone(sheet_path)
    sheet=pd.read_csv(sheet_path);need=['label_m2','label_m3','agreed_tone'];allowed={'negative','neutral','positive'}
    if any(c not in sheet for c in need):raise ValueError('Missing human-label columns')
    valid=sheet[need].apply(lambda c:c.isin(allowed)).all(axis=1)
    if len(sheet)!=200 or not valid.all():
        result={'status':'awaiting_independent_human_labels','labelled_rows':int(valid.sum()),'required_rows':200,
                'accuracy':None,'macro_f1':None,'cohen_kappa':None}
        write_json(TEXT/'tone_validation_status.json',result)
        pd.DataFrame([result]).to_csv(TEXT/'tone_validation.csv',index=False)
        return result
    if sheet.question_id.duplicated().any():raise ValueError('Duplicate question IDs in label sheet')
    p=pd.read_parquet(ROOT/'data/processed/question_tone_v1.parquet',columns=['question_id','tone'])
    s=sheet.merge(p,on='question_id',validate='one_to_one')
    if len(s)!=200:raise ValueError('Missing scored sample IDs')
    result={'status':'complete','labelled_rows':200,'required_rows':200,
        'accuracy':float(accuracy_score(s.agreed_tone,s.tone)),
        'macro_f1':float(f1_score(s.agreed_tone,s.tone,average='macro',labels=list(sorted(allowed)),zero_division=0)),
        'cohen_kappa':float(cohen_kappa_score(s.label_m2,s.label_m3,labels=['negative','neutral','positive']))}
    pd.DataFrame([result]).to_csv(TEXT/'tone_validation.csv',index=False);write_json(TEXT/'tone_validation_status.json',result)
    pd.DataFrame(confusion_matrix(s.agreed_tone,s.tone,labels=['negative','neutral','positive']),index=['negative','neutral','positive'],columns=['negative','neutral','positive']).rename_axis('actual').to_csv(TEXT/'tone_confusion.csv')
    return result

def run():
    TEXT.mkdir(parents=True,exist_ok=True)
    q=pd.read_parquet(ROOT/'data/processed/questions_clean_v1.parquet',columns=['question_id','created_at','tags','sampling_weight','target_resolved_7d','title','plain_body'])
    prose=q.title.fillna('').map(html.unescape)+' '+q.plain_body.fillna('')
    d=question_meta(q)
    saved=ROOT/'data/processed/question_tone_v1.parquet'
    if saved.exists():
        previous=pd.read_parquet(saved)
        if not previous.question_id.equals(d.question_id):raise ValueError('Saved tone scores do not match input question IDs')
        d['compound']=previous.compound
    else:d['compound']=tone_scores(prose)
    d['tone']=np.select([d.compound>=.05,d.compound<=-.05],['positive','negative'],default='neutral')
    d['frustration_flag']=prose.str.contains(FRUSTRATION,flags=re.I,regex=True).astype(int)
    d['politeness_flag']=prose.str.contains(POLITENESS,flags=re.I,regex=True).astype(int)
    d.to_parquet(ROOT/'data/processed/question_tone_v1.parquet',index=False)
    g=study_groups(d);rows=[]
    for (tag,month),s in g.groupby(['tag','month']):
        weights=s.sampling_weight
        r={'tag':tag,'month':month,'period':s.period.iloc[0],'n_sampled':len(s),'low_sample':len(s)<30}
        for tone in ['negative','neutral','positive']:r[tone+'_share']=float(np.average(s.tone.eq(tone),weights=weights))
        for f in ['frustration_flag','politeness_flag']:r[f+'_share']=float(np.average(s[f],weights=weights))
        rows.append(r)
    pd.DataFrame(rows).to_csv(TEXT/'tone_monthly.csv',index=False)
    sheet=TEXT/'tone_validation_sample.csv'
    if not sheet.exists():
        sample=pd.concat([d[d.period.eq(p)].sample(n=100,random_state=42) for p in ['pre','post']]).sample(frac=1,random_state=42)
        sample=sample[['question_id','period']].merge(q[['question_id','title']],on='question_id',validate='one_to_one')
        sample['title']=sample.title.map(html.unescape);sample['link']='https://stackoverflow.com/q/'+sample.question_id.astype(str)
        for c in ['label_m2','label_m3','agreed_tone']:sample[c]=''
        sample.to_csv(sheet,index=False)
    write_json(TEXT/'tone_method.json',{'technical_word_overrides':NEUTRAL_TECH,'frustration_regex':FRUSTRATION,'politeness_regex':POLITENESS,
        'thresholds':{'positive':'>=0.05','negative':'<=-0.05','neutral':'otherwise'},'label_rule':LABEL_RULE,'code_excluded':True,
        'warning':'VADER is exploratory until independently human validated; no human labels are generated by code'})
    validate(sheet)
    # Weighted association with tag and year controls, not a causal model.
    import statsmodels.api as sm
    X=pd.DataFrame({'negative':d.tone.eq('negative').astype(float),'positive':d.tone.eq('positive').astype(float),'frustration':d.frustration_flag.astype(float)})
    for tag in sorted(set(g.tag)-{'ALL'}):X['tag_'+tag]=q.tags.map(lambda ts:float(tag in ts))
    years=pd.get_dummies(d.created_at.dt.year,prefix='year',drop_first=True,dtype=float)
    X=sm.add_constant(pd.concat([X,years],axis=1))
    fit=sm.GLM(d.target_resolved_7d,X,family=sm.families.Binomial(),var_weights=d.sampling_weight).fit(cov_type='HC0')
    ci=fit.conf_int();pd.DataFrame({'term':X.columns,'coefficient':fit.params.to_numpy(),'odds_ratio':np.exp(fit.params.to_numpy()),'lower95':np.exp(ci[0].to_numpy()),'upper95':np.exp(ci[1].to_numpy()),'p_value':fit.pvalues.to_numpy()}).to_csv(TEXT/'tone_resolution_association.csv',index=False)
    print('Tone outputs and independent-label sheet saved',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--validate');a=p.parse_args()
    if a.validate:print(validate(a.validate))
    else:run()
