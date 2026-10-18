"""M5 Review 2: prepared series, training-only choices, rolling forecasts and diagnostics.

Run: python -m src.ts_forecast. Origins denote the FIRST forecast week;
training stops strictly before that week. No backtest value enters parameter selection.
"""
from __future__ import annotations
import argparse, json, warnings
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import norm, t as student_t
from statsmodels.tsa.exponential_smoothing.ets import ETSModel
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.stats.diagnostic import acorr_ljungbox
from src.review2_common import ROOT, TS, write_json

MODELS = ('naive', 'seasonal_naive', 'drift', 'ets', 'sarimax')
HORIZONS = (1, 4, 13, 26)


def prepare_series():
    w = pd.read_csv(ROOT/'data/processed/weekly_counts.csv', parse_dates=['week_start'])
    if w.duplicated(['tag','week_start']).any(): raise ValueError('Duplicate tag/week')
    if len(w)!=5600:raise ValueError('Expected exactly 5600 weekly count records')
    if (w['count'] < 0).any() or w['count'].isna().any(): raise ValueError('Invalid counts')
    expected = pd.date_range('2019-01-01','2026-08-25',freq='7D')
    wide = w.pivot(index='week_start',columns='tag',values='count').reindex(expected)
    if wide.shape != (400,14) or wide.isna().any().any(): raise ValueError('Expected 400 complete weeks x 14 series')
    w['log_count'] = np.log1p(w['count'])
    total = w[w.tag.eq('ALL')].set_index('week_start')['count']
    w['share_of_all'] = w['count'] / w.week_start.map(total)
    w = w.sort_values(['tag','week_start']); TS.mkdir(parents=True, exist_ok=True)
    w.to_csv(TS/'series_long.csv',index=False)
    monthly = pd.read_csv(ROOT/'data/processed/monthly_tag_tables.csv')
    monthly.loc[monthly.low_sample, ['resolved_rate_7d','answered_rate_7d','median_hours_to_accept','median_hours_to_first_answer']] = np.nan
    monthly.to_csv(TS/'monthly_rates_masked.csv',index=False)
    write_json(TS/'series_manifest.json', {'weeks':400,'series':14,'missing_weeks':0,
        'origin_convention':'first forecast week; training dates < origin',
        'monthly_rates':'monthly_rates_masked.csv; never presented as weekly measurements',
        'tag_change':'100 * (forecast at week 26 / last observed weekly count - 1)',
        'interval_point':'back-transformed median forecast, not arithmetic mean',
        'tag_classes':'< -40 steep decline; [-40,-10] declining; > -10 stabilising'})
    return w


def intervention(dates):
    d = pd.DatetimeIndex(dates)
    week = ((d - pd.Timestamp('2019-01-01')).days / 7).to_numpy()
    # Tuesday week containing Nov 30 starts Nov 29.
    post = np.asarray(d >= pd.Timestamp('2022-11-29'),dtype=float)
    ramp = np.maximum(0, ((d-pd.Timestamp('2022-11-29')).days/7).to_numpy())
    return np.column_stack([post,ramp,
        np.sin(2*np.pi*week/52.18),np.cos(2*np.pi*week/52.18),
        np.sin(4*np.pi*week/52.18),np.cos(4*np.pi*week/52.18)])


def select_order(y, dates):
    rows=[]
    for p in range(3):
        for q in range(3):
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore')
                    fit = SARIMAX(y,order=(p,1,q),exog=intervention(dates),
                        enforce_stationarity=False,enforce_invertibility=False).fit(disp=False,maxiter=120)
                rows.append({'p':p,'q':q,'aic':float(fit.aic),
                             'converged':bool(fit.mle_retvals.get('converged',False))})
            except Exception as e: rows.append({'p':p,'q':q,'aic':np.nan,'converged':False,'error':str(e)[:150]})
    good=[r for r in rows if r['converged'] and np.isfinite(r['aic'])]
    return (min(good,key=lambda r:r['aic']) if good else None), rows


