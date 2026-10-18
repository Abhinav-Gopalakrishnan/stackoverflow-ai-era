"""Headless verification tests for Streamlit dashboard pages (M1-22 / M1-24).

Tests each page with several filter combinations: default, one tag,
post period only, and log scale. Asserts 0 exceptions and render < 5 s.
"""

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
    ("Dataset & Classification", ROOT / "dashboard" / "pages" / "7_Dataset_and_Classification.py"),
]

# Filter combinations: (description, session_state overrides)
FILTER_COMBOS = [
    ("default", {}),
    ("one_tag_python", {"selected_tags": ["python"]}),
    ("post_period_only", {"period": "post"}),
    ("log_scale", {"log_scale": True}),
]


@pytest.mark.parametrize("page_name,page_path", PAGES)
@pytest.mark.parametrize(
    "combo_name,state_overrides",
    FILTER_COMBOS,
    ids=[c[0] for c in FILTER_COMBOS],
)
def test_dashboard_page_render_with_filters(
    page_name, page_path, combo_name, state_overrides
):
    """Assert each page renders without exception under 5 s for each filter combo."""
    assert page_path.exists(), f"Page file missing: {page_path}"

    start_time = time.perf_counter()
    at = AppTest.from_file(str(page_path))

    # Inject session_state overrides before running
    for key, value in state_overrides.items():
        at.session_state[key] = value

    at.run(timeout=10)
    elapsed = time.perf_counter() - start_time

    assert not at.exception, (
        f"Render exception in {page_name} [{combo_name}]: {at.exception}"
    )
    assert elapsed < 5.0, (
        f"Page {page_name} [{combo_name}] took {elapsed:.2f}s, exceeding 5s limit"
    )
