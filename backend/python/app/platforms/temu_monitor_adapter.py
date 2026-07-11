"""Temu monitor adapter backed by boards/ctf-website page-card evidence."""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib import error, request
from urllib.parse import parse_qs, urlparse

from app.external_snapshot.competitor_snapshot import fetch_snapshot
from app.platforms.temu_evidence import ensure_raw_products_file
from .base import MonitorPlatformAdapter


class TemuMonitorAdapter(MonitorPlatformAdapter):
    def crawl_target(self, *, tenant_id: int, target: dict, max_products: int) -> dict:
        target_url = str(target["target_url"])
        captured_at = str(target.get("captured_at") or datetime.utcnow().replace(microsecond=0).isoformat() + "+00:00")
        force_refresh = parse_bool(target.get("force_refresh"))
        evidence_file = None if force_refresh else resolve_page_card_evidence_file(target)
        if evidence_file is None:
            collect_evidence_from_http_collector(tenant_id=tenant_id, target=target, target_url=target_url)
            evidence_file = resolve_page_card_evidence_file(target)
        request = {
            "platform": "temu",
            "store_url": target_url,
            "captured_at": captured_at,
            "limit": max_products,
            "trace_id": str(target.get("job_id") or target.get("id") or "monitor-temu"),
            "options": {
                "ctf_page_card_file": str(evidence_file) if evidence_file else "",
            },
        }
        result = fetch_snapshot(request)
        status = str(result.get("status") or "")
        if status != "OK":
            error = result.get("error") or {}
            code = monitor_error_code(status)
            message = error.get("message") or f"Temu snapshot failed with status {status}"
            detail = error.get("detail") or ""
            raise RuntimeError(f"{code}: {message}{(': ' + detail) if detail else ''}")

        snapshot = result["snapshot"]
        return {
            "platform": "temu",
            "snapshot_at": monitor_snapshot_at(str(snapshot["captured_at"])),
            "products": [to_monitor_product(item) for item in snapshot["products"]],
            "snapshot_status": status,
            "snapshot_trace_id": result.get("trace_id"),
        }