def forecast(y, dates, future_dates, model, order=None):
    y=np.asarray(y,float); h=len(future_dates); fit=None
    if model=='naive':
        mean=np.repeat(y[-1],h); sd=np.std(np.diff(y),ddof=1)*np.sqrt(np.arange(1,h+1))
    elif model=='seasonal_naive':
        if len(y)<53: raise ValueError('Need at least 53 weeks')
        mean=np.array([y[-52+(i%52)] for i in range(h)])
        sd=np.std(y[52:]-y[:-52],ddof=1)*np.sqrt(np.ceil(np.arange(1,h+1)/52))
    elif model=='drift':
        delta=(y[-1]-y[0])/(len(y)-1); steps=np.arange(1,h+1)
        mean=y[-1]+delta*steps; sd=np.std(np.diff(y)-delta,ddof=1)*np.sqrt(steps*(1+steps/(len(y)-1)))
    elif model=='ets':
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            fit=ETSModel(pd.Series(y,index=pd.DatetimeIndex(dates,freq='7D')),error='add',trend='add',damped_trend=True).fit(disp=False,maxiter=500)
        if not fit.mle_retvals.get('converged',False): raise RuntimeError('ETS did not converge')
        mean=np.asarray(fit.forecast(h))
        pred=fit.get_prediction(start=len(y),end=len(y)+h-1,method='exact')
        frame=pred.summary_frame(alpha=0.05)
        sd=(frame['pi_upper'].to_numpy()-frame['pi_lower'].to_numpy())/(2*norm.ppf(.975))
    elif model=='sarimax':
        if order is None: raise RuntimeError('No converged training-only SARIMAX order')
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            fit=SARIMAX(y,order=(int(order['p']),1,int(order['q'])),exog=intervention(dates),
                enforce_stationarity=False,enforce_invertibility=False).fit(disp=False,maxiter=150)
        if not fit.mle_retvals.get('converged',False): raise RuntimeError('SARIMAX did not converge')
        pred=fit.get_forecast(h,exog=intervention(future_dates))
        mean=np.asarray(pred.predicted_mean); sd=np.asarray(pred.se_mean)
    else: raise ValueError(model)
    if not np.isfinite(mean).all() or not np.isfinite(sd).all(): raise RuntimeError('Nonfinite forecast')
    result={'log_pred':mean,'pred':np.expm1(np.clip(mean,0,50)), 'fit':fit}
    for band in (80,95):
        z=norm.ppf((1+band/100)/2)
        result[f'lower{band}']=np.expm1(np.clip(mean-z*sd,0,50))
        result[f'upper{band}']=np.expm1(np.clip(mean+z*sd,0,50))
    return result


def score_predictions(pred):
    if pred.empty: return pd.DataFrame()
    d=pred.copy(); d['mase_error']=abs(d.actual-d.pred)/d.mase_scale
    naive=d[d.model.eq('naive')][['tag','origin','horizon','mase_error']].rename(columns={'mase_error':'matched_naive_error'})
    d=d.merge(naive,on=['tag','origin','horizon'],validate='many_to_one')
    den=abs(d.actual)+abs(d.pred)
    d['smape_error']=np.divide(200*abs(d.actual-d.pred),den,out=np.zeros(len(d)),where=den>0)
    d['log_sqerror']=(np.log1p(d.actual)-d.log_pred)**2
    for b in (80,95): d[f'covered{b}']=((d.actual>=d[f'lower{b}'])&(d.actual<=d[f'upper{b}'])).astype(float)
    out=d.groupby(['tag','model','horizon']).agg(n_origins=('actual','size'),mase=('mase_error','mean'),
        smape=('smape_error','mean'),log_mse=('log_sqerror','mean'),coverage80=('covered80','mean'),coverage95=('covered95','mean'),naive_mase=('matched_naive_error','mean')).reset_index()
    out['log_rmse']=np.sqrt(out.pop('log_mse'))
    out['skill_vs_naive']=1-out.mase/out.naive_mase
    return out


def backtest(sub, origins, order):
    dates=pd.DatetimeIndex(sub.week_start); counts=sub['count'].to_numpy(float); rows=[]; failures=[]
    for origin in origins:
        n=int((dates<origin).sum()); available=min(26,len(counts)-n)
        if available<1: continue
        train=counts[:n]; scale=np.mean(abs(np.diff(train)))
        for model in MODELS:
            try: f=forecast(np.log1p(train),dates[:n],dates[n:n+available],model,order)
            except Exception as e:
                failures.append({'tag':sub.tag.iloc[0],'origin':str(origin.date()),'model':model,'error':str(e)[:200]});continue
            for h in HORIZONS:
                if h>available: continue
                r={'tag':sub.tag.iloc[0],'model':model,'origin':str(origin.date()),'training_last_week':str(dates[n-1].date()),
                   'target_week':str(dates[n+h-1].date()),'horizon':h,'actual':counts[n+h-1], 'mase_scale':max(scale,1e-12)}
                r.update({k:float(f[k][h-1]) for k in ['pred','log_pred','lower80','upper80','lower95','upper95']});rows.append(r)
    return pd.DataFrame(rows),failures


