"""Check measured topic evidence without fitting any model or changing outputs."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.topics import K_LIST, SEEDS, select_best_model


def main():
    folder = ROOT/'reports/review2/text'
    manifest = json.loads((folder/'topic_grid_manifest.json').read_text())
    status = json.loads((folder/'topics_status.json').read_text())
    assert manifest['status'] == status['status'] == 'complete'
    assert manifest['fingerprint'] == status['fingerprint']
    grid = pd.read_csv(folder/'topic_model_selection.csv')
    seeds = pd.read_csv(folder/'topic_model_seed_results.csv')
    expected = {(f, k) for f in ['NMF', 'LDA'] for k in K_LIST}
    assert set(zip(grid.model_family,grid.k)) == expected
    assert len(grid) == len(expected) and len(seeds) == len(expected)*len(SEEDS)
    assert not seeds.duplicated(['model_family','k','seed']).any()
    for row in grid.itertuples():
        runs = seeds[seeds.model_family.eq(row.model_family) & seeds.k.eq(row.k)]
        assert set(runs.seed) == set(SEEDS)
        np.testing.assert_allclose(row.coherence_npmi,runs.coherence_npmi.mean())
        np.testing.assert_allclose(row.diversity,runs.diversity.mean())
        assert bool(row.satisfies_rule) == (row.diversity>=.7 and row.stability>=.6)
    assert grid.coherence_npmi.between(-1,1).all()
    assert grid.diversity.between(0,1).all() and grid.stability.between(0,1).all()
    split = pd.read_csv(folder/'topic_split_manifest.csv')
    assert split.question_id.is_unique
    counts = split.split.value_counts()
    assert counts['training'] == manifest['training_rows']
    assert counts['coherence_reference'] == manifest['reference_rows'] == 20000
    family,k = select_best_model(grid)
    assert status['model_family'] == family and status['k'] == k
    topics = pd.read_parquet(ROOT/'data/processed/question_topics_v2.parquet')
    corpus = pd.read_parquet(ROOT/'data/processed/text_corpus_v1.parquet',columns=['question_id'])
    assert topics.question_id.is_unique and topics.question_id.equals(corpus.question_id)
    weights = topics[[f'topic_weight_{i}' for i in range(k)]].to_numpy()
    assert np.isfinite(weights).all() and (weights>=0).all()
    totals = weights.sum(axis=1)
    assert np.all((totals == 0) | np.isclose(totals,1,atol=1e-6))
    assert np.array_equal(topics.dominant_topic.eq(-1),totals==0)
    for name in ['topic_monthly_share','topic_prepost','topic_outcomes']:
        global_data = pd.read_csv(folder/f'{name}.csv')
        by_tag = pd.read_csv(folder/f'{name}_by_tag.csv')
        pd.testing.assert_frame_equal(global_data,by_tag[by_tag.tag.eq('ALL')].drop(columns='tag').reset_index(drop=True))
        assert by_tag.tag.nunique() == 14
    prepost = pd.read_csv(folder/'topic_prepost_by_tag.csv')
    assert prepost.bootstrap_resamples.eq(1000).all()
    np.testing.assert_allclose(prepost.change,prepost.post_share-prepost.pre_share,atol=1e-12)
    assert len(pd.read_csv(folder/'topics_top_terms.csv')) == 15*k
    print(f'PASS: {len(grid)} measured candidates, {len(seeds)} seed fits, disjoint split, '
          f'{len(topics):,} transformed IDs, {k} topics, 14 tag groups, bootstrap and global/tag consistency.')


if __name__ == '__main__':
    main()
