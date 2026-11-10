"""Additional report figures from saved project evidence; no model refitting."""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[2]
O=R/'reports/final_submission/figures'
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
def save(name):
    plt.tight_layout();plt.savefig(O/name,dpi=200,bbox_inches='tight');plt.close()
d=pd.read_csv(R/'dashboard/data/monthly_rates_masked.csv')
d=d[d.tag.eq('ALL')].sort_values('month')
d.loc[d.low_sample,'resolved_rate_7d']=float('nan')
fig,ax=plt.subplots(figsize=(7,2.6))
ax.plot(pd.to_datetime(d.month),100*d.resolved_rate_7d,color='#254b70',label='Weighted monthly proxy rate')
ax.axvspan(pd.Timestamp('2022-11-01'),pd.Timestamp('2023-01-01'),color='#a54932',alpha=.15,label='Excluded transition in pre/post summaries')
ax.set(xlabel='Month',ylabel='Proxy-positive questions (%)',ylim=(0,65));ax.legend(fontsize=8)
save('resolution_monthly.png')
fig,ax=plt.subplots(figsize=(6.4,2.4))
values=[[109,145],[40,95]]
ax.imshow(values,cmap='Blues',vmin=0,vmax=160,aspect='auto')
for i in range(2):
 for j in range(2):ax.text(j,i,str(values[i][j]),ha='center',va='center',fontsize=16,color='white' if values[i][j]>100 else 'black')
ax.set_xticks([0,1],['Predicted negative','Predicted positive'])
ax.set_yticks([0,1],['Actual negative','Actual positive'])
ax.set(xlabel='Model classification at threshold 0.2971',title='August 2026 resolution proxy | 389 questions')
save('confusion_report.png')
d=pd.read_csv(R/'reports/review2/text/topic_model_selection.csv')
fig,ax=plt.subplots(figsize=(7,2.5))
for family,colour in [('NMF','#254b70'),('LDA','#a54932')]:
 x=d[d.model_family.eq(family)].sort_values('k')
 ax.plot(x.k,x.stability,'o-',label=family,color=colour)
ax.axhline(.6,color='gray',ls='--',label='Minimum selection stability')
ax.set(xlabel='Number of topics',ylabel='Seed stability',ylim=(0,1.05));ax.legend(fontsize=8)
save('topic_stability_report.png')