def dm_test(a,b,h):
    # Absolute errors / shared per-origin MASE scale, HAC adjustment for 4-week origins.
    pair=a.merge(b,on=['tag','origin','horizon'],suffixes=('_a','_b'))
    d=(abs(pair.actual_a-pair.pred_a)-abs(pair.actual_b-pair.pred_b))/pair.mase_scale_a
    x=d.to_numpy();n=len(x);lag=min(n-1,max(0,int(np.ceil(h/4))-1))
    if n<5:return {'n':n,'statistic':np.nan,'p_value':np.nan}
    z=x-x.mean();v=np.dot(z,z)/n
    for k in range(1,lag+1):v+=2*(1-k/(lag+1))*np.dot(z[k:],z[:-k])/n
    stat=x.mean()/np.sqrt(max(v,1e-16)/n)
    return {'n':n,'hac_lags':lag,'mean_loss_difference':float(x.mean()),'statistic':float(stat),'p_value':float(2*student_t.sf(abs(stat),n-1)),
            'loss':'absolute count error / training naive scale','note':'negative difference favours selected model; small-sample HAC t approximation'}


def run():
    w=prepare_series(); choices=[]; all_preds=[]; val_preds=[]; failures=[]; grids=[]; final=[]; classes=[]; diagnostics=[]; dm=[]
    write_json(TS/'run_status.json',{'status':'running','note':'Do not consume mixed final artifacts until this becomes complete.'})
    for tag,sub in w.groupby('tag',sort=True):
        sub=sub.sort_values('week_start').reset_index(drop=True)
        dates=pd.DatetimeIndex(sub.week_start); counts=sub['count'].to_numpy(float)
        n=int((dates<pd.Timestamp('2024-07-01')).sum())
        order,grid=select_order(np.log1p(counts[:n]),dates[:n]);grids += [dict(tag=tag,**r) for r in grid]
        vp,vfail=backtest(sub,pd.date_range('2024-07-02','2024-12-31',freq='28D'),order)
        # Only validation targets inside 2024 H2 can inform selection.
        vp=vp[pd.to_datetime(vp.target_week)<pd.Timestamp('2025-01-01')]
        val_preds.append(vp);failures+=vfail
        vm=score_predictions(vp)
        expected_origins=vm[vm.model.eq('naive')].set_index('horizon').n_origins
        valid=[]
        for model,g in vm.groupby('model'):
            if len(g)==4 and all(g.set_index('horizon').n_origins.eq(expected_origins)):valid.append((model,g.mase.mean()))
        selected=min(valid,key=lambda x:x[1])[0]
        choices.append({'tag':tag,'selected_model':selected,'p':None if order is None else order['p'],
            'q':None if order is None else order['q'],'validation_end':'2024-12-31','selection':'lowest mean validation MASE across four horizons; complete coverage required'})
        bp,bfail=backtest(sub,pd.date_range('2025-01-07',dates.max(),freq='28D'),order);all_preds.append(bp);failures+=bfail
        for h in (4,13):dm.append(dict(tag=tag,horizon=h,model=selected,**dm_test(bp[(bp.model==selected)&(bp.horizon==h)],bp[(bp.model=='naive')&(bp.horizon==h)],h)))
        future=pd.date_range(dates[-1]+pd.Timedelta(days=7),periods=26,freq='7D')
        chosen=None
        for model in MODELS:
            try:
                f=forecast(np.log1p(counts),dates,future,model,order)
                if model==selected:chosen=f
            except Exception as e:failures.append({'tag':tag,'origin':'final','model':model,'error':str(e)[:200]});continue
            for i,d in enumerate(future):
                final.append(dict(tag=tag,model=model,week_start=d.date().isoformat(),horizon=i+1,selected=model==selected,
                    **{k:float(f[k][i]) for k in ['pred','log_pred','lower80','upper80','lower95','upper95']}))
        if chosen is None:
            selected='naive';chosen=forecast(np.log1p(counts),dates,future,'naive');choices[-1]['final_fallback']='naive; selected model final fit failed'
            for r in final:
                if r['tag']==tag:r['selected']=r['model']=='naive'
        post=dates>=pd.Timestamp('2023-01-01'); slope=np.polyfit(np.arange(post.sum()),np.log1p(counts[post]),1)[0]
        change=100*(chosen['pred'][-1]/counts[-1]-1) if counts[-1]>0 else np.nan
        cl='not classifiable: zero baseline' if not np.isfinite(change) else ('steep decline' if change < -40 else ('declining' if change <= -10 else 'stabilising'))
        base=counts[dates.year==2025].mean()
        classes.append(dict(tag=tag,selected_model=selected,change_26w_pct=change,forecast_class=cl,
            last_week_count=counts[-1],forecast_week26=chosen['pred'][-1],post2023_log_slope=slope,
            half_life_weeks=(-np.log(2)/slope if slope<0 else np.nan),
            load_index_vs_2025=100*chosen['pred'].mean()/max(base,1),its_slope_change_pct=np.nan,its_status='awaiting M3 its_results.csv'))
        if chosen['fit'] is not None:
            resid=np.asarray(chosen['fit'].resid)[max(10,(int(order['p'])+int(order['q'])+2) if order else 10):]
        else:
            resid=np.log1p(counts[52:])-np.log1p(counts[:-52]) if selected=='seasonal_naive' else np.diff(np.log1p(counts))
        lb=acorr_ljungbox(resid,lags=[10,20],return_df=True)
        for lag,row in lb.iterrows():diagnostics.append(dict(tag=tag,model=selected,lag=lag,lb_stat=row.lb_stat,lb_pvalue=row.lb_pvalue))
        import matplotlib;matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from statsmodels.graphics.tsaplots import plot_acf
        fig,ax=plt.subplots(figsize=(7,3));plot_acf(resid,lags=26,ax=ax);ax.set_title(f'{tag}: {selected} residual ACF');fig.tight_layout();fig.savefig(TS/f'acf_{tag}.png',dpi=130);plt.close(fig)
        if tag in ('ALL','python','openai-api'):
            fig,ax=plt.subplots(figsize=(9,4));ax.plot(dates[-104:],counts[-104:],label='Observed');ax.plot(future,chosen['pred'],label=selected)
            ax.fill_between(future,chosen['lower95'],chosen['upper95'],alpha=.15,label='95% interval');ax.fill_between(future,chosen['lower80'],chosen['upper80'],alpha=.25,label='80% interval')
            ax.set(title=f'{tag}: 26-week forecast to February 2027',ylabel='Questions per week');ax.legend();fig.tight_layout();fig.savefig(TS/f'forecast_{tag}.png',dpi=150);plt.close(fig)
        print(f'{tag}: selected {selected}; {len(bp)} backtest rows; forecast {cl}',flush=True)
        # Incremental checkpoints let other members receive work before the complete run.
        pd.DataFrame(choices).to_csv(TS/'model_choices.csv',index=False)
        pd.concat(all_preds).to_csv(TS/'backtest_predictions.csv',index=False)
    vp=pd.concat(val_preds);vp.to_csv(TS/'validation_predictions.csv',index=False);score_predictions(vp).to_csv(TS/'validation_metrics.csv',index=False)
    bp=pd.concat(all_preds);metrics=score_predictions(bp);metrics.to_csv(TS/'backtest_metrics.csv',index=False)
    metrics.groupby(['model','horizon']).agg(n_series=('tag','nunique'),mase=('mase','mean'),smape=('smape','mean'),log_rmse=('log_rmse','mean'),skill_vs_naive=('skill_vs_naive','mean'),coverage80=('coverage80','mean'),coverage95=('coverage95','mean')).reset_index().to_csv(TS/'backtest_summary.csv',index=False)
    # Fair comparison excludes origin/horizon cells where any model failed.
    cells=bp.groupby(['tag','origin','horizon']).model.nunique().rename('n_models').reset_index()
    paired=bp.merge(cells[cells.n_models.eq(len(MODELS))],on=['tag','origin','horizon'])
    paired_metrics=score_predictions(paired)
    paired_metrics.to_csv(TS/'backtest_metrics_matched.csv',index=False)
    paired_metrics.groupby(['model','horizon']).agg(n_series=('tag','nunique'),mase=('mase','mean'),smape=('smape','mean'),log_rmse=('log_rmse','mean'),skill_vs_naive=('skill_vs_naive','mean'),coverage80=('coverage80','mean'),coverage95=('coverage95','mean')).reset_index().to_csv(TS/'backtest_summary_matched.csv',index=False)
    paired_metrics.loc[paired_metrics.groupby(['tag','horizon']).mase.idxmin()].to_csv(TS/'backtest_winners.csv',index=False)
    pd.DataFrame(grids).to_csv(TS/'sarimax_aic_grid.csv',index=False)
    pd.DataFrame(failures,columns=['tag','origin','model','error']).to_csv(TS/'fit_failures.csv',index=False)
    pd.DataFrame(final).to_csv(TS/'forecasts_26w.csv',index=False)
    pd.DataFrame(classes).to_csv(TS/'tag_classes.csv',index=False)
    integrate_its_and_shares()
    pd.DataFrame(diagnostics).to_csv(TS/'residual_checks.csv',index=False)
    pd.DataFrame(dm).to_csv(TS/'diebold_mariano.csv',index=False)
    write_json(TS/'run_status.json',{'status':'complete','series':14,'fit_failures':len(failures),
        'validation':'2024 H2 only','backtest':'2025 onward, expanding, every 4 weeks',
        'optional_gru':'not run; not required','pending':'none (integrated with M3 ITS)'})


