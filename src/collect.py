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
* ID lists in batch endpoints (e.g. users/123;456) are MASKED in the log
  endpoint column, params_summary, and raw file names to avoid committing
  raw user IDs. The cache hash still uses the real IDs.
* Per-endpoint minimal API filters (base="none") avoid returning display
  names, profile images, or other profile metadata in raw JSON files.
  A caller-supplied "filter" param always overrides the per-endpoint default.

Public API
----------
create_filter(endpoint_type)    Run once to create/print a minimal filter.
api_get(endpoint, params, n_ids, page, retries, force_refresh)
iter_questions(tagged, fromdate, todate, **extra)   Paging generator.
"""

from __future__ import annotations

import csv
import hashlib
import json
import logging
import os
import re
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

# Per-endpoint minimal filters (base="none"). Caller-supplied filter overrides.
# Keys are the first path segment of the endpoint.
_ENDPOINT_FILTERS: dict[str, str] = {
    "questions":  _API_CFG.get("filter_questions", _FILTER),
    "answers":    _API_CFG.get("filter_answers",   _FILTER),
    "users":      _API_CFG.get("filter_users",     _FILTER),
}

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

# Pattern that detects a digit-only ID list after the first path segment.
# Examples: "users/123;456", "answers/11227902", "questions/123;456/answers"
_ID_IN_ENDPOINT_RE = re.compile(
    r"^(questions|answers|users)/(\d[\d;]*)(/answers)?$"
)

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


def _mask_endpoint(endpoint: str) -> str:
    """Replace an ID list in a batch endpoint with the placeholder {ids}.

    Examples
    --------
    "users/123;456;789"          -> "users/{ids}"
    "answers/11227902"           -> "answers/{ids}"
    "questions/123;456/answers"  -> "questions/{ids}/answers"
    "questions"                  -> "questions"   (unchanged)
    """
    m = _ID_IN_ENDPOINT_RE.match(endpoint)
    if not m:
        return endpoint
    prefix  = m.group(1)
    suffix  = m.group(3) or ""
    return f"{prefix}/{{ids}}{suffix}"


def _count_ids(endpoint: str) -> int:
    """Count the number of IDs in a batch endpoint (0 if none)."""
    m = _ID_IN_ENDPOINT_RE.match(endpoint)
    if not m:
        return 0
    return len(m.group(2).split(";"))


def _raw_filename(endpoint: str, params: dict) -> Path:
    """Deterministic filename: masked prefix + SHA-1 of real (endpoint + sorted non-key params).

    The hash uses the REAL endpoint (so different ID batches → different files).
    The file-name prefix uses the MASKED endpoint (no IDs visible in filenames).
    """
    safe_params = {k: v for k, v in sorted(params.items()) if k != "key"}
    blob = json.dumps({"endpoint": endpoint, "params": safe_params}, sort_keys=True)
    digest = hashlib.sha1(blob.encode()).hexdigest()[:16]

    # Masked prefix: "users_n5", "answers_n3", "questions", etc.
    masked = _mask_endpoint(endpoint)
    n_ids  = _count_ids(endpoint)
    if n_ids:
        prefix_ep = masked.replace("/", "_").replace("{ids}", f"n{n_ids}")
    else:
        prefix_ep = masked.replace("/", "_")[:60]

    return _RAW_DIR / f"{prefix_ep}__{digest}.json"


def _params_summary(params: dict, n_ids: int = 0) -> str:
    """Compact representation of params (key excluded); injects n_ids when > 0."""
    clean = {k: v for k, v in sorted(params.items()) if k != "key"}
    if n_ids:
        clean["n_ids"] = n_ids
    return json.dumps(clean, separators=(",", ":"))


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


def _pick_filter(endpoint: str, caller_params: dict | None) -> str:
    """Return the right filter for this endpoint.

    Precedence: caller-supplied > per-endpoint minimal filter > config default.
    """
    if caller_params and "filter" in caller_params:
        return caller_params["filter"]  # caller always wins
    first_segment = endpoint.split("/")[0]
    return _ENDPOINT_FILTERS.get(first_segment, _FILTER)


# ---------------------------------------------------------------------------
# Public: create_filter (run once per endpoint type)
# ---------------------------------------------------------------------------

def create_filter(endpoint_type: str = "questions") -> str:
    """Call /filters/create once with a minimal base="none" filter.

    Parameters
    ----------
    endpoint_type : One of "questions", "answers", "users".
                    Controls which fields are included.

    Returns the filter string to paste into config.yaml.
    """
    # Wrapper fields always needed for backoff / quota / paging / error handling
    wrapper_fields = (
        ".backoff;.error_id;.error_message;.error_name;"
        ".has_more;.items;.quota_max;.quota_remaining"
    )

    endpoint_fields = {
        "questions": (
            "question.question_id;question.accepted_answer_id;"
            "question.answer_count;question.creation_date;question.tags;"
            "question.title;question.body;question.score;"
            "question.view_count;question.is_answered;"
            "question.last_activity_date;question.closed_date;"
            "question.owner;shallow_user.user_id"
        ),
        "answers": (
            "answer.answer_id;answer.question_id;answer.creation_date"
        ),
        "users": (
            "user.user_id;user.creation_date"
        ),
    }

    include = f"{wrapper_fields};{endpoint_fields.get(endpoint_type, '')}"
    r = requests.get(
        f"{_BASE_URL}/filters/create",
        params={"include": include, "base": "none", "key": _api_key()},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    f = data["items"][0]["filter"]
    print(f"Filter string for {endpoint_type!r} (paste into config.yaml): {f}")
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
                  If 0 and the endpoint contains an ID list, the count is
                  inferred automatically.
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

    # Infer n_ids from the endpoint if not supplied explicitly
    if n_ids == 0:
        n_ids = _count_ids(endpoint)

    # Masked endpoint string for log and file names (no IDs)
    masked_ep = _mask_endpoint(endpoint)

    # Pick the right filter: caller wins, else per-endpoint minimal, else config
    chosen_filter = _pick_filter(endpoint, params)

    # Build full params: config defaults < caller overrides
    full_params: dict[str, Any] = {
        "site":     _SITE,
        "pagesize": _PAGE_SIZE,
        "filter":   chosen_filter,
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
            "endpoint":       masked_ep,
            "params_summary": _params_summary(full_params, n_ids),
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
                "endpoint":       masked_ep,
                "params_summary": _params_summary(full_params, n_ids),
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
                "endpoint":       masked_ep,
                "params_summary": _params_summary(full_params, n_ids),
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
                "endpoint":       masked_ep,
                "params_summary": _params_summary(full_params, n_ids),
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
            "endpoint":       masked_ep,
            "params_summary": _params_summary(full_params, n_ids),
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
    has_more = True
    while True:
        data = api_get("questions", params=params, page=page)
        page_items = data.get("items", [])
        for item in page_items:
            # Flatten owner.user_id
            owner = item.pop("owner", {}) or {}
            item["owner_user_id"] = owner.get("user_id")
            yield item

        if not page_items:
            break

        # If has_more was False, probe page+1 once. If page+1 is empty, loop breaks above.
        if not data.get("has_more"):
            has_more = False

        page += 1

