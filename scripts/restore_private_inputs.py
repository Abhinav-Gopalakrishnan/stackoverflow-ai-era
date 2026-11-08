"""Regenerate private inputs without replacing published analytical summaries."""
import argparse
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pandas as pd
import numpy as np
from src import text_prep, sentiment, complexity, topics
from src.review2_common import question_meta

def run(task):
    out=ROOT/'reports/final_validation/restoration';out.mkdir(parents=True,exist_ok=True)
    if task=='corpus':
        text_prep.TEXT=out
        text_prep.run(processes=2)
        q=pd.read_parquet(ROOT/'data/processed/questions_clean_v1.parquet',columns=['question_id','title','tags','created_at','sampling_weight','target_resolved_7d','hours_to_first_answer'])
        q['link']='https://stackoverflow.com/q/'+q.question_id.astype(str)
        q.to_parquet(ROOT/'data/processed/question_metadata_for_topics.parquet',index=False)
    elif task=='tone':
        import html
        q=pd.read_parquet(ROOT/'data/processed/questions_clean_v1.parquet',columns=['question_id','created_at','tags','sampling_weight','target_resolved_7d','title','plain_body'])
        d=question_meta(q);prose=q.title.fillna('').map(html.unescape)+' '+q.plain_body.fillna('')
        d['compound']=sentiment.tone_scores(prose)
        d['tone']=np.select([d.compound>=.05,d.compound<=-.05],['positive','negative'],default='neutral')
        d.to_parquet(ROOT/'data/processed/question_tone_v1.parquet',index=False)
        # Compare against the preserved reference rather than rewriting labels.
        sheet=pd.read_csv(ROOT/'reports/review2/text/tone_validation_sample.csv')
        scored=sheet.merge(d[['question_id','tone']],on='question_id',validate='one_to_one')
        from sklearn.metrics import accuracy_score
        (out/'tone_restore.json').write_text(json.dumps({'rows':len(d),'accuracy_against_original_human':accuracy_score(scored.label_m3,scored.tone)},indent=2))
    elif task=='complexity':
        q=pd.read_parquet(ROOT/'data/processed/questions_clean_v1.parquet')
        d=complexity.measurements(q)
        d.to_parquet(ROOT/'data/processed/question_complexity_v1.parquet',index=False)
    elif task=='topics':
        import joblib
        from sklearn.feature_extraction.text import TfidfVectorizer
        corpus=pd.read_parquet(ROOT/'data/processed/text_corpus_v1.parquet')
        train,reference=topics.get_stratified_sample(corpus)
        manifest=json.loads((topics.TEXT/'topic_grid_manifest.json').read_text())
        fingerprint=topics._fingerprint(train.clean_text,reference.clean_text)
        if fingerprint!=manifest['fingerprint']:
            raise ValueError('Rebuilt corpus/config differs from published model; rerun the measured grid and all downstream outputs before replacing topic evidence.')
        vectorizer=TfidfVectorizer(ngram_range=(1,2),min_df=20,max_df=.4,max_features=30000,dtype=np.float32)
        x=vectorizer.fit_transform(train.clean_text)
        model=topics._estimator('NMF',15,42).fit(x)
        names=vectorizer.get_feature_names_out()
        old=pd.read_csv(topics.TEXT/'topics_top_terms.csv')
        for topic in range(15):
            actual=names[np.argsort(model.components_[topic])[::-1][:15]].tolist()
            expected=old[old.topic.eq(topic)].sort_values('rank').term.tolist()
            if actual!=expected:raise ValueError(f'Topic {topic} differs; do not reuse published topic IDs.')
        cache=topics.CACHE_DIR/fingerprint;cache.mkdir(parents=True,exist_ok=True)
        joblib.dump({'tfidf':vectorizer},cache/'vectorizers.joblib')
        joblib.dump(model,cache/'NMF_15_42.joblib')
        pieces=[]
        for start in range(0,len(corpus),20000):
            matrix=vectorizer.transform(corpus.clean_text.iloc[start:start+20000]);v=model.transform(matrix)
            v[matrix.getnnz(axis=1)==0]=0;mass=v.sum(axis=1,keepdims=True)
            pieces.append(np.divide(v,mass,out=np.zeros_like(v),where=mass>0))
        values=np.vstack(pieces);scores=pd.DataFrame(values,columns=[f'topic_weight_{i}' for i in range(15)])
        scores.insert(0,'dominant_topic',np.where(values.sum(axis=1)>0,values.argmax(axis=1),-1))
        scores.insert(0,'question_id',corpus.question_id.to_numpy())
        scores.to_parquet(ROOT/'data/processed/question_topics_v2.parquet',index=False)
        (out/'topics_restore.json').write_text(json.dumps({'rows':len(scores),'fingerprint':fingerprint,'all_top_terms_match':True,'scope':'Rebuilt selected seed-42 NMF only; original 36-fit comparison retained.'},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('task',choices=['corpus','tone','complexity','topics']);run(p.parse_args().task)
