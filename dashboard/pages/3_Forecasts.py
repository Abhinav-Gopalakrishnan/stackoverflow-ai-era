"""Page 3: Forecasts (Stub - to be wired in M1-24)."""

import sys
from pathlib import Path
import streamlit as st

_dashboard_dir = Path(__file__).resolve().parent.parent
_repo_root = _dashboard_dir.parent
for _p in (str(_dashboard_dir), str(_repo_root)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from common import render_sidebar
except ImportError:
    from dashboard.common import render_sidebar

st.set_page_config(
    page_title="Page 3: Forecasts",
    page_icon="🔮",
    layout="wide",
)

render_sidebar()

st.title("Page 3: Forecasts")
st.info("wired in M1-24")
st.markdown(
    """
    *Deliverables mapped to this page:*
    - 26-Week Forecast Horizons with 80% and 95% CIs (`forecasts_26w.csv`)
    - Tag Trajectory Classification & Half-Life (`tag_classes.csv`)
    - Backtest Evaluation & Matched Baselines (`backtest_summary_matched.csv`, `backtest_metrics_matched.csv`)
    """
)
