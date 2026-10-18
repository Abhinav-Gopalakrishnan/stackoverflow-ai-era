"""Unit tests and contracts for Member 4 topic modeling and keyword shift."""
import unittest
import numpy as np
import pandas as pd
import scipy.sparse as sp
import tempfile
from pathlib import Path
from unittest.mock import patch
from src import topics
from src.topics import compute_npmi_coherence, compute_diversity, compute_stability
from src.keywords import compute_monroe_log_odds

class TestTopicModeling(unittest.TestCase):
    def test_training_and_reference_questions_are_disjoint(self):
        corpus = pd.DataFrame({
            'question_id': range(12), 'n_tokens': [3] * 12,
            'created_at': pd.to_datetime(['2020-01-01'] * 6 + ['2020-07-01'] * 6, utc=True),
            'clean_text': ['sample prose'] * 12})
        train, reference = topics.get_stratified_sample(corpus, n_per_half=2)
        self.assertEqual(len(train), 4)
        self.assertEqual(len(reference), 8)
        self.assertFalse(set(train.question_id) & set(reference.question_id))

    def test_npmi_handles_terms_in_every_document(self):
        score = compute_npmi_coherence([[0, 1]], sp.csr_matrix(np.ones((5, 2))))
        self.assertTrue(np.isfinite(score))
        self.assertGreaterEqual(score, -1)
        self.assertLessEqual(score, 1)

    def test_joint_bootstrap_preserves_constant_topic_weights(self):
        values = np.tile([.75, .25], (8, 1))
        draws = topics._bootstrap_means(values, np.arange(1, 9), n_boot=50)
        np.testing.assert_allclose(draws, np.tile([.75, .25], (50, 1)))

    def test_grid_measures_both_families_and_all_three_seeds(self):
        texts = pd.Series(['python package error install'] * 30 +
                          ['docker image container compose'] * 30 +
                          ['react component render state'] * 30 +
                          ['pandas dataframe column row'] * 30)
        reference = texts.sample(n=40, random_state=8).reset_index(drop=True)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.object(topics, 'TEXT', root / 'results'), \
                 patch.object(topics, 'CACHE_DIR', root / 'cache'), \
                 patch.object(topics, 'NMF_ITERATIONS', 30), \
                 patch.object(topics, 'LDA_ITERATIONS', 2):
                grid = topics.run_model_grid(texts, reference, k_list=[2])
            seeds = pd.read_csv(root / 'results/topic_model_seed_results.csv')
            self.assertEqual(set(grid.model_family), {'NMF', 'LDA'})
            self.assertEqual(len(seeds), 6)
            self.assertTrue(grid.seeds.eq(3).all())
            for row in grid.itertuples():
                measured = seeds[seeds.model_family.eq(row.model_family)]
                self.assertAlmostEqual(row.coherence_npmi, measured.coherence_npmi.mean())
                self.assertEqual(row.training_rows, len(texts))
                self.assertEqual(row.reference_rows, len(reference))

    def test_npmi_coherence_bounded(self):
        # Synthetic binary document-term matrix (100 docs, 5 terms)
        X = sp.csr_matrix([
            [1, 1, 0, 0, 0],
            [1, 1, 0, 0, 0],
            [1, 1, 0, 0, 0],
            [0, 0, 1, 1, 0],
            [0, 0, 1, 1, 0],
            [0, 0, 0, 0, 1],
        ] * 15)  # 90 docs
        
        # Perfect co-occurrence of terms 0 and 1
        npmi_high = compute_npmi_coherence([[0, 1]], X)
        self.assertGreater(npmi_high, 0.5)
        self.assertLessEqual(npmi_high, 1.0)
        
        # Disjoint terms 0 and 2
        npmi_low = compute_npmi_coherence([[0, 2]], X)
        self.assertEqual(npmi_low, -1.0)

    def test_diversity_metric(self):
        # 2 topics with completely disjoint words
        top_words_disjoint = [[0, 1, 2], [3, 4, 5]]
        self.assertEqual(compute_diversity(top_words_disjoint, top_n=3), 1.0)
        
        # 2 topics with identical words
        top_words_identical = [[0, 1, 2], [0, 1, 2]]
        self.assertEqual(compute_diversity(top_words_identical, top_n=3), 0.5)

    def test_stability_metric(self):
        # 2 runs with identical top 10 words
        run1 = [{'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j'}]
        run2 = [{'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j'}]
        stab = compute_stability([run1, run2])
        self.assertEqual(stab, 1.0)
        
        # Completely disjoint
        run3 = [{'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't'}]
        stab_disjoint = compute_stability([run1, run3])
        self.assertEqual(stab_disjoint, 0.0)

    def test_monroe_log_odds_direction(self):
        # Post corpus talks exclusively about "chatgpt" and "ai", pre talks about "jquery"
        pre_texts = pd.Series(["jquery selector element click table"] * 50)
        post_texts = pd.Series(["chatgpt ai assistant model prompt"] * 50)
        w_pre = np.ones(50)
        w_post = np.ones(50)
        
        res = compute_monroe_log_odds(pre_texts, w_pre, post_texts, w_post, min_df=5, max_df=1.0)
        self.assertFalse(res.empty)
        # chatgpt should have a high positive z-score (rising)
        chatgpt_row = res[res.term == 'chatgpt']
        self.assertFalse(chatgpt_row.empty)
        self.assertGreater(chatgpt_row.z_score.iloc[0], 2.0)
        
        # jquery should have a negative z-score (falling)
        jquery_row = res[res.term == 'jquery']
        self.assertFalse(jquery_row.empty)
        self.assertLess(jquery_row.z_score.iloc[0], -2.0)

if __name__ == '__main__':
    unittest.main()
