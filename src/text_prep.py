"""M2: prose-only, technology-aware spaCy corpus for M4; python -m src.text_prep."""
from __future__ import annotations
import argparse, html, re, time
import json, hashlib
from collections import Counter
import numpy as np
import pandas as pd
from src.review2_common import ROOT,TEXT,question_meta,write_json

TECH={'c++':'cplusplus','c#':'csharp','.net':'dotnet','node.js':'nodejs','next.js':'nextjs','vue.js':'vuejs','asp.net':'aspnet'}
BOILERPLATE={'trying','try','want','using','use','help','thanks','thank','please','anyone','question','issue','problem','work','need'}
PLACEHOLDERS={'urltoken','pathtoken','numbertoken'}

def normalize(text):
    s=html.unescape(str(text or '')).lower()
    for token,replacement in sorted(TECH.items(),key=lambda x:-len(x[0])):
        s=re.sub(r'(?<!\w)'+re.escape(token)+r'(?!\w)',replacement,s)
    s=re.sub(r'https?://\S+|www\.\S+',' urltoken ',s)
    s=re.sub(r'(?<!\w)(?:[a-z]:\\|/|\./|\.\./)[\w./\\-]+',' pathtoken ',s)
    s=re.sub(r'\b\d{4,}\b',' numbertoken ',s)
    return re.sub(r'[^a-z0-9_\s]',' ',s)


def run(processes=2):
    import spacy
    from spacy.lang.en.stop_words import STOP_WORDS
    TEXT.mkdir(parents=True,exist_ok=True)
    q=pd.read_parquet(ROOT/'data/processed/questions_clean_v1.parquet',columns=['question_id','created_at','tags','sampling_weight','target_resolved_7d','title','plain_body'])
    d=question_meta(q);titles=q.title.fillna('').map(html.unescape)
    texts=(titles+' '+q.plain_body.fillna('')).map(normalize)
    stop=(set(STOP_WORDS)|BOILERPLATE)-{'error'}
    nlp=spacy.load('en_core_web_sm',disable=['parser','ner']);nlp.max_length=max(nlp.max_length,int(texts.str.len().max())+1)
    cache=ROOT/'data/processed/.review2_cache';cache.mkdir(exist_ok=True)
    checkpoint=cache/'corpus.jsonl';manifest=cache/'corpus_fingerprint.json'
    fingerprint=hashlib.sha256(pd.util.hash_pandas_object(q[['question_id','title','plain_body']],index=False).to_numpy().tobytes()).hexdigest()
    if manifest.exists() and json.loads(manifest.read_text())['fingerprint'] != fingerprint:
        raise ValueError('Corpus checkpoint belongs to a different dataset; choose a fresh cache directory')
    write_json(manifest,{'fingerprint':fingerprint,'rows':len(q)})
    cleaned=[json.loads(line) for line in checkpoint.read_text().splitlines()] if checkpoint.exists() else []
    if len(cleaned)>len(q):raise ValueError('Checkpoint longer than input')
    vocab=Counter(t for s in cleaned for t in s.split());started=time.time();start=len(cleaned)
    print(f'Resuming corpus at {start:,} questions',flush=True)
    pending=[]
    for i,doc in enumerate(nlp.pipe(texts.iloc[start:],batch_size=128,n_process=processes),start=start):
        tokens=[t.lemma_.lower() for t in doc if not t.is_space and not t.is_punct and
                t.lemma_.lower() not in stop and (t.is_alpha or t.text in PLACEHOLDERS)]
        s=' '.join(tokens);cleaned.append(s);pending.append(s);vocab.update(tokens)
        if (i+1)%10000==0:
            with checkpoint.open('a') as f:
                for line in pending:f.write(json.dumps(line)+'\n')
            pending=[]
            print(f'Corpus {i+1:,}/{len(q):,}; {time.time()-started:.0f}s',flush=True)
    with checkpoint.open('a') as f:
        for line in pending:f.write(json.dumps(line)+'\n')
    d['clean_text']=cleaned;d['n_tokens']=d.clean_text.str.split().str.len()
    out=ROOT/'data/processed/text_corpus_v1.parquet';d.drop(columns='month').to_parquet(out,index=False)
    # Explicitly include example titles/links in the sample without exposing prose.
    sample=d.sample(n=min(2000,len(d)),random_state=42).copy()
    sample['title']=titles.loc[sample.index];sample['link']='https://stackoverflow.com/q/'+sample.question_id.astype(str)
    sample.drop(columns=['clean_text','month']).to_parquet(TEXT/'corpus_sample_metadata.parquet',index=False)
    d.sample(n=min(2000,len(d)),random_state=42).drop(columns='month').to_parquet(ROOT/'data/processed/text_corpus_sample_2000.parquet',index=False)
    # Private metadata joins give M4 the outcomes and linked titles missing from corpus columns.
    write_json(TEXT/'corpus_stats.json',{'documents_before':len(q),'documents_after':len(d),'empty_after_cleaning':int(d.n_tokens.eq(0).sum()),
        'vocabulary_size':len(vocab),'total_tokens':int(d.n_tokens.sum()),'spacy_model':'en_core_web_sm',
        'parser_ner':'disabled','code_excluded':True,'sampling_weight':'retained, must be used in shares','seconds':round(time.time()-started,2)})
    write_json(TEXT/'text_preprocessing.json',{'technology_tokens':TECH,'stopwords':sorted(stop),
        'placeholders':sorted(PLACEHOLDERS),'empty_docs':'retained and flagged by n_tokens=0; M4 excludes from fitting, reports count',
        'sample':'text_corpus_sample_2000.parquet is a development input; it contains cleaned prose, not public examples',
        'public_examples':'corpus_sample_metadata.parquet: titles and links only'})
    print(f'Corpus saved: {out}',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--processes',type=int,default=2);a=p.parse_args();run(a.processes)
