"""Headless verification tests for Streamlit dashboard pages (M1-22)."""

import time
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent.parent

PAGES = [
    ("Overview", ROOT / "dashboard" / "app.py"),
    ("Patterns", ROOT / "dashboard" / "pages" / "2_Patterns_and_2022_Break.py"),
    ("Forecasts", ROOT / "dashboard" / "pages" / "3_Forecasts.py"),
    ("Topics", ROOT / "dashboard" / "pages" / "4_Topics.py"),
    ("Tone & Complexity", ROOT / "dashboard" / "pages" / "5_Tone_and_Complexity.py"),
    ("Recommendations", ROOT / "dashboard" / "pages" / "6_Recommendations.py"),
]


@pytest.mark.parametrize("page_name,page_path", PAGES)
def test_dashboard_page_render_and_timing(page_name, page_path):
    """Assert each dashboard page renders without exception in under 5 seconds."""
    assert page_path.exists(), f"Page file missing: {page_path}"

    start_time = time.perf_counter()
    at = AppTest.from_file(str(page_path))
    at.run()
    elapsed = time.perf_counter() - start_time

    assert not at.exception, f"Render exception in {page_name}: {at.exception}"
    assert elapsed < 5.0, f"Page {page_name} took {elapsed:.2f}s, exceeding 5s limit"
