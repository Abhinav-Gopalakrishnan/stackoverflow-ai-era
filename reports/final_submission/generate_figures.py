from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[2];O=R/'reports/final_submission/figures';O.mkdir(exist_ok=True)
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
def save(name):plt.tight_layout();plt.savefig(O/name,dpi=200,bbox_inches='tight');plt.close()
d=pd.read_csv(R/'data/processed/weekly_counts.csv');d=d[d.tag.eq('ALL')]
fig,ax=plt.subplots(figsize=(7,2.5));ax.plot(pd.to_datetime(d.week_start),d['count'],color='#254b70');ax.axvline(pd.Timestamp('2022-11-30'),color='#a54932',ls='--',label='ChatGPT launch');ax.set(ylabel='Questions per week',xlabel='Week starting',title='Separately collected site-wide API totals');ax.legend();save('volume.png')
d=pd.read_csv(R/'reports/review2/text/topic_prepost.csv').merge(pd.read_csv(R/'reports/review2/text/topic_labels.csv')[['topic','final_name']],on='topic');d=pd.concat([d.nsmallest(3,'change'),d.nlargest(3,'change')]).sort_values('change')
fig,ax=plt.subplots(figsize=(7,2.7));ax.barh(d.final_name,d.change*100,color=['#a54932' if x<0 else '#254b70' for x in d.change]);ax.axvline(0,color='gray',lw=.6);ax.set(xlabel='Post minus pre share (percentage points)');save('topics.png')
d=pd.read_csv(R/'reports/review2/ts/backtest_predictions.csv');d=d[(d.tag=='ALL')&(d.model=='sarimax')];origins=d.groupby('origin').horizon.nunique();origin=origins[origins.eq(4)].index.max();d=d[d.origin.eq(origin)].sort_values('horizon')
fig,ax=plt.subplots(figsize=(7,2.3));ax.plot(d.horizon,d.actual,'o-',label='Observed');ax.plot(d.horizon,d.pred,'s--',label='SARIMAX');ax.set(xlabel='Forecast horizon (weeks)',ylabel='Questions',title='Historical forecast endpoints | origin '+d.origin.iloc[0]);ax.legend();save('backtest.png')
from matplotlib.patches import FancyBboxPatch
fig,ax=plt.subplots(figsize=(7,1.25));ax.axis('off');labels=['API\ncollection','Unit 1\nClean and\nexplore','Unit 2\nPredict\nresolution','Unit 3\nForecast and\nmine','Streamlit\nExplore\nresults']
for i,label in enumerate(labels):
 x=.01+i*.2
 ax.add_patch(FancyBboxPatch((x,.13),.17,.74,boxstyle='round,pad=0.004',facecolor='#f3f5f7',edgecolor='#8797a5'))
 ax.text(x+.085,.5,label,ha='center',va='center',fontsize=9)
 if i<4:ax.annotate('',xy=(x+.196,.5),xytext=(x+.174,.5),arrowprops=dict(arrowstyle='->',lw=.8,shrinkA=0,shrinkB=0))
ax.set_xlim(0,1);ax.set_ylim(0,1);save('workflow.png')

d=pd.read_csv(R/'dashboard/data/classifier_validation.csv')
fig,ax=plt.subplots(figsize=(7,1.7));ax.barh(d.model,d.pr_auc,color='#254b70');ax.set_xlim(0,.57);ax.set_xlabel('Validation PR-AUC (average precision)')
for i,r in enumerate(d.itertuples()):ax.text(r.pr_auc+.008,i,f'{r.pr_auc:.4f}',va='center')
ax.invert_yaxis();save('models.png')

from PIL import Image
r=R/'reports/final_validation/screenshots'
a=Image.open(r/'01_overview.png');b=Image.open(r/'02_overview_post.png')
c=Image.new('RGB',(a.width+b.width,max(a.height,b.height)),'white');c.paste(a,(0,0));c.paste(b,(a.width,0));c.save(O/'dashboard_states.png')
