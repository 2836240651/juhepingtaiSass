from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class SnapshotStatus:
    OK = "OK"
    PARTIAL_OK = "PARTIAL_OK"
    AUTH_REQUIRED = "AUTH_REQUIRED"
    RISK_BLOCKED = "RISK_BLOCKED"
    STORE_UNAVAILABLE = "STORE_UNAVAILABLE"
    NO_PRODUCTS = "NO_PRODUCTS"
    INVALID_URL = "INVALID_URL"
    PARSER_CHANGED = "PARSER_CHANGED"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    RATE_LIMITED = "RATE_LIMITED"
    TIMEOUT = "TIMEOUT"
    UNSUPPORTED_PLATFORM = "UNSUPPORTED_PLATFORM"
    INTERNAL_ERROR = "INTERNAL_ERROR"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_trace_id(request: dict[str, Any]) -> str:
    trace_id = request.get("trace_id")
    return str(trace_id) if trace_id else f"snapshot-{int(datetime.now(timezone.utc).timestamp())}"


def error_response(
    status: str,
    request: dict[str, Any],
    message: str,
    detail: str = "",
    source: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "status": status,
        "trace_id": get_trace_id(request),
        "source": source,
        "snapshot": None,
        "error": {"code": status, "message": message, "detail": detail},
    }


def success_response(
    request: dict[str, Any],
    source: dict[str, Any],
    snapshot: dict[str, Any],
    status: str = SnapshotStatus.OK,
) -> dict[str, Any]:
    return {
        "status": status,
        "trace_id": get_trace_id(request),
        "source": source,
        "snapshot": snapshot,
        "error": None,
    }