def collect_evidence_from_http_collector(*, tenant_id: int, target: dict, target_url: str) -> dict[str, Any] | None:
    collector_url = os.environ.get("CROSSHUB_TEMU_COLLECTOR_URL", "").strip().rstrip("/")
    if not collector_url:
        return None
    target_id = str(target.get("id") or "").strip()
    if not target_id:
        return None

    payload: dict[str, Any] = {
        "target_id": target_id,
        "tenant_id": tenant_id,
        "capture_mode": os.environ.get("CROSSHUB_TEMU_COLLECTOR_CAPTURE_MODE", "browser").strip() or "browser",
        "store_url": target_url,
    }
    evidence_root = os.environ.get("CROSSHUB_MONITOR_EVIDENCE_DIR", "").strip()
    if evidence_root:
        payload["evidence_root"] = evidence_root
    timeout_ms = positive_int(os.environ.get("CROSSHUB_TEMU_COLLECTOR_TIMEOUT_MS"))
    if timeout_ms:
        payload["timeout_ms"] = timeout_ms
    if "CROSSHUB_TEMU_COLLECTOR_HEADLESS" in os.environ:
        payload["headless"] = parse_bool(os.environ.get("CROSSHUB_TEMU_COLLECTOR_HEADLESS"))

    body = json.dumps(payload).encode("utf-8")
    http_request = request.Request(
        f"{collector_url}/collector/temu/fetch",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    timeout_seconds = (timeout_ms / 1000.0) if timeout_ms else 70.0
    try:
        with request.urlopen(http_request, timeout=timeout_seconds) as response:
            result = json.loads(response.read().decode("utf-8-sig"))
    except TimeoutError as exc:
        raise RuntimeError(f"MONITOR_TIMEOUT: Temu collector timed out after {timeout_seconds:.1f}s") from exc
    except error.URLError as exc:
        raise RuntimeError(f"MONITOR_SOURCE_UNAVAILABLE: Temu collector unavailable: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"MONITOR_SOURCE_UNAVAILABLE: Temu collector returned invalid JSON: {exc}") from exc

    status = str(result.get("status") or "")
    if status and status != "OK":
        error_payload = result.get("error") or {}
        message = error_payload.get("message") or f"Temu collector failed with status {status}"
        meta_file = str(result.get("meta_file") or "")
        meta_hint = f" meta_file={meta_file}" if meta_file else ""
        meta = result.get("meta")
        meta_text = ""
        if isinstance(meta, dict) and meta:
            try:
                meta_text = json.dumps(meta, ensure_ascii=False)
            except Exception:
                meta_text = ""
        if meta_text and len(meta_text) > 900:
            meta_text = meta_text[:900] + "...(truncated)"
        meta_append = f" meta={meta_text}" if meta_text else ""
        raise RuntimeError(f"{monitor_error_code(status)}: {message}{meta_hint}{meta_append}")
    return result


def positive_int(value: Any) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def parse_bool(value: Any) -> bool:
    return str(value or "").strip().lower() in ("1", "true", "yes", "y", "on")


def resolve_page_card_evidence_file(target: dict) -> Path | None:
    explicit = target.get("ctf_page_card_file") or target.get("evidence_file")
    if explicit:
        path = Path(str(explicit))
        return path if path.exists() else None

    evidence_dir = os.environ.get("CROSSHUB_MONITOR_EVIDENCE_DIR")
    if not evidence_dir:
        return None
    root = Path(evidence_dir)
    target_id = str(target.get("id") or "")
    mall_id = mall_id_from_url(str(target.get("target_url") or ""))
    candidates = []
    if target_id:
        target_dir = root / target_id
        prepared = ensure_raw_products_file(target_dir) if target_dir.exists() else None
        if prepared:
            return prepared
        candidates.append(root / f"{target_id}.json")
    if mall_id:
        mall_dir = root / mall_id
        prepared = ensure_raw_products_file(mall_dir) if mall_dir.exists() else None
        if prepared:
            return prepared
        candidates.append(root / f"{mall_id}.json")
    candidates.append(root / "raw_products.json")
    for path in candidates:
        if path.exists():
            return path
    return None


def mall_id_from_url(url: str) -> str:
    try:
        return parse_qs(urlparse(url).query).get("mall_id", [""])[0]
    except Exception:
        return ""


def monitor_error_code(status: str) -> str:
    return {
        "NO_PRODUCTS": "MONITOR_NO_PRODUCTS",
        "INVALID_URL": "MONITOR_INVALID_URL",
        "SOURCE_UNAVAILABLE": "MONITOR_SOURCE_UNAVAILABLE",
        "PARSER_CHANGED": "MONITOR_PARSER_CHANGED",
        "AUTH_REQUIRED": "MONITOR_AUTH_REQUIRED",
        "RISK_BLOCKED": "MONITOR_RISK_BLOCKED",
        "TIMEOUT": "MONITOR_TIMEOUT",
    }.get(status, "MONITOR_JOB_FAILED")


def monitor_snapshot_at(captured_at: str) -> str:
    normalized = captured_at.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
        return parsed.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return captured_at[:19].replace("T", " ")


def to_monitor_product(item: dict) -> dict:
    sales = item.get("sales") or {}
    price = item.get("price") or {}
    sales_value = int(sales.get("value") or 0)
    return {
        "product_id": str(item.get("product_id") or ""),
        "product_name": str(item.get("product_name") or ""),
        "category": str(item.get("category") or ""),
        "price": float(price.get("amount") or 0),
        "daily_sales": sales_value,
        "total_sales": sales_value,
        "listed_at": str(item.get("listed_at") or "")[:10],
        "url": str(item.get("product_url") or ""),
    }
