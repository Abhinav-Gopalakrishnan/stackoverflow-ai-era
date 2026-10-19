"""Measured topic comparison and tag-specific, weighted topic summaries."""
import sys
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

_repo_root = Path(__file__).resolve().parents[2]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))
from dashboard.common import render_chart, load_data, render_sidebar, filter_observations, focus_tag

st.set_page_config(page_title='Topics', page_icon='🏷️', layout='wide')
filters = render_sidebar(log=False, events=False)
st.title('Topic Mining & Changing Question Shares')
st.markdown('NMF and LDA were compared on the same training sample, vocabulary, disjoint coherence reference and three seeds. Names are automatic descriptions; independent human naming agreement is unavailable.')
selected_tag = focus_tag(filters, 'page4_tag_selector')
terms = load_data('topics_top_terms.csv')
labels = load_data('topic_labels.csv')
monthly = load_data('topic_monthly_share_by_tag.csv')
prepost = load_data('topic_prepost_by_tag.csv').query('tag == @selected_tag')
outcomes = load_data('topic_outcomes_by_tag.csv').query('tag == @selected_tag')
examples = load_data('topic_examples.csv')
selection = load_data('topic_model_selection.csv')
with st.expander('Actual model comparison and selection rule'):
    st.dataframe(selection, hide_index=True)
    st.caption('Coherence is exact document-cooccurrence NPMI on top 10 terms, not sliding-window c_npmi. Rule: maximum mean coherence with diversity ≥0.7 and stability ≥0.6; otherwise best coherence. Twelve candidates, three seeds each.')
meta = prepost.merge(labels, on='topic', validate='one_to_one').sort_values('change', ascending=False)
name_map = labels.set_index('topic').final_name.to_dict()
selected_topic = st.selectbox('Select Focus Topic:', meta.topic.tolist(), format_func=lambda t:f'Topic {t}: {name_map[t]}', key='topic_selector')
r = meta.loc[meta.topic.eq(selected_topic)].iloc[0]
o = outcomes.loc[outcomes.topic.eq(selected_topic)].iloc[0]
st.caption('Pre/post metrics always compare 2019-01–2022-10 with 2023-01–2026-08, excluding transition. The monthly chart follows the selected window. Study tags overlap; shares are computed within each tag, never by summing tags.')
if bool(r.get('mixed', False)):
    st.warning('Automatic term rules flag this topic as mixed. Treat the description as provisional and exclude it from strong thematic recommendations.')
c = st.columns(4)
c[0].metric('Pre share', f'{r.pre_share:.2%}')
c[1].metric('Post share', f'{r.post_share:.2%}')
c[2].metric('Absolute share shift', f'{r.change*100:+.2f} pp', help=f'95% CI [{r.lower95*100:+.2f}, {r.upper95*100:+.2f}] pp')
c[3].metric('7-day resolved rate', f'{o.resolved_rate_7d:.1%}' if pd.notna(o.resolved_rate_7d) else 'Insufficient data')
col1,col2 = st.columns(2)
with col1:
    t = terms.query('topic == @selected_topic').sort_values('rank').head(15)
    fig=go.Figure(go.Bar(x=t.weight,y=t.term,orientation='h',marker_color='#1D4E89'))
    fig.update_layout(title='Top 15 characteristic terms',yaxis_autorange='reversed',xaxis_title='Model component weight',height=450)
    render_chart(fig,width='stretch')
with col2:
    m=filter_observations(monthly, 'month', filters, monthly=True, tags=[selected_tag]).query('topic == @selected_topic').sort_values('month')
    fig=go.Figure(go.Scatter(x=m.month,y=m.weighted_share*100,mode='lines+markers',name=selected_tag))
    fig.update_layout(title=f'{selected_tag}: monthly weighted topic share',yaxis_title='Within-tag share (%)',xaxis_title='Month',height=450)
    render_chart(fig,width='stretch')
    st.caption('Zero-vocabulary questions have zero topic weights; no topic is assigned to them. Low-sample months are flagged in the downloadable table.')
    st.dataframe(m,hide_index=True)
st.subheader('All Topics: Absolute Pre/Post Share Change with 95% Intervals')
f = meta.sort_values('change')
fig=go.Figure(go.Bar(x=f.change*100,y=[f'T{r.topic}: {r.final_name}' for r in f.itertuples()],orientation='h',error_x=dict(type='data',symmetric=False,array=((f.upper95-f.change)*100).clip(lower=0),arrayminus=((f.change-f.lower95)*100).clip(lower=0)),marker_color=['#059669' if x>0 else '#DC2626' for x in f.change]))
fig.update_layout(xaxis_title='Absolute change (percentage points)',height=max(440,30*len(f)))
render_chart(fig,width='stretch')
st.caption('1,000 question-level bootstrap resamples, retaining sampling weights. These intervals describe absolute share differences, not relative percentage changes. Pre/post associations do not identify AI substitution.')
st.subheader('Representative Title-Only Examples — Full Corpus')
st.caption('Examples describe the global model, not the selected tag. CC BY-SA 4.0; canonical source links below.')
for r in examples.query('topic == @selected_topic').head(10).itertuples():
    st.markdown(f'- [{r.title}]({r.link})')
