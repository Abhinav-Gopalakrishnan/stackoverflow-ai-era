"""Original locked results and a separate evaluation of the fitted v2 model."""
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st
_repo_root = Path(__file__).resolve().parents[2]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))
from dashboard.common import render_chart, load_data
st.set_page_config(page_title='Dataset & Classification',page_icon='📚',layout='wide')
st.title('Dataset & Predictive Modelling — Units 1 and 2')
st.caption('This page displays the final-data preview and saved evaluation results. No model is retrained or retuned on the locked test set.')
v=load_data('dataset_validation.csv').iloc[0]
c=st.columns(3)
c[0].metric('Cleaned questions',f'{int(v.rows):,}')
c[1].metric('Columns',str(int(v['columns'])))
c[2].metric('Validation checks','All passed' if v.all_passed else 'Failed')
st.markdown('Stack Exchange API collection, 2019–August 2026; 13 study tags plus the ALL aggregate. Unequal historic sampling weights range from 1 to 23. The primary resolution proxy is whether the answer accepted in the collected record was posted within 168 hours of the question. Its creation time is available; the time the asker clicked Accept is not. This does not establish acceptance within seven days or asker satisfaction.')
st.subheader('Final Dataset Sample — Title and Source Links Only')
sample=load_data('final_dataset_sample.csv')
st.dataframe(sample,hide_index=True,column_config={'link':st.column_config.LinkColumn('Source')})
st.download_button('Download dataset preview',sample.to_csv(index=False),'final_dataset_sample.csv')
with st.expander('Full dataset schema and missingness'):
    st.dataframe(load_data('dataset_schema.csv'),hide_index=True)
    st.caption('The 302 MiB cleaned parquet is supplied separately; the public app deliberately contains only a small sanitized preview. Full source definitions are in docs/data_dictionary.md.')
st.subheader('Validation Comparison — Seven-Day Resolution Proxy')
comparison=load_data('classifier_validation.csv')
metric=st.selectbox('Comparison metric',['pr_auc','roc_auc','f1','precision','recall'])
render_chart(px.bar(comparison,x='model',y=metric,color='model',title=f'Validation {metric} (28,132 questions)'),width='stretch')
st.dataframe(comparison,hide_index=True)
st.markdown('The original logistic regression, random forest and XGBoost models are compared with a majority baseline. Training was before 2025, validation January–June 2025 and locked test July 2025–July 2026. XGBoost and its F1 threshold were selected using validation only. Version 2 below corrects missing-age imputation and separates calibration from threshold selection. Neither version can reconstruct original posting-time text from later snapshots.')
st.subheader('Locked Test Results — XGBoost')
t=load_data('classifier_test.csv').iloc[0]
c=st.columns(4)
c[0].metric('Test PR-AUC',f'{t.pr_auc:.4f}')
c[1].metric('Test ROC-AUC',f'{t.roc_auc:.4f}')
c[2].metric('Test F1',f'{t.f1:.4f}')
c[3].metric('Test questions',f'{int(t.n):,}')
st.dataframe(load_data('classifier_test.csv'),hide_index=True)
st.warning('Primary-target performance is modest. PR-AUC, F1 and ROC-AUC are different measures; none is “accuracy”. The secondary any-answer target is easier and must not replace the primary accepted-answer result. Drift and narrow feature information limit generalisation.')

st.divider()
st.subheader('Version 2 — fitted model used by Predict a Question')
st.page_link('pages/8_Predict_a_Question.py',label='Run the fitted model on a question')
st.caption('The original results above are historical evidence. Version 2 uses a seven-day training purge, fold-fitted missing-value imputation, Jan–Mar 2025 calibration and April–June threshold selection. August 2026 is an additional retrospective evaluation; these questions were already explored by Unit 3.')
v2=load_data('v2_classifier_metrics.csv')
st.dataframe(v2,hide_index=True)
st.warning('Only 389 questions support the August evaluation. Collected text may contain later edits; original posting-time revisions and acceptance-event timestamps were not reconstructed. The seven-day gap cannot resolve those measurement limits.')
tabs=st.tabs(['Confusion matrix','Feature importance','Subgroups','Calibration','Review capacity'])
with tabs[0]:
    cm=load_data('v2_confusion.csv').set_index('Unnamed: 0')
    render_chart(px.imshow(cm,text_auto=True,color_continuous_scale='Blues',title='August 2026 confusion matrix'),width='stretch')
with tabs[1]:
    gain=load_data('v2_feature_gain.csv').head(15).sort_values('gain')
    render_chart(px.bar(gain,x='gain',y='feature',orientation='h',title='Version 2 XGBoost feature gain'),width='stretch')
    st.caption('Gain is a model importance measure, not a causal effect. Individual tree SHAP explanations appear on the prediction page.')
with tabs[2]:
    st.dataframe(load_data('v2_subgroups.csv'),hide_index=True)
    st.caption('Tags overlap. Small groups and different class balances can produce unstable error rates. These comparisons do not establish discriminatory treatment; sparse groups need additional observations before intervention.')
with tabs[3]:
    cal=load_data('v2_calibration.csv')
    fig=px.scatter(cal,x='predicted',y='observed',size='n',hover_data=['n'],range_x=[0,1],range_y=[0,1],title='Predicted probability versus observed proxy rate')
    fig.add_shape(type='line',x0=0,y0=0,x1=1,y1=1,line=dict(dash='dash'))
    render_chart(fig,width='stretch')
    st.caption('Calibration was fitted before evaluation. Sparse bins and temporal drift limit reliability. See Brier scores above; lower is better.')
with tabs[4]:
    capture=load_data('v2_capture.csv')
    st.dataframe(capture,hide_index=True)
    st.caption('Lowest model scores are reviewed first. Capture measures identification of proxy-negative cases; it does not measure successful interventions.')
