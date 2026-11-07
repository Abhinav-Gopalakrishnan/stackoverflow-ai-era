from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest


@pytest.fixture
def app_page():
    """Exercise the registered navigation, just as a browser session does."""
    root = Path(__file__).resolve().parents[1] / "dashboard"

    def open_page(page="app.py", state=None):
        at = AppTest.from_file(str(root / "app.py"))
        for key, value in (state or {}).items():
            at.session_state[key] = value
        at.run(timeout=30)
        if page != "app.py":
            at.switch_page(page).run(timeout=30)
        return at

    return open_page
