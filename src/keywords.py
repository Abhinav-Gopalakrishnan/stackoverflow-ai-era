"""Member 4 (Nishanth): Distinctive words shift pre- vs post-AI adoption.
Implements Monroe, Colaresi & Quinn (2008) weighted log-odds ratio with an informative Dirichlet prior.

Usage:
  python -m src.keywords
"""
from __future__ import annotations
import argparse, time
from collections import Counter
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from src.review2_common import ROOT, TEXT, write_json

def compute_monroe_log_odds(texts_pre: pd.Series, weights_pre: np.ndarray,
                           texts_post: pd.Series, weights_post: np.ndarray,
                           min_df: int = 20, max_df: float = 0.4, max_features: int = 15000,
                           prior_scaling: float = 1000.0) -> pd.DataFrame:
    """Compute weighted log-odds ratio with informative Dirichlet prior (Monroe et al., 2008)."""
    cv = CountVectorizer(ngram_range=(1, 2), min_df=min_df, max_df=max_df, max_features=max_features)
    # Fit vocabulary on combined texts
    combined = pd.concat([texts_pre, texts_post], ignore_index=True)
    cv.fit(combined)
    vocab = np.array(cv.get_feature_names_out())
    
    # Weighted word frequencies
    X_pre = cv.transform(texts_pre)
    X_post = cv.transform(texts_post)
    
    # y1: post, y2: pre
    y1 = np.array(X_post.T.dot(weights_post)).flatten()
    y2 = np.array(X_pre.T.dot(weights_pre)).flatten()
    
    n1 = y1.sum()
    n2 = y2.sum()
    
    # Background counts for Dirichlet prior
    y_background = y1 + y2
    n_background = n1 + n2
    
    if n_background <= 0 or n1 <= 0 or n2 <= 0:
        return pd.DataFrame()
        
    # Informative Dirichlet prior
    alpha = prior_scaling * (y_background / n_background)
    alpha0 = prior_scaling
    
    # Monroe log-odds formula
    odds_post = (y1 + alpha) / (n1 + alpha0 - (y1 + alpha))
    odds_pre = (y2 + alpha) / (n2 + alpha0 - (y2 + alpha))
    
    delta = np.log(odds_post) - np.log(odds_pre)
    variance = (1.0 / (y1 + alpha)) + (1.0 / (y2 + alpha))
    z_scores = delta / np.sqrt(variance)
    
    res = pd.DataFrame({
        'term': vocab,
        'z_score': z_scores,
        'log_odds': delta,
        'count_pre': y2,
        'count_post': y1,
        'freq_pre_pct': (y2 / n2) * 100.0,
        'freq_post_pct': (y1 / n1) * 100.0
    })
    return res.sort_values('z_score', ascending=False).reset_index(drop=True)


def run_keyword_shift():
    TEXT.mkdir(parents=True, exist_ok=True)
    print("Loading corpus for keyword analysis...", flush=True)
    df_corpus = pd.read_parquet(ROOT / 'data/processed/text_corpus_v1.parquet')
    
    # Period segmentation: pre <= 2022-10, post >= 2023-01
    df_corpus['period'] = np.where(df_corpus.created_at < '2022-11-01', 'pre',
                          np.where(df_corpus.created_at < '2023-01-01', 'transition', 'post'))
    
    # Exclude transition period
    contrast_df = df_corpus[df_corpus.period.isin(['pre', 'post']) & (df_corpus.n_tokens > 0)].copy()
    
    scopes = ['ALL', 'python', 'javascript', 'powerbi']
    all_results = []
    
    for scope in scopes:
        print(f"\nComputing Monroe log-odds for scope: {scope}...", flush=True)
        if scope == 'ALL':
            sub = contrast_df
        else:
            sub = contrast_df[contrast_df.tags.apply(lambda ts: scope in ts if isinstance(ts, (list, np.ndarray)) else False)]
            
        pre_sub = sub[sub.period == 'pre']
        post_sub = sub[sub.period == 'post']
        
        print(f"  Pre: {len(pre_sub):,} questions, Post: {len(post_sub):,} questions", flush=True)
        if len(pre_sub) < 50 or len(post_sub) < 50:
            print(f"  Skipping {scope}: insufficient sample size", flush=True)
            continue
            
        df_stats = compute_monroe_log_odds(
            pre_sub.clean_text, pre_sub.sampling_weight.to_numpy(),
            post_sub.clean_text, post_sub.sampling_weight.to_numpy()
        )
        
        # Top 30 rising (highest z)
        top_rising = df_stats.head(30).copy()
        top_rising['direction'] = 'rising'
        top_rising['rank'] = np.arange(1, len(top_rising) + 1)
        top_rising['tag_scope'] = scope
        
        # Top 30 falling (lowest z)
        top_falling = df_stats.tail(30).iloc[::-1].copy()
        top_falling['direction'] = 'falling'
        top_falling['rank'] = np.arange(1, len(top_falling) + 1)
        top_falling['tag_scope'] = scope
        
        combined_scope = pd.concat([top_rising, top_falling], ignore_index=True)
        all_results.append(combined_scope)
        
    final_df = pd.concat(all_results, ignore_index=True)
    out_path = TEXT / 'keywords_prepost.csv'
    final_df.to_csv(out_path, index=False)
    print(f"\nSaved keywords_prepost.csv with {len(final_df)} rows to {out_path}", flush=True)
    
    plot_keyword_shift(final_df)


def plot_keyword_shift(final_df):
    """Business-facing plot excludes preprocessing placeholders; raw rankings remain saved."""
    placeholders=r'(?:^|\s)(?:numbertoken|pathtoken|urltoken)(?:\s|$)'
    display=final_df[~final_df.term.astype(str).str.contains(placeholders,regex=True)]
    fig,axes=plt.subplots(1,2,figsize=(14,6))
    for ax,direction,color in zip(axes,['rising','falling'],['#2ca02c','#d62728']):
        frame=display[(display.tag_scope=='ALL')&(display.direction==direction)].sort_values('rank').head(15).iloc[::-1]
        ax.barh(frame.term,frame.z_score.abs(),color=color,alpha=.85)
        ax.set(title=f'Collected question sample: {direction} terms',xlabel='|Monroe log-odds z-score|')
        ax.grid(axis='x',linestyle='--',alpha=.3)
    fig.suptitle('Preprocessing placeholders excluded from this view; raw rankings remain in CSV',fontsize=10)
    fig.tight_layout();fig.savefig(TEXT/'keywords_shift_all.png',dpi=160);plt.close(fig)


if __name__ == '__main__':
    run_keyword_shift()
