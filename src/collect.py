"""src/collect.py — M1-04: Core API request function.

Provides api_get() as a drop-in replacement for the same function in
src/enrich.py (Member 2).  Same call signature:
    api_get(endpoint, params=None, n_ids=0, page=1, retries=<from config>)
Returns the parsed JSON dict on success, raises on terminal failure.

Key differences from enrich.py api_get
---------------------------------------
* Settings come from config.yaml (not module-level constants).
* Raw files are named by a deterministic hash (endpoint + non-key params),
  so a re-run skips existing files.  Pass force_refresh=True to bypass.
* Caller-supplied params override config defaults (including "filter", so
  M1-06 can use filter=total for weekly counts).
* Logs 12 columns (timestamp, member, endpoint, params_summary, page,
  http_status, items, has_more, quota_remaining, backoff, retry_count,
  raw_file) to a separate-headed CSV so it never mixes with enrich.py rows.
* Retries on: network errors, HTTP 5xx, HTTP 429, and API error_id 502/503.
  Fails immediately on other 4xx error_ids (e.g. 400 bad_parameter).
* Raises QuotaExhausted when quota_remaining <= quota_floor.
* The "backoff" value from a response is stored in module state and slept
  BEFORE the next request (not after, which would waste a dead-sleep period).

Public API
----------
create_filter()              Run once to create/print the custom filter.
api_get(endpoint, params, n_ids, page, retries, force_refresh)
iter_questions(tagged, fromdate, todate, **extra)   Paging generator.
"""

from __future__ import annotations

import csv
import hashlib
import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

import requests
import yaml
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

load_dotenv()

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
_CONFIG_PATH = _ROOT / "config.yaml"

with open(_CONFIG_PATH) as _fh:
    _CFG = yaml.safe_load(_fh)

_API_CFG   = _CFG["api"]
_BASE_URL  = _API_CFG["base_url"].rstrip("/")
_SITE      = _API_CFG["site"]
_PAGE_SIZE = _API_CFG["page_size"]
_MIN_DELAY = _API_CFG["min_delay_s"]
_MAX_RETRY = _API_CFG["max_retries"]
_Q_FLOOR   = _API_CFG["quota_floor"]
_FILTER    = _API_CFG["filter"]

_RAW_DIR  = _ROOT / _CFG["paths"]["raw_dir"]
_LOG_PATH = _ROOT / _CFG["paths"]["log"]

_LOG_FIELDS = [
    "timestamp_utc", "member", "endpoint", "params_summary",
    "page", "http_status", "items", "has_more",
    "quota_remaining", "backoff", "retry_count", "raw_file",
]
_LOG_HEADER_SENTINEL = ",".join(_LOG_FIELDS)

# Module-level backoff state: seconds to sleep BEFORE the next request.
_pending_backoff: float = 0.0

_RETRY_API_ERRORS = {502, 503}   # throttle_violation, temporarily_unavailable

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class QuotaExhausted(RuntimeError):
    """Raised when quota_remaining falls to or below quota_floor."""


class ClientError(RuntimeError):
    """Raised on unrecoverable 4xx / bad-parameter API errors."""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _api_key() -> str:
    key = os.getenv("STACK_API_KEY", "")
    if not key or key == "your_key_here":
        raise RuntimeError("STACK_API_KEY not set. Copy .env.example to .env.")
    return key


def _raw_filename(endpoint: str, params: dict) -> Path:
    """Deterministic filename: SHA-1 of (endpoint + sorted non-key params)."""
    safe = {k: v for k, v in sorted(params.items()) if k != "key"}
    blob = json.dumps({"endpoint": endpoint, "params": safe}, sort_keys=True)
    digest = hashlib.sha1(blob.encode()).hexdigest()[:16]
    # Make endpoint path-safe
    safe_ep = endpoint.replace("/", "_").replace(";", "_")[:60]
    return _RAW_DIR / f"{safe_ep}__{digest}.json"


def _params_summary(params: dict) -> str:
    """Compact representation of params, key excluded."""
    return json.dumps(
        {k: v for k, v in sorted(params.items()) if k != "key"},
        separators=(",", ":"),
    )


def _format_raw_path(path: Path) -> str:
    try:
        return str(path.relative_to(_ROOT))
    except ValueError:
        return str(path)


def _write_log(row: dict) -> None:
    _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if _LOG_PATH.exists() and _LOG_PATH.stat().st_size > 0:
        # Check header compatibility
        with open(_LOG_PATH, newline="", encoding="utf-8") as fh:
            existing_header = fh.readline().strip()
        if existing_header != _LOG_HEADER_SENTINEL:
            alt = _LOG_PATH.with_stem(_LOG_PATH.stem + "_m1")
            logger.warning(
                "logs/collection_log.csv has a different header (%s). "
                "Writing M1 rows to %s instead.",
                existing_header,
                alt,
            )
            _write_log_to(_LOG_FIELDS, row, alt)
            return
    _write_log_to(_LOG_FIELDS, row, _LOG_PATH)


