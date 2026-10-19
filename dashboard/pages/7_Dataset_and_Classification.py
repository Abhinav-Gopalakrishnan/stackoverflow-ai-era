"""Units 1 and 2 evidence from saved, locked results; no inference UI."""
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from common import render_chart, load_data
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
st.markdown('Logistic regression, random forest and XGBoost are compared with a majority baseline. Train is before 2025, validation is January–June 2025 and locked test is July 2025–July 2026. August 2026 is only in the later Unit 3 analyses. Training-only preprocessing prevents future information entering earlier predictions. XGBoost was selected by validation PR-AUC; the F1 threshold was also fixed using validation only.')
st.subheader('Locked Test Results — XGBoost')
t=load_data('classifier_test.csv').iloc[0]
c=st.columns(4)
c[0].metric('Test PR-AUC',f'{t.pr_auc:.4f}')
c[1].metric('Test ROC-AUC',f'{t.roc_auc:.4f}')
c[2].metric('Test F1',f'{t.f1:.4f}')
c[3].metric('Test questions',f'{int(t.n):,}')
st.dataframe(load_data('classifier_test.csv'),hide_index=True)
st.warning('Primary-target performance is modest. PR-AUC, F1 and ROC-AUC are different measures; none is “accuracy”. The secondary any-answer target is easier and must not replace the primary accepted-answer result. Drift and narrow feature information limit generalisation.')
