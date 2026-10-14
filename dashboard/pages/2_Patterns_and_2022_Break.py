"""Page 2: Patterns and 2022 Break (Stub - to be wired in M1-24)."""

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
    page_title="Page 2: Patterns & 2022 Break",
    page_icon="📈",
    layout="wide",
)

render_sidebar()

st.title("Page 2: Patterns and 2022 Break")
st.info("wired in M1-24")
st.markdown(
    """
    *Deliverables mapped to this page:*
    - STL Decomposition (`stl_components.csv`)
    - Ruptures Changepoint Detection (`changepoints.csv`)
    - Interrupted Time Series Analysis (`its_results.csv`)
    """
)
