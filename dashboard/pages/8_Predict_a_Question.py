"""Real inference through the versioned fitted classifier and preprocessor."""
import sys
from pathlib import Path
from datetime import date
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import streamlit as st
import pandas as pd
import plotly.express as px
from src.predict import load_bundle, question_frame, infer, explain, MODEL_DIR
from dashboard.common import load_data, render_chart

st.set_page_config(page_title='Predict a Question',page_icon='🎯',layout='wide')
st.title('Predict a Question')
st.write('Enter a question to run the fitted XGBoost model. This is a historical demonstration using the data available through August 2026.')

@st.cache_resource
def fitted_model(modified):
    return load_bundle()

if not (MODEL_DIR/'pipeline.joblib').exists():
    st.error('The fitted model is missing. Follow the model setup instructions in the README.');st.stop()
bundle,metadata=fitted_model((MODEL_DIR/'pipeline.joblib').stat().st_mtime_ns)
st.caption(metadata['target'])
with st.form('prediction_form'):
    title=st.text_input('Question title',value='How can I merge two pandas DataFrames on a shared key?',max_chars=500)
    prose=st.text_area('Question prose',value='I have two data frames with a shared identifier. I want to keep all rows from the first frame and attach matching values from the second. What is the correct merge operation?',height=120)
    code=st.text_area('Code or error output (optional)',value="result = left.merge(right, on='id', how='left')",height=90)
    tags=st.multiselect('Technology tags',metadata['study_tags'],default=['python','pandas'])
    c1,c2,c3=st.columns(3)
    posted=c1.date_input('Historical posting date',value=date(2026,8,15),min_value=date(2019,2,26),max_value=date(2026,8,31))
    hour=c2.number_input('Posting hour (UTC)',0,23,12)
    age=c3.number_input('Account age in days',0,20000,365)
    unknown=st.checkbox('Account age unknown')
    submit=st.form_submit_button('Predict',type='primary')
if submit:
    try:
        q=question_frame(title,prose,code,tags,pd.Timestamp(posted,tz='UTC')+pd.Timedelta(hours=hour),None if unknown else age)
        features,raw,p=infer(bundle,metadata,q,load_data('series_long.csv'))
        local=explain(bundle,metadata,features)
        st.session_state['last_prediction']={'probability':float(p[0]),'raw':float(raw[0]),'explanation':local,'features':features.drop(columns=['title','tags'],errors='ignore')}
    except ValueError as e:
        st.error(str(e));st.session_state.pop('last_prediction',None)
result=st.session_state.get('last_prediction')
if result:
    st.caption('Result from the last submitted form. Submit again after changing an input.')
    a,b,c=st.columns(3)
    a.metric('Estimated proxy-positive probability',f"{result['probability']:.1%}")
    b.metric('Validation-selected threshold',f"{metadata['threshold']:.1%}")
    c.metric('Classification','Proxy positive' if result['probability']>=metadata['threshold'] else 'Proxy negative')
    st.warning('This is an uncertain statistical estimate. It does not guarantee an answer, acceptance or satisfaction. The additional August evaluation has only 389 questions; calibration can drift.')
    render_chart(px.bar(result['explanation'].sort_values('contribution'),x='contribution',y='feature',orientation='h',title='Contributions to this prediction'),width='stretch')
    st.caption('Tree SHAP contributions affect the raw model margin before calibration. Title SVD components are latent text features. These associations do not estimate the benefit of editing a question.')
    with st.expander('Computed features and model version'):
        st.dataframe(result['features'],hide_index=True)
        st.json({k:metadata[k] for k in ['version','training_end_exclusive','calibration_period','threshold_period','evaluation_period']})
st.page_link('pages/7_Dataset_and_Classification.py',label='Inspect model evaluation and limitations')
