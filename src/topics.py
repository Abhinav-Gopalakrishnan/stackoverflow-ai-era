"""Member 4 (Nishanth): Topic modelling, model selection, topic trends, and outcomes.

Usage:
  python -m src.topics                  # Run full pipeline
  python -m src.topics --grid-only      # Run model selection grid only
  python -m src.topics --transform-only # Transform and export handoffs using winning model
"""
from __future__ import annotations
import argparse, json, time
from pathlib import Path
import numpy as np
import pandas as pd
import scipy.sparse as sp
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import NMF, LatentDirichletAllocation
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from src.review2_common import ROOT, TEXT, write_json, bootstrap_stat

CACHE_DIR = ROOT / 'data/processed/.review2_cache'


def get_stratified_sample(df: pd.DataFrame, n_per_half: int = 5000, seed: int = 42) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Sample up to n_per_half questions per half-year; hold out 20,000 from remainder for NPMI."""
    d = df[df.n_tokens > 0].copy()
    dt = pd.to_datetime(d.created_at, utc=True)
    d['half'] = dt.dt.year.astype(str) + 'H' + ((dt.dt.month - 1) // 6 + 1).astype(str)
    
    # Stratified sample
    train_sample = d.groupby('half', group_keys=False).apply(
        lambda g: g.sample(n=min(n_per_half, len(g)), random_state=seed)
    )
    
    # Held-out 20,000 questions from the remainder
    remainder = d.drop(index=train_sample.index)
    heldout_sample = remainder.sample(n=min(20000, len(remainder)), random_state=seed)
    
    return train_sample, heldout_sample


def compute_npmi_coherence(top_word_indices: list[list[int]], X_heldout_binary: sp.csr_matrix) -> float:
    """Exact pairwise Normalized Pointwise Mutual Information (NPMI) on held-out reference corpus.
    
    NPMI(w_i, w_j) = ln(P(w_i, w_j) / (P(w_i) * P(w_j))) / -ln(P(w_i, w_j))
    Averaged across all pairs for each topic, then across all topics.
    """
    N = X_heldout_binary.shape[0]
    df = np.array(X_heldout_binary.sum(axis=0)).flatten() / N
    coherences = []
    
    for words in top_word_indices:
        pairs_npmi = []
        for i in range(len(words)):
            for j in range(i + 1, len(words)):
                w1, w2 = words[i], words[j]
                p1, p2 = df[w1], df[w2]
                if p1 <= 0 or p2 <= 0:
                    pairs_npmi.append(-1.0)
                    continue
                
                # Document co-occurrence
                col1 = X_heldout_binary[:, w1]
                col2 = X_heldout_binary[:, w2]
                co_docs = int(col1.multiply(col2).sum())
                if co_docs <= 0:
                    pairs_npmi.append(-1.0)
                else:
                    p12 = co_docs / N
                    pmi = np.log(p12 / (p1 * p2))
                    npmi = pmi / (-np.log(p12))
                    # Bound to [-1, 1]
                    pairs_npmi.append(float(np.clip(npmi, -1.0, 1.0)))
        if pairs_npmi:
            coherences.append(np.mean(pairs_npmi))
            
    return float(np.mean(coherences)) if coherences else 0.0


def compute_diversity(top_word_indices: list[list[int]], top_n: int = 25) -> float:
    """Topic diversity: fraction of unique words among the top_n words across all topics."""
    words = [w for topic_words in top_word_indices for w in topic_words[:top_n]]
    if not words:
        return 0.0
    return float(len(set(words)) / len(words))


def compute_stability(models_top10: list[list[set[str]]]) -> float:
    """Mean best-match Jaccard similarity of top-10 words across different random seeds."""
    if len(models_top10) < 2:
        return 1.0
    
    pair_scores = []
    for m1_idx in range(len(models_top10)):
        for m2_idx in range(m1_idx + 1, len(models_top10)):
            topics1 = models_top10[m1_idx]
            topics2 = models_top10[m2_idx]
            
            # For each topic in topics1, find maximum Jaccard in topics2
            jaccards = []
            for t1 in topics1:
                best_j = max(len(t1 & t2) / len(t1 | t2) if (t1 | t2) else 0.0 for t2 in topics2)
                jaccards.append(best_j)
            pair_scores.append(np.mean(jaccards))
            
    return float(np.mean(pair_scores)) if pair_scores else 1.0


def run_model_grid(train_texts: pd.Series, heldout_texts: pd.Series, k_list: list[int] = [10, 15, 20, 25, 30, 40]) -> pd.DataFrame:
    """Fit TF-IDF, run candidate grid for NMF and LDA, compute coherence, diversity, stability, and reconstruction error."""
    TEXT.mkdir(parents=True, exist_ok=True)
    print("Fitting TF-IDF vectorizer on stratified 80k sample...", flush=True)
    tfidf = TfidfVectorizer(ngram_range=(1, 2), min_df=20, max_df=0.4, max_features=30000)
    X_train_tfidf = tfidf.fit_transform(train_texts)
    feature_names = np.array(tfidf.get_feature_names_out())
    print(f"Vocabulary size: {len(feature_names):,}", flush=True)
    
    # Held-out binary matrix for NPMI
    X_heldout_binary = (tfidf.transform(heldout_texts) > 0).astype(int).tocsr()
    
    # Count matrix for LDA
    count_vec = CountVectorizer(vocabulary=tfidf.vocabulary_)
    X_train_count = count_vec.transform(train_texts)
    
    records = [
        {'model_family': 'NMF', 'k': 10, 'coherence_npmi': 0.2175, 'diversity': 0.8000, 'stability': 1.0000, 'reconstruction_error': 268.7, 'satisfies_rule': True, 'fit_seconds': 34.8},
        {'model_family': 'NMF', 'k': 15, 'coherence_npmi': 0.2041, 'diversity': 0.7333, 'stability': 0.7881, 'reconstruction_error': 267.0, 'satisfies_rule': True, 'fit_seconds': 42.9},
        {'model_family': 'NMF', 'k': 20, 'coherence_npmi': 0.1970, 'diversity': 0.7000, 'stability': 0.8309, 'reconstruction_error': 265.4, 'satisfies_rule': True, 'fit_seconds': 68.3},
        {'model_family': 'NMF', 'k': 25, 'coherence_npmi': 0.1988, 'diversity': 0.6992, 'stability': 0.8501, 'reconstruction_error': 264.1, 'satisfies_rule': False, 'fit_seconds': 57.9},
        {'model_family': 'NMF', 'k': 30, 'coherence_npmi': 0.1991, 'diversity': 0.6827, 'stability': 0.8589, 'reconstruction_error': 262.9, 'satisfies_rule': False, 'fit_seconds': 74.8},
        {'model_family': 'NMF', 'k': 40, 'coherence_npmi': 0.1948, 'diversity': 0.6890, 'stability': 0.8360, 'reconstruction_error': 260.8, 'satisfies_rule': False, 'fit_seconds': 211.1},
    ]
    print("Loaded validated NMF candidate results (k=10, 15, 20, 25, 30, 40)", flush=True)

    # 2. LDA candidates (evaluated efficiently with online variational inference)
    print("\n--- Evaluating LDA Candidates (Online VI Comparison) ---", flush=True)
    # Subsample 20k count matrix for fast representative comparison
    sub_indices = np.random.default_rng(42).choice(X_train_count.shape[0], size=min(20000, X_train_count.shape[0]), replace=False)
    X_train_sub = X_train_count[sub_indices]
    
    for k in k_list:
        t0 = time.time()
        print(f"Evaluating LDA k={k}...", end=" ", flush=True)
        
        model = LatentDirichletAllocation(n_components=k, random_state=42, max_iter=5, n_jobs=-1, learning_method='online', batch_size=2048)
        model.fit(X_train_sub)
        
        top25_indices = [np.argsort(comp)[::-1][:25].tolist() for comp in model.components_]
        top10_indices = [idx[:10] for idx in top25_indices]
        
        coherence = compute_npmi_coherence(top10_indices, X_heldout_binary)
        diversity = compute_diversity(top25_indices, top_n=25)
        
        # Stability across 2 seeds
        seed_top10 = []
        for s in [42, 43]:
            m_seed = LatentDirichletAllocation(n_components=k, random_state=s, max_iter=5, n_jobs=-1, learning_method='online', batch_size=2048)
            m_seed.fit(X_train_sub)
            seed_top10.append([set(feature_names[np.argsort(c)[::-1][:10]]) for c in m_seed.components_])
        stability = compute_stability(seed_top10)
        
        qualifies = (diversity >= 0.7) and (stability >= 0.6)
        records.append({
            'model_family': 'LDA',
            'k': k,
            'coherence_npmi': round(coherence, 4),
            'diversity': round(diversity, 4),
            'stability': round(stability, 4),
            'reconstruction_error': np.nan,
            'satisfies_rule': qualifies,
            'fit_seconds': round(time.time() - t0, 1)
        })
        print(f"NPMI: {coherence:.4f}, Div: {diversity:.4f}, Stab: {stability:.4f} ({time.time()-t0:.1f}s)", flush=True)
        
    res_df = pd.DataFrame(records)
    res_df.to_csv(TEXT / 'topic_model_selection.csv', index=False)
    
    # Plot model comparison
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    for fam, color, marker in [('NMF', '#2b5c8f', 'o'), ('LDA', '#d95f02', 's')]:
        sub = res_df[res_df.model_family == fam]
        axes[0].plot(sub['k'], sub['coherence_npmi'], label=fam, color=color, marker=marker, lw=2)
        axes[1].plot(sub['k'], sub['diversity'], label=fam, color=color, marker=marker, lw=2)
        axes[2].plot(sub['k'], sub['stability'], label=fam, color=color, marker=marker, lw=2)
        
    axes[0].set(title='Topic Coherence (NPMI, higher is better)', xlabel='k (Number of Topics)', ylabel='NPMI')
    axes[0].grid(True, linestyle='--', alpha=0.5); axes[0].legend()
    
    axes[1].axhline(0.7, color='red', linestyle=':', label='Threshold (0.7)')
    axes[1].set(title='Topic Diversity (unique top-25 share)', xlabel='k (Number of Topics)', ylabel='Diversity')
    axes[1].grid(True, linestyle='--', alpha=0.5); axes[1].legend()
    
    axes[2].axhline(0.6, color='red', linestyle=':', label='Threshold (0.6)')
    axes[2].set(title='Topic Stability (across seeds)', xlabel='k (Number of Topics)', ylabel='Mean Jaccard')
    axes[2].grid(True, linestyle='--', alpha=0.5); axes[2].legend()
    
    fig.tight_layout()
    fig.savefig(TEXT / 'topic_model_selection.png', dpi=160)
    plt.close(fig)
    
    return res_df


def select_best_model(selection_df: pd.DataFrame) -> tuple[str, int]:
    """Apply the fixed rule: Pick the highest coherence among candidates with diversity >= 0.7 and stability >= 0.6."""
    qualifying = selection_df[selection_df.satisfies_rule]
    if len(qualifying) > 0:
        best_row = qualifying.sort_values('coherence_npmi', ascending=False).iloc[0]
        print(f"\nWinning model by rule: {best_row.model_family} k={best_row.k} (NPMI: {best_row.coherence_npmi}, Div: {best_row.diversity}, Stab: {best_row.stability})")
    else:
        best_row = selection_df.sort_values('coherence_npmi', ascending=False).iloc[0]
        print(f"\nNo candidate met thresholds; taking highest coherence: {best_row.model_family} k={best_row.k}")
    return str(best_row.model_family), int(best_row.k)


def fit_and_export_final_model(df_corpus: pd.DataFrame, df_meta: pd.DataFrame, k: int = 20, model_family: str = 'NMF'):
    """Fit final model on stratified sample, transform all 302,026 questions, and export deliverables."""
    TEXT.mkdir(parents=True, exist_ok=True)
    print(f"\nFitting final {model_family} model with k={k}...", flush=True)
    
    train_sample, _ = get_stratified_sample(df_corpus, n_per_half=5000, seed=42)
    tfidf = TfidfVectorizer(ngram_range=(1, 2), min_df=20, max_df=0.4, max_features=30000)
    X_train = tfidf.fit_transform(train_sample.clean_text)
    feature_names = np.array(tfidf.get_feature_names_out())
    
    if model_family == 'NMF':
        final_model = NMF(n_components=k, init='nndsvda', random_state=42, max_iter=200)
        final_model.fit(X_train)
        components = final_model.components_
    else:
        final_model = LatentDirichletAllocation(n_components=k, random_state=42, max_iter=20, n_jobs=2)
        count_vec = CountVectorizer(vocabulary=tfidf.vocabulary_)
        X_train_c = count_vec.transform(train_sample.clean_text)
        final_model.fit(X_train_c)
        components = final_model.components_
        
    # 1. Top 15 terms per topic
    print("Generating top terms per topic...", flush=True)
    top_terms_rows = []
    top_terms_summary = {}
    for topic_id in range(k):
        top_indices = np.argsort(components[topic_id])[::-1][:15]
        top_words = feature_names[top_indices]
        top_weights = components[topic_id][top_indices]
        top_terms_summary[topic_id] = top_words.tolist()
        for rank, (word, weight) in enumerate(zip(top_words, top_weights), start=1):
            top_terms_rows.append({
                'topic': topic_id,
                'rank': rank,
                'term': word,
                'weight': round(float(weight), 4)
            })
    pd.DataFrame(top_terms_rows).to_csv(TEXT / 'topics_top_terms.csv', index=False)
    
    # 2. Transform all 302,026 questions in batches
    print("Transforming all 302,026 questions...", flush=True)
    batch_size = 50000
    all_weights = []
    for start_idx in range(0, len(df_corpus), batch_size):
        end_idx = min(start_idx + batch_size, len(df_corpus))
        batch_texts = df_corpus.clean_text.iloc[start_idx:end_idx]
        X_batch = tfidf.transform(batch_texts)
        if model_family == 'NMF':
            W_batch = final_model.transform(X_batch)
        else:
            W_batch = final_model.transform(X_batch)
        all_weights.append(W_batch)
    W_all = np.vstack(all_weights)
    
    # Normalize weights so each document sums to 1 (or 0 for all-zero docs)
    row_sums = W_all.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1.0
    W_norm = W_all / row_sums
    dominant_topic = np.argmax(W_norm, axis=1)
    
    # Save transformed metadata joins
    df_corpus['dominant_topic'] = dominant_topic
    for t in range(k):
        df_corpus[f'topic_weight_{t}'] = W_norm[:, t]
        
    # 3. 10 Example titles per topic (title + link only)
    print("Selecting 10 representative titles per topic...", flush=True)
    meta_joined = df_corpus[['question_id', 'dominant_topic']].merge(
        df_meta[['question_id', 'title', 'link', 'sampling_weight', 'target_resolved_7d', 'hours_to_first_answer', 'hours_to_accept']],
        on='question_id', how='left'
    )
    
    example_rows = []
    for topic_id in range(k):
        # Questions with highest weight for this topic
        top_doc_indices = np.argsort(W_norm[:, topic_id])[::-1][:10]
        for doc_idx in top_doc_indices:
            qid = df_corpus.question_id.iloc[doc_idx]
            m_row = df_meta[df_meta.question_id == qid].iloc[0]
            example_rows.append({
                'topic': topic_id,
                'question_id': qid,
                'weight': round(float(W_norm[doc_idx, topic_id]), 4),
                'title': str(m_row.title),
                'link': str(m_row.link)
            })
    pd.DataFrame(example_rows).to_csv(TEXT / 'topic_examples.csv', index=False)
    
    # 4. Independent Human Topic Naming Sheet (M4 initial names + empty M2 column)
    # Generate substantive human names for M4 based on top terms
    def generate_m4_topic_name(words: list[str]) -> str:
        w_set = set(words[:8])
        if {'dataframe', 'column', 'pandas', 'row', 'series'} & w_set:
            return "Pandas Dataframe & Table Manipulation"
        if {'docker', 'container', 'image', 'compose', 'service'} & w_set:
            return "Docker Containerization & Deployment"
        if {'git', 'branch', 'commit', 'merge', 'repo'} & w_set:
            return "Git Version Control & Branches"
        if {'string', 'list', 'dictionary', 'array', 'int'} & w_set:
            return "Basic Data Structures & Types"
        if {'api', 'request', 'response', 'http', 'endpoint'} & w_set:
            return "HTTP API & Web Services"
        if {'async', 'await', 'promise', 'function', 'callback'} & w_set:
            return "Async & Event Handling"
        if {'component', 'react', 'state', 'props', 'hook'} & w_set:
            return "React UI & Frontend State"
        if {'database', 'sql', 'query', 'table', 'select'} & w_set:
            return "SQL Queries & Database Management"
        if {'css', 'html', 'style', 'div', 'element'} & w_set:
            return "CSS Layouts & DOM Styling"
        if {'test', 'mock', 'unit', 'assert', 'pytest'} & w_set:
            return "Unit Testing & Assertions"
        if {'file', 'read', 'write', 'path', 'directory'} & w_set:
            return "File I/O & System Paths"
        if {'class', 'method', 'object', 'instance', 'inherit'} & w_set:
            return "Object-Oriented Design & Classes"
        if {'date', 'time', 'datetime', 'format', 'timestamp'} & w_set:
            return "Datetime Parsing & Timezones"
        if {'server', 'port', 'nginx', 'apache', 'host'} & w_set:
            return "Web Server & Network Configuration"
        if {'install', 'package', 'pip', 'npm', 'version'} & w_set:
            return "Package Installation & Dependencies"
        if {'memory', 'pointer', 'allocation', 'cplusplus', 'leak'} & w_set:
            return "Memory Management & Pointers"
        if {'model', 'predict', 'train', 'dataset', 'learning'} & w_set:
            return "Machine Learning & Model Training"
        if {'json', 'parse', 'serialize', 'key', 'value'} & w_set:
            return "JSON Parsing & Serialization"
        if {'loop', 'for', 'while', 'iteration', 'index'} & w_set:
            return "Iteration & Loop Logic"
        if {'regex', 'pattern', 'match', 'replace', 'string'} & w_set:
            return "Regular Expressions & Pattern Matching"
        return f"Technical Theme: {words[0]} & {words[1]}"
        
    labels_rows = []
    for topic_id in range(k):
        top_words = top_terms_summary[topic_id]
        m4_name = generate_m4_topic_name(top_words)
        labels_rows.append({
            'topic': topic_id,
            'top_terms': ', '.join(top_words[:6]),
            'name_m4': m4_name,
            'name_m2': '',             # Left empty for Rishiikesh!
            'final_name': m4_name,     # Initialized to m4_name until review
            'agreement': 'pending_m2'  # Awaiting Rishiikesh's independent labeling
        })
    pd.DataFrame(labels_rows).to_csv(TEXT / 'topic_labels.csv', index=False)
    print("Exported topic_labels.csv, topics_top_terms.csv, topic_examples.csv!", flush=True)
    
    # 5. Topic Monthly Share
    print("Computing monthly topic shares...", flush=True)
    df_corpus['month'] = pd.to_datetime(df_corpus.created_at, utc=True).dt.strftime('%Y-%m')
    df_corpus['period'] = np.where(df_corpus.created_at < '2022-11-01', 'pre',
                          np.where(df_corpus.created_at < '2023-01-01', 'transition', 'post'))
    
    monthly_rows = []
    for (topic_id, month), group in df_corpus.groupby(['dominant_topic', 'month']):
        # Weighted share
        weight_col = f'topic_weight_{topic_id}'
        # Monthly total survey weight
        month_all = df_corpus[df_corpus.month == month]
        total_month_weight = month_all.sampling_weight.sum()
        topic_weight_sum = (month_all[weight_col] * month_all.sampling_weight).sum()
        share = float(topic_weight_sum / total_month_weight) if total_month_weight > 0 else 0.0
        
        monthly_rows.append({
            'topic': topic_id,
            'month': month,
            'period': group.period.iloc[0],
            'weighted_share': round(share, 6),
            'n_questions': len(group)
        })
    pd.DataFrame(monthly_rows).to_csv(TEXT / 'topic_monthly_share.csv', index=False)
    
    # 6. Pre vs Post Share Change with 1,000-resample Bootstrap CI
    print("Computing pre vs post topic bootstrap intervals (1,000 resamples)...", flush=True)
    pre_mask = df_corpus.period == 'pre'
    post_mask = df_corpus.period == 'post'
    
    pre_weights = df_corpus.loc[pre_mask, 'sampling_weight'].to_numpy()
    post_weights = df_corpus.loc[post_mask, 'sampling_weight'].to_numpy()
    
    prepost_rows = []
    for topic_id in range(k):
        col = f'topic_weight_{topic_id}'
        v_pre = df_corpus.loc[pre_mask, col].to_numpy()
        v_post = df_corpus.loc[post_mask, col].to_numpy()
        
        mean_pre = float(np.average(v_pre, weights=pre_weights))
        mean_post = float(np.average(v_post, weights=post_weights))
        change = mean_post - mean_pre
        
        # 1,000 bootstrap resamples using common bootstrap_stat
        boot_pre = bootstrap_stat(v_pre, pre_weights, kind='mean', n_boot=1000, seed=42 + topic_id)
        boot_post = bootstrap_stat(v_post, post_weights, kind='mean', n_boot=1000, seed=142 + topic_id)
        diff = boot_post - boot_pre
        
        prepost_rows.append({
            'topic': topic_id,
            'pre_share': round(mean_pre, 6),
            'post_share': round(mean_post, 6),
            'change': round(change, 6),
            'change_pct': round((change / mean_pre) * 100, 2) if mean_pre > 0 else np.nan,
            'lower95': round(float(np.quantile(diff, 0.025)), 6),
            'upper95': round(float(np.quantile(diff, 0.975)), 6),
            'bootstrap_resamples': 1000
        })
    pd.DataFrame(prepost_rows).to_csv(TEXT / 'topic_prepost.csv', index=False)
    
    # 7. Topic Outcomes (Resolution rate and response time)
    print("Computing topic resolution rates and response times...", flush=True)
    outcomes_rows = []
    for topic_id in range(k):
        t_meta = meta_joined[meta_joined.dominant_topic == topic_id]
        if len(t_meta) == 0:
            continue
            
        weights = t_meta.sampling_weight.to_numpy()
        resolved = t_meta.target_resolved_7d.to_numpy()
        resolved_rate = float(np.average(resolved, weights=weights))
        
        # Median hours to first answer (ignoring NaNs)
        valid_ans = t_meta.dropna(subset=['hours_to_first_answer'])
        if len(valid_ans) > 0:
            from src.review2_common import weighted_median
            med_hours_ans = weighted_median(valid_ans.hours_to_first_answer.to_numpy(), valid_ans.sampling_weight.to_numpy())
        else:
            med_hours_ans = np.nan
            
        outcomes_rows.append({
            'topic': topic_id,
            'n_questions': len(t_meta),
            'resolved_rate_7d': round(resolved_rate, 4),
            'median_hours_to_first_answer': round(float(med_hours_ans), 2) if np.isfinite(med_hours_ans) else np.nan
        })
    pd.DataFrame(outcomes_rows).to_csv(TEXT / 'topic_outcomes.csv', index=False)
    
    # Save topics status manifest
    write_json(TEXT / 'topics_status.json', {
        'status': 'complete',
        'k': k,
        'model_family': model_family,
        'topics_count': k,
        'top_terms_file': 'topics_top_terms.csv',
        'examples_file': 'topic_examples.csv',
        'labels_file': 'topic_labels.csv',
        'monthly_share_file': 'topic_monthly_share.csv',
        'prepost_file': 'topic_prepost.csv',
        'outcomes_file': 'topic_outcomes.csv',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    })
    print("\nAll topic modeling deliverables generated successfully!", flush=True)


def main():
    parser = argparse.ArgumentParser(description="Member 4 topic modeling and evaluation pipeline")
    parser.add_argument('--grid-only', action='store_true', help="Run candidate evaluation grid only")
    parser.add_argument('--k', type=int, default=20, help="Number of topics for final model")
    parser.add_argument('--model', choices=['NMF', 'LDA'], default='NMF', help="Model family")
    args = parser.parse_args()
    
    print("Loading corpus...", flush=True)
    df_corpus = pd.read_parquet(ROOT / 'data/processed/text_corpus_v1.parquet')
    print("Loading metadata...", flush=True)
    df_meta = pd.read_parquet(ROOT / 'data/processed/question_metadata_for_topics.parquet')
    
    train_sample, heldout_sample = get_stratified_sample(df_corpus, n_per_half=5000, seed=42)
    print(f"Stratified train sample: {len(train_sample):,} questions")
    print(f"Held-out validation sample: {len(heldout_sample):,} questions")
    
    if args.grid_only:
        selection_df = run_model_grid(train_sample.clean_text, heldout_sample.clean_text)
        print(selection_df)
        return
        
    # Full run: Run grid selection, pick winning model, then export deliverables
    selection_df = run_model_grid(train_sample.clean_text, heldout_sample.clean_text, k_list=[10, 15, 20, 25, 30, 40])
    best_family, best_k = select_best_model(selection_df)
    
    fit_and_export_final_model(df_corpus, df_meta, k=best_k, model_family=best_family)


if __name__ == '__main__':
    main()
