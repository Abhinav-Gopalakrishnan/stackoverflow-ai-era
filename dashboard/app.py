"""Streamlit entry point with explicit, readable navigation."""
import streamlit as st
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
page=st.navigation([
    st.Page('overview.py',title='Overview',default=True),
    st.Page('pages/7_Dataset_and_Classification.py',title='Dataset & Classification'),
    st.Page('pages/8_Predict_a_Question.py',title='Predict a Question'),
    st.Page('pages/2_Patterns_and_2022_Break.py',title='Patterns & 2022 Break'),
    st.Page('pages/3_Forecasts.py',title='Forecasts'),
    st.Page('pages/4_Topics.py',title='Topics'),
    st.Page('pages/5_Tone_and_Complexity.py',title='Tone & Structure'),
    st.Page('pages/6_Recommendations.py',title='Actions & Scenarios'),
])
page.run()
