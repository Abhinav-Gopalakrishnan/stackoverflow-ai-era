"""Unit tests for dashboard data export (M1-23).

Ensures all exported CSV files exist, are non-empty, contain the exact required columns,
remain under the 50 MB deployment threshold, and contain no prohibited columns.
"""

from pathlib import Path
import pytest
import pandas as pd
from src.export_dashboard_data import (
    DATA_DIR,
    EXPORT_SPECS,
    FORBIDDEN_COLUMNS,
    MAX_TOTAL_SIZE_MB,
    export_all,
)


@pytest.fixture(scope="module", autouse=True)
def run_export():
    """Ensure dashboard/data/ is freshly exported before running tests."""
    export_all()


def test_all_files_exist_and_non_empty():
    """Assert every required file exists and has non-zero size and rows."""
    for filename in EXPORT_SPECS:
        path = DATA_DIR / filename
        assert path.exists(), f"Missing exported file: {filename}"
        assert path.stat().st_size > 0, f"Exported file is empty: {filename}"

        df = pd.read_csv(path)
        assert len(df) > 0, f"Exported file contains 0 rows: {filename}"


@pytest.mark.parametrize("filename,spec", list(EXPORT_SPECS.items()))
def test_exact_required_columns(filename, spec):
    """Assert every exported file has the exact required schema."""
    path = DATA_DIR / filename
    df = pd.read_csv(path)
    expected_cols = spec["columns"]
    actual_cols = list(df.columns)
    assert actual_cols == expected_cols, (
        f"{filename} column mismatch:\nExpected: {expected_cols}\nActual:   {actual_cols}"
    )


def test_total_data_size_under_limit():
    """Assert total size of exported files is strictly under 50 MB."""
    total_bytes = sum((DATA_DIR / f).stat().st_size for f in EXPORT_SPECS if (DATA_DIR / f).exists())
    total_mb = total_bytes / (1024 * 1024)
    assert total_mb < MAX_TOTAL_SIZE_MB, (
        f"Exported data size ({total_mb:.2f} MB) exceeds limit ({MAX_TOTAL_SIZE_MB} MB)"
    )


def test_no_forbidden_or_pii_columns():
    """Assert no exported file contains question bodies, plain text, code or user identifiers."""
    for filename in EXPORT_SPECS:
        path = DATA_DIR / filename
        df = pd.read_csv(path)
        col_names_lower = [c.lower() for c in df.columns]

        for forbidden in FORBIDDEN_COLUMNS:
            assert forbidden not in col_names_lower, (
                f"Security breach: forbidden column '{forbidden}' found in {filename}"
            )

        # Check for any pattern of user hash / id / body
        for col in col_names_lower:
            assert "user_hash" not in col, f"User hash column found in {filename}: {col}"
            assert "plain_body" not in col, f"Plain body column found in {filename}: {col}"
            assert "code_text" not in col, f"Code text column found in {filename}: {col}"
