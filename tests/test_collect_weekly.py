import unittest
from unittest.mock import patch, MagicMock
from datetime import date
import pandas as pd
from pathlib import Path

from src.collect_weekly import generate_weekly_windows, save_records, collect_weekly_counts


class TestCollectWeekly(unittest.TestCase):
    def test_generate_weekly_windows(self):
        windows = generate_weekly_windows("2019-01-01", "2026-08-31")
        self.assertEqual(len(windows), 400)
        self.assertEqual(windows[0][0], date(2019, 1, 1))
        self.assertEqual(windows[0][1], date(2019, 1, 7))
        self.assertEqual(windows[-1][0], date(2026, 8, 25))
        self.assertEqual(windows[-1][1], date(2026, 8, 31))

        # Ensure no gaps between consecutive windows
        for i in range(len(windows) - 1):
            curr_end = windows[i][1]
            next_start = windows[i + 1][0]
            self.assertEqual((next_start - curr_end).days, 1)

    @patch("src.collect_weekly.WEEKLY_COUNTS_PATH")
    @patch("src.collect_weekly.api_get")
    def test_collect_weekly_mocked(self, mock_api_get, mock_path):
        mock_api_get.return_value = {"total": 1234, "quota_remaining": 9000}
        tmp_csv = Path("scratch/test_weekly_tmp.csv")
        mock_path.parent.mkdir(parents=True, exist_ok=True)
        mock_path.exists.return_value = False
        mock_path.open = tmp_csv.open

        # Run with max_calls=2 to verify limited calls
        with patch("src.collect_weekly.save_records") as mock_save:
            collect_weekly_counts(["python"], max_calls=2)
            self.assertEqual(mock_api_get.call_count, 2)
            mock_save.assert_called()


if __name__ == "__main__":
    unittest.main()
