"""tests/test_collect.py — Unit tests for M1-04 src/collect.py.

Uses mocks only — no live network calls to the Stack Exchange API.
Run with: python -m unittest tests/test_collect.py
"""

import csv
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, call, patch

# Ensure src can be imported
import sys
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src import collect


class TestCollectApiGet(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.raw_dir = Path(self.temp_dir) / "raw"
        self.log_file = Path(self.temp_dir) / "collection_log.csv"
        
        # Patch paths in collect module
        self.orig_raw_dir = collect._RAW_DIR
        self.orig_log_path = collect._LOG_PATH
        collect._RAW_DIR = self.raw_dir
        collect._LOG_PATH = self.log_file
        collect._pending_backoff = 0.0

    def tearDown(self):
        collect._RAW_DIR = self.orig_raw_dir
        collect._LOG_PATH = self.orig_log_path
        collect._pending_backoff = 0.0
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("src.collect.requests.get")
    @patch("src.collect.time.sleep")
    def test_forced_error_retry(self, mock_sleep, mock_get):
        """First two responses 502, third succeeds.
        Assert 3 attempts, 2 retries, exponential sleep, and correct log rows with retry_count.
        """
        resp_502_1 = MagicMock()
        resp_502_1.status_code = 502
        resp_502_1.json.return_value = {"error_id": 502, "error_name": "throttle_violation"}

        resp_502_2 = MagicMock()
        resp_502_2.status_code = 502
        resp_502_2.json.return_value = {"error_id": 502, "error_name": "throttle_violation"}

        resp_200 = MagicMock()
        resp_200.status_code = 200
        resp_200.json.return_value = {
            "items": [{"question_id": 12345, "title": "Test Question"}],
            "has_more": False,
            "quota_max": 10000,
            "quota_remaining": 9990
        }

        mock_get.side_effect = [resp_502_1, resp_502_2, resp_200]

        res = collect.api_get("questions", params={"tagged": "python"})

        self.assertEqual(mock_get.call_count, 3)
        self.assertEqual(len(res["items"]), 1)
        self.assertEqual(res["items"][0]["question_id"], 12345)

        # Check sleep calls: min_delay sleeps and retry wait sleeps
        # min_delay is 0.5; retry 0 wait is 0.5 * 1 = 0.5; retry 1 wait is 0.5 * 2 = 1.0
        sleep_args = [arg[0][0] for arg in mock_sleep.call_args_list]
        self.assertIn(0.5, sleep_args)
        self.assertIn(1.0, sleep_args)

        # Check log file
        self.assertTrue(self.log_file.exists())
        with open(self.log_file, newline="", encoding="utf-8") as fh:
            reader = list(csv.DictReader(fh))
        self.assertEqual(len(reader), 3)
        self.assertEqual([r["retry_count"] for r in reader], ["0", "1", "2"])
        self.assertEqual([r["http_status"] for r in reader], ["502", "502", "200"])
        self.assertEqual(reader[2]["items"], "1")

    @patch("src.collect.requests.get")
    @patch("src.collect.time.sleep")
    def test_backoff_honoured_before_next_call(self, mock_sleep, mock_get):
        """The backoff field in response 1 must be slept BEFORE request 2 is sent."""
        resp1 = MagicMock()
        resp1.status_code = 200
        resp1.json.return_value = {
            "items": [{"question_id": 1}],
            "backoff": 15,
            "quota_remaining": 9000
        }

        resp2 = MagicMock()
        resp2.status_code = 200
        resp2.json.return_value = {
            "items": [{"question_id": 2}],
            "quota_remaining": 8999
        }

        mock_get.side_effect = [resp1, resp2]

        call_events = []
        def sleep_recorder(secs):
            call_events.append(("sleep", secs))
        mock_sleep.side_effect = sleep_recorder

        def get_recorder(url, **kwargs):
            call_events.append(("get", kwargs.get("params", {}).get("page")))
            return resp1 if len([e for e in call_events if e[0] == "get"]) == 1 else resp2
        mock_get.side_effect = get_recorder

        # First call receives backoff=15
        collect.api_get("questions", params={"tagged": "python"}, page=1)
        self.assertEqual(collect._pending_backoff, 15.0)

        # Second call should sleep 15 BEFORE making the GET request
        collect.api_get("questions", params={"tagged": "python"}, page=2)
        self.assertEqual(collect._pending_backoff, 0.0)

        # Find the index of the second GET
        get_indices = [i for i, event in enumerate(call_events) if event[0] == "get"]
        self.assertEqual(len(get_indices), 2)
        second_get_idx = get_indices[1]

        # Ensure that ("sleep", 15.0) occurred before the second GET
        sleep_15_events = [
            i for i, event in enumerate(call_events)
            if event[0] == "sleep" and event[1] == 15.0
        ]
        self.assertTrue(len(sleep_15_events) >= 1)
        self.assertLess(sleep_15_events[0], second_get_idx)

    @patch("src.collect.requests.get")
    @patch("src.collect.time.sleep")
    def test_rerun_skips_existing_raw_file(self, mock_sleep, mock_get):
        """Cached files are re-used without making an HTTP request, unless force_refresh=True."""
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {
            "items": [{"question_id": 999}],
            "quota_remaining": 9990
        }
        mock_get.return_value = resp

        # Call 1: fetches from network and writes raw file
        data1 = collect.api_get("questions", params={"tagged": "fastapi"})
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(data1["items"][0]["question_id"], 999)

        # Call 2: file exists -> CACHED, network not called
        data2 = collect.api_get("questions", params={"tagged": "fastapi"})
        self.assertEqual(mock_get.call_count, 1) # Still 1
        self.assertEqual(data2["items"][0]["question_id"], 999)

        # Call 3: force_refresh=True -> bypasses cache and calls network
        data3 = collect.api_get("questions", params={"tagged": "fastapi"}, force_refresh=True)
        self.assertEqual(mock_get.call_count, 2)
        self.assertEqual(data3["items"][0]["question_id"], 999)

        # Check log file has CACHED entry
        with open(self.log_file, newline="", encoding="utf-8") as fh:
            reader = list(csv.DictReader(fh))
        self.assertEqual([r["http_status"] for r in reader], ["200", "CACHED", "200"])

    @patch("src.collect.requests.get")
    @patch("src.collect.time.sleep")
    def test_api_key_never_in_log_or_raw_json(self, mock_sleep, mock_get):
        """API key must not appear in any log row or raw JSON file."""
        fake_key = os.getenv("STACK_API_KEY", "test_secret_key_12345")

        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {
            "items": [{"question_id": 555}],
            "quota_remaining": 9900
        }
        mock_get.return_value = resp

        collect.api_get("questions", params={"tagged": "python"})

        # Check raw JSON files
        raw_files = list(self.raw_dir.glob("*.json"))
        self.assertGreater(len(raw_files), 0)
        for rf in raw_files:
            content = rf.read_text(encoding="utf-8")
            self.assertNotIn(fake_key, content)
            self.assertNotIn('"key"', content)

        # Check CSV log file
        log_content = self.log_file.read_text(encoding="utf-8")
        self.assertNotIn(fake_key, log_content)

    @patch("src.collect.requests.get")
    @patch("src.collect.time.sleep")
    def test_caller_supplied_filter_overrides_config(self, mock_sleep, mock_get):
        """Caller params like filter='total' must override the config filter."""
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"total": 42000, "quota_remaining": 9900}
        mock_get.return_value = resp

        collect.api_get("questions", params={"tagged": "python", "filter": "total"})

        sent_params = mock_get.call_args[1]["params"]
        self.assertEqual(sent_params["filter"], "total")
        self.assertNotEqual(sent_params["filter"], collect._FILTER)

    def test_page_1_and_page_2_different_raw_files(self):
        """Page 1 and page 2 of same query map to different deterministic filenames."""
        p1 = {"site": "stackoverflow", "pagesize": 100, "filter": "default", "page": 1, "tagged": "python"}
        p2 = {"site": "stackoverflow", "pagesize": 100, "filter": "default", "page": 2, "tagged": "python"}

        file1 = collect._raw_filename("questions", p1)
        file2 = collect._raw_filename("questions", p2)

        self.assertNotEqual(file1.name, file2.name)

    @patch("src.collect.requests.get")
    @patch("src.collect.time.sleep")
    def test_client_error_no_retry(self, mock_sleep, mock_get):
        """400 bad_parameter must raise ClientError immediately without retrying."""
        resp = MagicMock()
        resp.status_code = 400
        resp.json.return_value = {
            "error_id": 400,
            "error_name": "bad_parameter",
            "error_message": "`fromdate` must be less than `todate`"
        }
        mock_get.return_value = resp

        with self.assertRaises(collect.ClientError) as ctx:
            collect.api_get("questions", params={"fromdate": 200, "todate": 100})

        self.assertEqual(mock_get.call_count, 1)
        self.assertIn("bad_parameter", str(ctx.exception))

    @patch("src.collect.requests.get")
    @patch("src.collect.time.sleep")
    def test_log_and_raw_filename_contains_no_id_lists(self, mock_sleep, mock_get):
        """Endpoints with ID lists must be masked in log endpoint, params_summary, and file names."""
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {
            "items": [{"user_id": 12345, "creation_date": 1600000000}],
            "quota_remaining": 9900
        }
        mock_get.return_value = resp

        # Call with user ID batch
        collect.api_get("users/12345;67890")

        # 1. Check collection_log.csv
        with open(self.log_file, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["endpoint"], "users/{ids}")
        self.assertNotIn("12345", row["endpoint"])
        self.assertNotIn("67890", row["endpoint"])
        self.assertIn('"n_ids":2', row["params_summary"])
        self.assertNotIn("12345", row["params_summary"])
        self.assertNotIn("12345", row["raw_file"])
        self.assertIn("users_n2__", row["raw_file"])

        # 2. Check on-disk raw file name
        raw_files = list(self.raw_dir.glob("*.json"))
        self.assertEqual(len(raw_files), 1)
        self.assertTrue(raw_files[0].name.startswith("users_n2__"))
        self.assertNotIn("12345", raw_files[0].name)

    @patch("src.collect.requests.get")
    @patch("src.collect.time.sleep")
    def test_right_filter_chosen_per_endpoint(self, mock_sleep, mock_get):
        """api_get must pick the minimal filter matching the endpoint prefix unless overridden."""
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"items": [], "quota_remaining": 9900}
        mock_get.return_value = resp

        # Questions
        collect.api_get("questions")
        p_q = mock_get.call_args[1]["params"]
        self.assertEqual(p_q["filter"], collect._ENDPOINT_FILTERS["questions"])

        # Answers
        collect.api_get("answers/11227902")
        p_a = mock_get.call_args[1]["params"]
        self.assertEqual(p_a["filter"], collect._ENDPOINT_FILTERS["answers"])

        # Users
        collect.api_get("users/12345;67890")
        p_u = mock_get.call_args[1]["params"]
        self.assertEqual(p_u["filter"], collect._ENDPOINT_FILTERS["users"])

    @patch("src.collect.requests.get")
    @patch("src.collect.time.sleep")
    def test_caller_filter_overrides_endpoint_filter(self, mock_sleep, mock_get):
        """Caller-supplied filter (e.g. filter='total') must override per-endpoint defaults."""
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"total": 500, "quota_remaining": 9900}
        mock_get.return_value = resp

        collect.api_get("users/12345", params={"filter": "total"})
        sent_params = mock_get.call_args[1]["params"]
        self.assertEqual(sent_params["filter"], "total")

    def test_committed_log_never_contains_users_followed_by_digits(self):
        """The committed logs/collection_log.csv must never contain users/ followed by digits."""
        real_log_path = collect._ROOT / "logs" / "collection_log.csv"
        if not real_log_path.exists():
            return
        import re
        content = real_log_path.read_text(encoding="utf-8")
        matches = re.findall(r"users/\d+", content)
        self.assertEqual(
            matches,
            [],
            f"Found forbidden endpoint patterns in committed log: {matches}"
        )


if __name__ == "__main__":
    unittest.main()

