"""Reproducible Review 2 topic comparison and weighted corpus exports.

Every score is measured. NMF and LDA use the same stratified training IDs,
vocabulary, disjoint coherence reference and three seeds. Checkpoints are private.
Run ``python -m src.topics``; ``--grid-only`` or ``--transform-only`` can resume.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import scipy.sparse as sp
import sklearn
from sklearn.decomposition import NMF, LatentDirichletAllocation
from sklearn.exceptions import ConvergenceWarning
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer

from src.review2_common import ROOT, TEXT, period, weighted_median, write_json

CACHE_DIR = ROOT / 'data/processed/.review2_cache/topic_corrections'
SEEDS = (42, 43, 44)
K_LIST = (10, 15, 20, 25, 30, 40)
NMF_ITERATIONS = 400
LDA_ITERATIONS = 10
METHOD_VERSION = 'measured-grid-v1'


def get_stratified_sample(df, n_per_half=5000, seed=42):
    """Up to 5,000 per half-year, with 20,000 disjoint reference documents."""
    if not df.question_id.is_unique:
        raise ValueError('Corpus question IDs must be unique')
    d = df.loc[df.n_tokens.gt(0)].copy()
    dates = pd.to_datetime(d.created_at, utc=True)
    d['half'] = dates.dt.year.astype(str) + 'H' + ((dates.dt.month - 1) // 6 + 1).astype(str)
    train = pd.concat([g.sample(n=min(n_per_half, len(g)), random_state=seed)
                       for _, g in d.groupby('half', sort=True)])
    remainder = d.drop(index=train.index)
    reference = remainder.sample(n=min(20000, len(remainder)), random_state=seed)
    if set(train.question_id) & set(reference.question_id):
        raise ValueError('Training and reference IDs overlap')
    return train, reference


def compute_npmi_coherence(top_word_indices, X_heldout_binary):
    """Mean top-word document-cooccurrence NPMI, then mean over topics.

    This is exact document-level NPMI, not gensim's sliding-window c_npmi.
    All candidates use the same 20,000 reference documents. Unseen pairs = -1.
    """
    union = sorted({i for words in top_word_indices for i in words})
    if not union or not X_heldout_binary.shape[0]:
        return 0.0
    x = (X_heldout_binary[:, union] > 0).astype(np.int64).tocsr()
    n = x.shape[0]
    probabilities = np.asarray(x.sum(axis=0)).ravel() / n
    joint = (x.T @ x).toarray() / n
    index = {word: i for i, word in enumerate(union)}
    scores = []
    for words in top_word_indices:
        pairs = []
        for a, word_a in enumerate(words):
            for word_b in words[a + 1:]:
                i, j = index[word_a], index[word_b]
                p = joint[i, j]
                if p <= 0 or probabilities[i] <= 0 or probabilities[j] <= 0:
                    pairs.append(-1.0)
                elif p >= 1:
                    pairs.append(1.0)
                else:
                    pairs.append(float(np.clip(np.log(p / (probabilities[i] * probabilities[j])) /
                                               -np.log(p), -1, 1)))
        if pairs:
            scores.append(float(np.mean(pairs)))
    return float(np.mean(scores)) if scores else 0.0


def compute_diversity(top_word_indices, top_n=25):
    words = [w for topic in top_word_indices for w in topic[:top_n]]
    return len(set(words)) / len(words) if words else 0.0


def compute_stability(models_top10):
    """Mean best-match Jaccard across all pairs of the supplied seeds."""
    if len(models_top10) < 2:
        return 1.0
    scores = []
    for i, first in enumerate(models_top10):
        for second in models_top10[i + 1:]:
            scores.append(np.mean([max(len(a & b) / len(a | b) if a | b else 0
                                       for b in second) for a in first]))
    return float(np.mean(scores))


def _fingerprint(train_texts, heldout_texts):
    h = hashlib.sha256()
    for texts in (train_texts, heldout_texts):
        h.update(pd.util.hash_pandas_object(texts, index=True).to_numpy().tobytes())
    config = dict(version=METHOD_VERSION, seeds=SEEDS, k=K_LIST, nmf_iter=NMF_ITERATIONS,
                  lda_iter=LDA_ITERATIONS, sklearn=sklearn.__version__, vocabulary='1-2grams,min20,max0.4,30000')
    h.update(json.dumps(config, sort_keys=True).encode())
    return h.hexdigest()


def _estimator(family, k, seed):
    if family == 'NMF':
        return NMF(n_components=k, init='nndsvda', random_state=seed,
                   max_iter=NMF_ITERATIONS, tol=1e-4)
    return LatentDirichletAllocation(n_components=k, random_state=seed,
                                    max_iter=LDA_ITERATIONS, learning_method='online',
                                    batch_size=2048, n_jobs=1, evaluate_every=-1)


def run_model_grid(train_texts, heldout_texts, k_list=K_LIST):
    TEXT.mkdir(parents=True, exist_ok=True)
    fingerprint = _fingerprint(train_texts, heldout_texts)
    cache = CACHE_DIR / fingerprint
    cache.mkdir(parents=True, exist_ok=True)
    tfidf = TfidfVectorizer(ngram_range=(1, 2), min_df=20, max_df=.4,
                           max_features=30000, dtype=np.float32)
    print(f'Fitting shared vocabulary on {len(train_texts):,} training documents', flush=True)
    train_tfidf = tfidf.fit_transform(train_texts)
    counts = CountVectorizer(vocabulary=tfidf.vocabulary_)
    train_counts = counts.transform(train_texts)
    reference_binary = (counts.transform(heldout_texts) > 0).astype(np.int64).tocsr()
    joblib.dump({'tfidf': tfidf, 'counts': counts}, cache / 'vectorizers.joblib')
    records, seed_records = [], []
    write_json(TEXT / 'topic_grid_manifest.json', {
        'status': 'running', 'fingerprint': fingerprint, 'method_version': METHOD_VERSION,
        'training_rows': len(train_texts), 'reference_rows': len(heldout_texts),
        'vocabulary_size': len(tfidf.vocabulary_), 'seeds': list(SEEDS), 'k_values': list(k_list),
        'same_training_sample_for_both_models': True,
        'coherence': 'Exact document-cooccurrence NPMI on top 10 terms; not sliding-window NPMI',
        'selection_rule': 'Highest mean coherence with mean diversity >= 0.7 and stability >= 0.6; otherwise best coherence',
        'iteration_budgets': {'NMF': NMF_ITERATIONS, 'LDA': LDA_ITERATIONS},
        'python': platform.python_version(), 'sklearn': sklearn.__version__,
        'started_utc': datetime.now(timezone.utc).isoformat()})
    for family in ('NMF', 'LDA'):
        matrix = train_tfidf if family == 'NMF' else train_counts
        for k in k_list:
            runs, top_words = [], []
            for seed in SEEDS:
                name = f'{family}_{k}_{seed}'
                result_file, model_file = cache / f'{name}.json', cache / f'{name}.joblib'
                if result_file.exists() and model_file.exists():
                    result = json.loads(result_file.read_text())
                    print(f'Resuming measured {name}', flush=True)
                else:
                    print(f'Fitting {name} on {len(train_texts):,} documents...', flush=True)
                    started = time.perf_counter()
                    model = _estimator(family, k, seed)
                    with warnings.catch_warnings(record=True) as caught:
                        warnings.simplefilter('always', ConvergenceWarning)
                        model.fit(matrix)
                    top25 = [np.argsort(c)[::-1][:25].tolist() for c in model.components_]
                    result = dict(model_family=family, k=k, seed=seed,
                                  coherence_npmi=compute_npmi_coherence([w[:10] for w in top25], reference_binary),
                                  diversity=compute_diversity(top25),
                                  reconstruction_error=float(model.reconstruction_err_) if family == 'NMF' else None,
                                  fit_seconds=time.perf_counter() - started, n_iter=int(model.n_iter_),
                                  fit_warnings=[str(w.message) for w in caught], top25=top25)
                    joblib.dump(model, model_file)
                    write_json(result_file, result)
                runs.append(result)
                top_words.append([set(w[:10]) for w in result['top25']])
                seed_records.append({key: value for key, value in result.items() if key != 'top25'})
                print(f"{name}: NPMI {result['coherence_npmi']:.4f}, diversity {result['diversity']:.4f}, "
                      f"{result['fit_seconds']:.1f}s, iterations {result['n_iter']}", flush=True)
                pd.DataFrame(seed_records).to_csv(TEXT / 'topic_model_seed_results.csv', index=False)
            stability = compute_stability(top_words)
            diversity = float(np.mean([r['diversity'] for r in runs]))
            records.append(dict(model_family=family, k=k,
                                coherence_npmi=float(np.mean([r['coherence_npmi'] for r in runs])),
                                coherence_sd=float(np.std([r['coherence_npmi'] for r in runs], ddof=1)),
                                diversity=diversity, stability=stability,
                                reconstruction_error=float(np.mean([r['reconstruction_error'] for r in runs])) if family == 'NMF' else np.nan,
                                satisfies_rule=bool(diversity >= .7 and stability >= .6),
                                fit_seconds=sum(r['fit_seconds'] for r in runs), seeds=len(SEEDS),
                                training_rows=len(train_texts), reference_rows=len(heldout_texts),
                                warning_runs=sum(bool(r['fit_warnings']) for r in runs)))
            pd.DataFrame(records).to_csv(TEXT / 'topic_model_selection_progress.csv', index=False)
    frame = pd.DataFrame(records)
    frame.to_csv(TEXT / 'topic_model_selection.csv', index=False)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    for family, group in frame.groupby('model_family'):
        for ax, field in zip(axes, ['coherence_npmi', 'diversity', 'stability']):
            ax.plot(group.k, group[field], marker='o', label=family)
            ax.set(xlabel='Number of topics', ylabel=field.replace('_', ' '))
            ax.legend(); ax.grid(alpha=.25)
    axes[1].axhline(.7, color='grey', linestyle=':')
    axes[2].axhline(.6, color='grey', linestyle=':')
    fig.suptitle(f'Measured topic comparison: {len(train_texts):,} training / {len(heldout_texts):,} reference documents')
    fig.tight_layout(); fig.savefig(TEXT / 'topic_model_selection.png', dpi=160); plt.close(fig)
    manifest = json.loads((TEXT / 'topic_grid_manifest.json').read_text())
    manifest.update(status='complete', fits=len(seed_records), completed_utc=datetime.now(timezone.utc).isoformat())
    write_json(TEXT / 'topic_grid_manifest.json', manifest)
    return frame


def select_best_model(selection_df):
    valid = selection_df[selection_df.satisfies_rule.astype(bool)]
    pool = valid if not valid.empty else selection_df
    winner = pool.sort_values(['coherence_npmi', 'model_family', 'k'], ascending=[False, True, True]).iloc[0]
    print(f'Selected {winner.model_family} k={winner.k}; threshold fallback={valid.empty}', flush=True)
    return str(winner.model_family), int(winner.k)


def _bootstrap_means(values, weights, n_boot=1000, seed=42):
    """Exact question bootstrap for all topic means together; retain survey weights."""
    if not len(weights):
        return np.full((n_boot, values.shape[1]), np.nan)
    rng = np.random.default_rng(seed)
    out = np.empty((n_boot, values.shape[1]))
    probabilities = np.full(len(weights), 1 / len(weights))
    for start in range(0, n_boot, 16):
        draws = rng.multinomial(len(weights), probabilities, size=min(16, n_boot-start))
        mass = draws * weights
        out[start:start+len(draws)] = mass @ values / mass.sum(axis=1)[:, None]
    return out


def _suggest_label(words):
    top = set(words[:10])
    if words[0] == 'numbertoken': return 'Mixed numerical tables and calculations', True
    if 'image description' in words or 'enter image' in words:
        return 'Mixed plotting, images and screenshot boilerplate', True
    rules = [({'error','python'}, 'Python errors and package execution'),
             ({'table','query'}, 'SQL queries and tables'),
             ({'array','object'}, 'Arrays and object manipulation'),
             ({'request','api'}, 'API requests and responses'),
             ({'class','method'}, 'Java classes and methods'),
             ({'react', 'component'}, 'React components and state'),
             ({'docker', 'container'}, 'Docker containers and images'),
             ({'android', 'gradle'}, 'Android development and builds'),
             ({'dataframe', 'panda', 'column'}, 'Dataframe rows and columns'),
             ({'power', 'dax'}, 'Power BI measures and tables'),
             ({'file', 'csv', 'folder'}, 'Files and data import/export'),
             ({'button', 'click', 'html'}, 'User-interface events and elements'),
             ({'array', 'list', 'string'}, 'Collections and programming operations'),
             ({'error', 'exception'}, 'Runtime and package error troubleshooting')]
    for terms, label in rules:
        if len(top & terms) >= min(2, len(terms)): return label, False
    return ' / '.join(words[:3]), False


def fit_and_export_final_model(df_corpus, df_meta, k=10, model_family='NMF'):
    manifest = json.loads((TEXT / 'topic_grid_manifest.json').read_text())
    if manifest['status'] != 'complete': raise RuntimeError('Complete the measured grid first')
    cache = CACHE_DIR / manifest['fingerprint']
    vectorizers = joblib.load(cache / 'vectorizers.joblib')
    model = joblib.load(cache / f'{model_family}_{k}_{SEEDS[0]}.joblib')
    vectorizer = vectorizers['tfidf' if model_family == 'NMF' else 'counts']
    names = vectorizer.get_feature_names_out()
    corpus = df_corpus.reset_index(drop=True).copy()
    if not corpus.question_id.is_unique or not df_meta.question_id.is_unique:
        raise ValueError('Expected unique corpus and metadata IDs')
    meta = corpus[['question_id']].merge(df_meta, on='question_id', validate='one_to_one')
    if len(meta) != len(corpus): raise ValueError('Missing metadata IDs')
    print(f'Transforming all {len(corpus):,} documents with {model_family} k={k}', flush=True)
    values = np.empty((len(corpus), k), dtype=np.float32)
    for start in range(0, len(corpus), 20000):
        matrix = vectorizer.transform(corpus.clean_text.iloc[start:start+20000])
        weights = model.transform(matrix)
        weights[matrix.getnnz(axis=1) == 0] = 0
        mass = weights.sum(axis=1, keepdims=True)
        values[start:start+len(weights)] = np.divide(weights, mass, out=np.zeros_like(weights), where=mass>0)
        print(f'Transformed {min(start+20000,len(corpus)):,}', flush=True)
    dominant = np.argmax(values, axis=1)
    dominant[values.sum(axis=1) == 0] = -1
    terms, examples, labels, suggestions = [], [], [], []
    for topic in range(k):
        indexes = np.argsort(model.components_[topic])[::-1][:15]
        words = names[indexes].tolist()
        for rank, index in enumerate(indexes, 1):
            terms.append(dict(topic=topic, rank=rank, term=names[index], weight=float(model.components_[topic,index])))
        selected = np.argsort(values[:,topic])[::-1]
        selected = selected[values[selected,topic] > 0][:10]
        for i in selected:
            examples.append(dict(topic=topic, question_id=int(corpus.question_id.iloc[i]), weight=float(values[i,topic]),
                                 title=str(meta.title.iloc[i]), link=str(meta.link.iloc[i])))
        name, mixed = _suggest_label(words)
        labels.append(dict(topic=topic, top_terms=', '.join(words), name_m4='', name_m2='', final_name=name,
                           agreement='mixed: automatic suggestion' if mixed else 'not independently human validated',
                           label_source='automatic top-term rules', mixed=mixed))
        suggestions.append(dict(topic=topic, suggested_name=name, top_terms=', '.join(words),
                                source='automatic top-term rules; not human labels', mixed=mixed))
    for filename, rows in [('topics_top_terms.csv',terms),('topic_examples.csv',examples),
                           ('topic_labels.csv',labels),('topic_label_suggestions.csv',suggestions)]:
        pd.DataFrame(rows).to_csv(TEXT/filename,index=False)
    scores = pd.DataFrame(values, columns=[f'topic_weight_{i}' for i in range(k)])
    scores.insert(0,'dominant_topic',dominant);scores.insert(0,'question_id',corpus.question_id.to_numpy())
    scores.to_parquet(ROOT/'data/processed/question_topics_v2.parquet',index=False)
    export_topic_aggregates(corpus, meta, values, dominant)
    write_json(TEXT/'topics_status.json',dict(status='complete', k=k, model_family=model_family,
        topics_count=k, corpus_rows=len(corpus), training_rows=manifest['training_rows'],
        reference_rows=manifest['reference_rows'], zero_projection_documents=int((dominant<0).sum()),
        fingerprint=manifest['fingerprint'], seeds=list(SEEDS), selected_export_seed=SEEDS[0],
        label_source='automatic term rules; no human naming agreement claimed',
        top_terms_file='topics_top_terms.csv',examples_file='topic_examples.csv',labels_file='topic_labels.csv',
        monthly_share_file='topic_monthly_share.csv',prepost_file='topic_prepost.csv',outcomes_file='topic_outcomes.csv',
        completed_utc=datetime.now(timezone.utc).isoformat()))


def export_topic_aggregates(corpus, meta, values, dominant):
    import yaml
    dates = pd.to_datetime(corpus.created_at, utc=True)
    months = dates.dt.strftime('%Y-%m').to_numpy()
    periods = period(dates)
    survey = corpus.sampling_weight.to_numpy(dtype=float)
    tags = yaml.safe_load((ROOT/'config.yaml').read_text())['study']['tags']
    monthly, prepost, outcomes, by_tag = [], [], [], []
    for group_no, tag in enumerate(['ALL', *tags]):
        mask = np.ones(len(corpus), dtype=bool) if tag=='ALL' else corpus.tags.map(lambda ts:tag in ts).to_numpy()
        indices = np.flatnonzero(mask)
        v, w = values[indices], survey[indices]
        print(f'Aggregating and bootstrapping {tag}: {len(indices):,} questions', flush=True)
        for month in sorted(set(months[indices])):
            local = np.flatnonzero(months[indices] == month)
            means = np.average(v[local], axis=0, weights=w[local])
            for topic, share in enumerate(means):
                monthly.append(dict(tag=tag,topic=topic,month=month,period=periods[indices[local[0]]],
                                    weighted_share=float(share),n_questions=len(local),low_sample=len(local)<30))
        halves = [periods[indices]==p for p in ['pre','post']]
        means = [np.average(v[h],axis=0,weights=w[h]) if h.any() else np.full(values.shape[1],np.nan) for h in halves]
        draws = [_bootstrap_means(v[h],w[h],seed=42+group_no*2+j) for j,h in enumerate(halves)]
        changes = draws[1]-draws[0]
        for topic in range(values.shape[1]):
            change = means[1][topic]-means[0][topic]
            prepost.append(dict(tag=tag,topic=topic,pre_share=means[0][topic],post_share=means[1][topic],change=change,
                                change_pct=100*change/means[0][topic] if means[0][topic]>0 else np.nan,
                                lower95=float(np.nanquantile(changes[:,topic],.025)),
                                upper95=float(np.nanquantile(changes[:,topic],.975)),bootstrap_resamples=1000,
                                n_pre=int(halves[0].sum()),n_post=int(halves[1].sum())))
            selected = indices[dominant[indices]==topic]
            m = meta.iloc[selected]
            rate = float(np.average(m.target_resolved_7d,weights=survey[selected])) if len(selected) else np.nan
            hours = weighted_median(m.hours_to_first_answer, survey[selected]) if len(selected) else np.nan
            outcomes.append(dict(tag=tag,topic=topic,n_questions=len(selected),resolved_rate_7d=rate,
                                 median_hours_to_first_answer=hours))
            by_tag.append(dict(tag=tag,topic=topic,weighted_share=float(np.average(v[:,topic],weights=w)),
                               n_questions=len(indices),dominant_questions=len(selected)))
    for filename,rows in [('topic_monthly_share',monthly),('topic_prepost',prepost),('topic_outcomes',outcomes)]:
        frame=pd.DataFrame(rows)
        frame.to_csv(TEXT/f'{filename}_by_tag.csv',index=False)
        frame[frame.tag.eq('ALL')].drop(columns='tag').to_csv(TEXT/f'{filename}.csv',index=False)
    pd.DataFrame(by_tag).to_csv(TEXT/'topic_by_tag.csv',index=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--grid-only',action='store_true')
    parser.add_argument('--transform-only',action='store_true')
    args=parser.parse_args()
    corpus=pd.read_parquet(ROOT/'data/processed/text_corpus_v1.parquet')
    meta=pd.read_parquet(ROOT/'data/processed/question_metadata_for_topics.parquet')
    train, reference=get_stratified_sample(corpus)
    split=pd.concat([train[['question_id','half']].assign(split='training'),
                     reference[['question_id','half']].assign(split='coherence_reference')])
    split.to_csv(TEXT/'topic_split_manifest.csv',index=False)
    if args.transform_only:
        manifest=json.loads((TEXT/'topic_grid_manifest.json').read_text())
        if manifest['fingerprint']!=_fingerprint(train.clean_text,reference.clean_text):
            raise ValueError('Measured grid does not match current input/configuration')
        grid=pd.read_csv(TEXT/'topic_model_selection.csv')
    else:
        grid=run_model_grid(train.clean_text,reference.clean_text)
    if not args.grid_only:
        family,k=select_best_model(grid)
        fit_and_export_final_model(corpus,meta,k,family)


if __name__=='__main__':
    main()
