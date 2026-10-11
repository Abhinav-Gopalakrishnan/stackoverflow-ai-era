"""Review 2 contracts for Member 5 forecasting."""
import unittest
import numpy as np
import pandas as pd
from src.ts_forecast import forecast, backtest, score_predictions

class Contracts(unittest.TestCase):
    def test_naive_forecast_never_uses_future(self):
        dates=pd.date_range('2020-01-07',periods=110,freq='7D')
        q=pd.DataFrame({'tag':'demo','week_start':dates,'count':np.arange(110)+10})
        origin=dates[80]
        a,_=backtest(q,[origin],None)
        q.loc[80:,'count']=100000
        b,_=backtest(q,[origin],None)
        for model in ['naive','seasonal_naive','drift','ets']:
            np.testing.assert_allclose(a[a.model.eq(model)].pred,b[b.model.eq(model)].pred)
        self.assertTrue((pd.to_datetime(a.training_last_week)<pd.to_datetime(a.origin)).all())
    def test_naive_identity_and_intervals(self):
        y=np.log1p(np.arange(60)+1)
        f=forecast(y,pd.date_range('2020-01-07',periods=60,freq='7D'),pd.date_range('2021-03-02',periods=4,freq='7D'),'naive')
        np.testing.assert_allclose(f['pred'],60)
        self.assertTrue((f['lower95']<=f['lower80']).all())
        self.assertTrue((f['upper95']>=f['upper80']).all())
    def test_forecast_skill_matches_origin(self):
        rows=[]
        for m,p,o in [('naive',12,'a'),('naive',100,'b'),('ets',11,'a')]:
            rows.append(dict(tag='x',model=m,origin=o,horizon=1,actual=10,pred=p,log_pred=np.log1p(p),mase_scale=2,lower80=0,upper80=20,lower95=0,upper95=30))
        t=score_predictions(pd.DataFrame(rows))
        self.assertAlmostEqual(t[t.model.eq('ets')].skill_vs_naive.iloc[0],.5)

if __name__ == "__main__": unittest.main()