def _write_log_to(fields: list, row: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    new_file = not path.exists() or path.stat().st_size == 0
    with open(path, "a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        if new_file:
            w.writeheader()
        w.writerow(row)


def _strip_key_from_data(data: dict) -> dict:
    """Return a copy of data with any 'key' entry removed (defensive clean)."""
    return {k: v for k, v in data.items() if k != "key"}


# ---------------------------------------------------------------------------
# Public: create_filter (run once)
# ---------------------------------------------------------------------------

def create_filter() -> str:
    """Call /filters/create once, print and return the filter string.

    The filter adds question.body to the default filter, which already
    includes all wrapper fields (items, has_more, backoff, quota_max,
    quota_remaining).  Run this once, then paste the printed string into
    config.yaml under api.filter.
    """
    r = requests.get(
        f"{_BASE_URL}/filters/create",
        params={"include": "question.body", "base": "default", "key": _api_key()},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    f = data["items"][0]["filter"]
    print(f"Filter string (paste into config.yaml > api.filter): {f}")
    return f


# ---------------------------------------------------------------------------
# Public: api_get
# ---------------------------------------------------------------------------

def api_get(
    endpoint: str,
    params: dict | None = None,
    n_ids: int = 0,
    page: int = 1,
    retries: int | None = None,
    force_refresh: bool = False,
) -> dict:
    """Make one GET to the Stack Exchange API.

    Parameters
    ----------
    endpoint    : Path after base URL, e.g. "questions" or "answers/123;456".
    params      : Caller-supplied params.  Caller values override config
                  defaults (including "filter").
    n_ids       : Number of IDs in a batched request (for logging only).
    page        : Page number (added to params; caller can override).
    retries     : Max attempts.  Defaults to config max_retries.
    force_refresh: Bypass the on-disk cache even if the raw file exists.

    Returns
    -------
    dict        : Parsed JSON response.

    Raises
    ------
    QuotaExhausted  : quota_remaining <= quota_floor.
    ClientError     : Unrecoverable 4xx (e.g. bad_parameter).
    RuntimeError    : All retries exhausted.
    """
    global _pending_backoff

    if retries is None:
        retries = _MAX_RETRY

    # Build full params: config defaults < caller overrides
    full_params: dict[str, Any] = {
        "site":     _SITE,
        "pagesize": _PAGE_SIZE,
        "filter":   _FILTER,
        "page":     page,
    }
    if params:
        full_params.update(params)  # caller overrides config defaults
    full_params["page"] = full_params.get("page", page)
    # Key added last so it is always present but never written to disk
    full_params_with_key = {**full_params, "key": _api_key()}

    raw_path = _raw_filename(endpoint, full_params)  # key excluded by _raw_filename

    # ------------------------------------------------------------------
    # Cache hit
    # ------------------------------------------------------------------
    if raw_path.exists() and not force_refresh:
        data = json.loads(raw_path.read_text(encoding="utf-8"))
        _write_log({
            "timestamp_utc":  datetime.now(timezone.utc).isoformat(),
            "member":         "M1",
            "endpoint":       endpoint,
            "params_summary": _params_summary(full_params),
            "page":           full_params.get("page", page),
            "http_status":    "CACHED",
            "items":          len(data.get("items", [])),
            "has_more":       data.get("has_more", ""),
            "quota_remaining": data.get("quota_remaining", ""),
            "backoff":        data.get("backoff", ""),
            "retry_count":    0,
            "raw_file":       _format_raw_path(raw_path),
        })
        return data

    # ------------------------------------------------------------------
    # Network calls with retry
    # ------------------------------------------------------------------
    attempt = 0
    last_exc: Exception | None = None

    while attempt < retries:
        # Honour backoff from previous response BEFORE sleeping min_delay
        if _pending_backoff > 0:
            time.sleep(_pending_backoff)
            _pending_backoff = 0.0

        time.sleep(_MIN_DELAY)

        stamp = datetime.now(timezone.utc)
        status: int | None = None
        data: dict = {}
        retry_count = attempt

        try:
            resp = requests.get(
                f"{_BASE_URL}/{endpoint}",
                params=full_params_with_key,
                timeout=30,
            )
            status = resp.status_code
            try:
                data = resp.json()
            except ValueError:
                data = {}
        except requests.RequestException as exc:
            last_exc = exc
            wait = _MIN_DELAY * (2 ** attempt)
            logger.warning("Network error attempt %d: %s — retrying in %.1fs", attempt + 1, exc, wait)
            _write_log({
                "timestamp_utc":  stamp.isoformat(),
                "member":         "M1",
                "endpoint":       endpoint,
                "params_summary": _params_summary(full_params),
                "page":           full_params.get("page", page),
                "http_status":    "NETWORK_ERR",
                "items":          0,
                "has_more":       "",
                "quota_remaining": "",
                "backoff":        "",
                "retry_count":    retry_count,
                "raw_file":       "",
            })
            attempt += 1
            time.sleep(wait)
            continue

        # ------------------------------------------------------------------
        # Classify the response
        # ------------------------------------------------------------------
        api_error_id  = data.get("error_id")
        quota_rem     = data.get("quota_remaining")
        backoff_val   = data.get("backoff", 0)
        items_cnt     = len(data.get("items", []))
        has_more      = data.get("has_more", False)

        # Store backoff for the NEXT request
        if backoff_val:
            _pending_backoff = float(backoff_val)

        should_retry = (
            status in (429, 502, 503, 504)
            or (status is not None and 500 <= status < 600)
            or api_error_id in _RETRY_API_ERRORS
        )
        is_client_err = (
            (status is not None and 400 <= status < 500 and not should_retry)
            or (api_error_id is not None and api_error_id not in _RETRY_API_ERRORS)
        )

        if is_client_err:
            msg = (
                f"Client error {status} on {endpoint}: "
                f"{data.get('error_name','?')} — {data.get('error_message','?')}"
            )
            _write_log({
                "timestamp_utc":  stamp.isoformat(),
                "member":         "M1",
                "endpoint":       endpoint,
                "params_summary": _params_summary(full_params),
                "page":           full_params.get("page", page),
                "http_status":    status,
                "items":          0,
                "has_more":       "",
                "quota_remaining": quota_rem,
                "backoff":        backoff_val,
                "retry_count":    retry_count,
                "raw_file":       "",
            })
            raise ClientError(msg)

        if status == 200 and api_error_id not in _RETRY_API_ERRORS:
            # Success path
            _RAW_DIR.mkdir(parents=True, exist_ok=True)
            clean_data = _strip_key_from_data(data)
            raw_path.write_text(json.dumps(clean_data), encoding="utf-8")

            _write_log({
                "timestamp_utc":  stamp.isoformat(),
                "member":         "M1",
                "endpoint":       endpoint,
                "params_summary": _params_summary(full_params),
                "page":           full_params.get("page", page),
                "http_status":    status,
                "items":          items_cnt,
                "has_more":       has_more,
                "quota_remaining": quota_rem,
                "backoff":        backoff_val,
                "retry_count":    retry_count,
                "raw_file":       _format_raw_path(raw_path),
            })

            # Quota guard AFTER logging so the log row is always written
            if quota_rem is not None and quota_rem <= _Q_FLOOR:
                raise QuotaExhausted(
                    f"quota_remaining={quota_rem} is at or below floor={_Q_FLOOR}."
                )

            return clean_data

        # Retriable failure
        wait = _MIN_DELAY * (2 ** attempt)
        logger.warning(
            "Retriable error status=%s error_id=%s attempt %d — retrying in %.1fs",
            status, api_error_id, attempt + 1, wait,
        )
        _write_log({
            "timestamp_utc":  stamp.isoformat(),
            "member":         "M1",
            "endpoint":       endpoint,
            "params_summary": _params_summary(full_params),
            "page":           full_params.get("page", page),
            "http_status":    status,
            "items":          items_cnt,
            "has_more":       "",
            "quota_remaining": quota_rem,
            "backoff":        backoff_val,
            "retry_count":    retry_count,
            "raw_file":       "",
        })
        attempt += 1
        time.sleep(wait)

    raise RuntimeError(
        f"api_get: all {retries} attempts failed for endpoint={endpoint!r}. "
        f"Last exception: {last_exc}"
    )


# ---------------------------------------------------------------------------
# Public: iter_questions — paging helper for /questions
# ---------------------------------------------------------------------------

def iter_questions(
    tagged: str,
    fromdate: int,
    todate: int,
    **extra,
) -> Iterator[dict]:
    """Yield question dicts for one tag over a date window, all pages.

    Each item includes: question_id, accepted_answer_id,
    owner_user_id (flattened from owner.user_id), answer_count,
    creation_date, tags, title, body, score, view_count.

    Parameters
    ----------
    tagged   : Tag string, e.g. "python".
    fromdate : UTC epoch start (inclusive).
    todate   : UTC epoch end (exclusive).
    **extra  : Any extra params forwarded to api_get (e.g. filter="total").
    """
    params: dict[str, Any] = {
        "tagged":   tagged,
        "fromdate": fromdate,
        "todate":   todate,
        "sort":     "creation",
        "order":    "asc",
        **extra,
    }
    page = 1
    while True:
        data = api_get("questions", params=params, page=page)
        for item in data.get("items", []):
            # Flatten owner.user_id
            owner = item.pop("owner", {}) or {}
            item["owner_user_id"] = owner.get("user_id")
            yield item
        if not data.get("has_more"):
            break
        page += 1
