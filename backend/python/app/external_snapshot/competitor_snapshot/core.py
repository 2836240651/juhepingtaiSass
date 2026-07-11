from __future__ import annotations

from typing import Any

from .models import SnapshotStatus, error_response
from .providers.temu import TemuProvider


def fetch_snapshot(request: dict[str, Any]) -> dict[str, Any]:
    platform = str(request.get("platform") or "").strip().lower()
    if not platform:
        return error_response(SnapshotStatus.UNSUPPORTED_PLATFORM, request, "Missing platform.")
    if platform != "temu":
        return error_response(SnapshotStatus.UNSUPPORTED_PLATFORM, request, f"Unsupported platform: {platform}.")
    if not request.get("store_id") and not request.get("store_url"):
        return error_response(SnapshotStatus.INVALID_URL, request, "Either store_id or store_url is required.")
    try:
        return TemuProvider().fetch_snapshot(request)
    except Exception as exc:
        return error_response(SnapshotStatus.INTERNAL_ERROR, request, "Unexpected provider error.", str(exc), TemuProvider().capabilities())
