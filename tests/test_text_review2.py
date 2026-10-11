"""Review 2 contracts for Member 2 text preparation."""
import unittest
import numpy as np
import pandas as pd
from src.review2_common import period, weighted_median, bootstrap_stat
from src.text_prep import normalize
from src.sentiment import analyzer

class Contracts(unittest.TestCase):
    def test_technology_tokens_and_html(self):
        s=normalize('C++ / C# .NET node.js next.js vue.js asp.net &#39;error&#39; https://x.com C:\\temp\\test.py 123456')
        for t in ['cplusplus','csharp','dotnet','nodejs','nextjs','vuejs','aspnet','urltoken','pathtoken','numbertoken','error']:self.assertIn(t,s)
    def test_transition_period(self):
        self.assertEqual(list(period(pd.Series(['2022-10-31','2022-11-01','2022-12-31','2023-01-01']))),['pre','transition','transition','post'])
    def test_weighted_bootstrap_preserves_constant(self):
        np.testing.assert_allclose(bootstrap_stat([3,3],[1,20],n_boot=50),3)
        self.assertEqual(weighted_median([1,10],[1,9]),10)
    def test_technical_word_overrides(self):
        a=analyzer()
        self.assertEqual(a.lexicon['fatal'],0)
        self.assertLess(a.polarity_scores('I am desperate and frustrated')['compound'],0)

if __name__ == "__main__": unittest.main()