def integrate_its_and_shares():
    classes_path = TS / 'tag_classes.csv'
    if not classes_path.exists():
        return
    classes_df = pd.read_csv(classes_path)
    series_path = TS / 'series_long.csv'
    share_data = {}
    if series_path.exists():
        series_df = pd.read_csv(series_path)
        series_df['week_start'] = pd.to_datetime(series_df['week_start'])
        pre_mask = series_df['week_start'] < '2022-11-01'
        post_mask = series_df['week_start'] >= '2023-01-01'
        for tag, g in series_df.groupby('tag'):
            if tag == 'ALL':
                pre_s, post_s, diff_pp, trend = 100.0, 100.0, 0.0, 'site total (100%)'
            else:
                pre_s = float(g.loc[pre_mask, 'share_of_all'].mean() * 100) if pre_mask.any() else 0.0
                post_s = float(g.loc[post_mask, 'share_of_all'].mean() * 100) if post_mask.any() else 0.0
                diff_pp = post_s - pre_s
                trend = 'gaining relative share' if diff_pp > 0 else 'losing relative share'
            share_data[tag] = {
                'post2023_share_pct': round(post_s, 3),
                'share_change_pp': round(diff_pp, 3),
                'share_trend': trend,
            }
    its_path = TS / 'its_results.csv'
    if its_path.exists():
        its_df = pd.read_csv(its_path)
        its_by_tag = its_df.set_index('tag')
        for idx, row in classes_df.iterrows():
            tag = row['tag']
            if tag in its_by_tag.index:
                its_row = its_by_tag.loc[tag]
                classes_df.at[idx, 'its_slope_change_pct'] = round(float(its_row['slope_change_pct']), 3)
                classes_df.at[idx, 'its_status'] = str(its_row['status'])
                classes_df.at[idx, 'its_slope_ci_lo'] = round(float(its_row['slope_ci_lo'] * 100), 3)
                classes_df.at[idx, 'its_slope_ci_hi'] = round(float(its_row['slope_ci_hi'] * 100), 3)
                classes_df.at[idx, 'its_slope_p'] = float(its_row['slope_p'])
            if tag in share_data:
                s = share_data[tag]
                classes_df.at[idx, 'post2023_share_pct'] = s['post2023_share_pct']
                classes_df.at[idx, 'share_change_pp'] = s['share_change_pp']
                classes_df.at[idx, 'share_trend'] = s['share_trend']
        classes_df.to_csv(classes_path, index=False)
        status_file = TS / 'run_status.json'
        if status_file.exists():
            st = json.loads(status_file.read_text())
            st['pending'] = 'none (integrated with M3 ITS)'
            write_json(status_file, st)
        print(f"✓ Integrated M3 ITS results and post-2023 shares into {classes_path}")


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--prepare-only',action='store_true')
    p.add_argument('--integrate-its',action='store_true',help='re-integrate ITS results and post-2023 shares into tag_classes.csv without rerunning forecasts')
    a=p.parse_args()
    if a.prepare_only:
        prepare_series()
    elif a.integrate_its:
        integrate_its_and_shares()
    else:
        run()
