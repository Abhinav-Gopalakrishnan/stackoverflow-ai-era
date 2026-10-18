"""Semantic interaction checks: controls must alter observations, not just render."""
import json
from pathlib import Path
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest
from dashboard.common import filter_observations

ROOT=Path(__file__).resolve().parents[1]


def test_intersect_period_window_and_tag():
    frame=pd.DataFrame({'tag':['python']*4+['java'],'month':['2022-10','2022-11','2022-12','2023-01','2023-01'],'x':range(5)})
    filters={'start_date':'2022-01-01','end_date':'2023-12-31','period':'post','tags':['python']}
    out=filter_observations(frame,'month',filters,monthly=True)
    assert out.x.tolist()==[3]


def charts(at): return [x.proto.spec for x in at.get('plotly_chart')]


@pytest.mark.parametrize('page', ['app.py','pages/2_Patterns_and_2022_Break.py','pages/5_Tone_and_Complexity.py','pages/4_Topics.py'])
def test_period_changes_observation_chart(page):
    at=AppTest.from_file(str(ROOT/'dashboard'/page)).run(timeout=15)
    assert not at.exception
    before=charts(at)
    at.radio(key='period_radio').set_value('post').run(timeout=15)
    assert not at.exception
    assert charts(at)!=before


def test_topic_tag_changes_prevalence():
    at=AppTest.from_file(str(ROOT/'dashboard/pages/4_Topics.py')).run(timeout=15)
    assert not at.exception
    before=charts(at)
    at.multiselect(key='tag_selector').set_value(['python']).run(timeout=15)
    assert not at.exception
    assert charts(at)!=before
    assert at.selectbox(key='page4_tag_selector').value=='python'


@pytest.mark.parametrize('page',['pages/3_Forecasts.py','pages/6_Recommendations.py'])
def test_fixed_models_disable_observation_controls(page):
    at=AppTest.from_file(str(ROOT/'dashboard'/page)).run(timeout=15)
    assert not at.exception
    assert at.radio(key='period_radio').disabled
    assert at.date_input(key='date_range_picker').disabled


def test_dataset_classifier_page_has_locked_results():
    at=AppTest.from_file(str(ROOT/'dashboard/pages/7_Dataset_and_Classification.py')).run(timeout=15)
    assert not at.exception
    assert any('0.4315' in m.value for m in at.metric)
