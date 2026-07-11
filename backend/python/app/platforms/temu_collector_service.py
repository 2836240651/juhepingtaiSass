"""Small HTTP collector that converts Temu HAR/API payload evidence to raw_products.json."""
from __future__ import annotations

import json
import tempfile
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from app.browser.context import open_temu_context, requires_auth
from app.platforms.temu_evidence import dedupe_products, extract_raw_products, ingest_evidence_file


CAPABILITIES = {
    "platforms": ["temu"],
    "endpoints": ["GET /health", "GET /capabilities", "POST /collector/temu/fetch"],
    "supported_evidence": ["raw_payload", "har", "source_file", "authorized_browser"],
    "writes": ["raw_payload.json", "raw_products.json"],
    "source_type": "AUTHORIZED_BROWSER_OR_PAYLOAD_EVIDENCE",
    "uses_worker": False,
}


def create_server(address: tuple[str, int], *, default_evidence_root: Path) -> ThreadingHTTPServer:
    class TemuCollectorHandler(BaseHTTPRequestHandler):
        evidence_root = default_evidence_root

        def do_GET(self) -> None:
            if self.path == "/health":
                self.write_json({"status": "ok"})
                return
            if self.path == "/capabilities":
                self.write_json(CAPABILITIES)
                return
            self.write_json({"status": "NOT_FOUND", "error": {"code": "NOT_FOUND"}}, HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:
            if self.path != "/collector/temu/fetch":
                self.write_json({"status": "NOT_FOUND", "error": {"code": "NOT_FOUND"}}, HTTPStatus.NOT_FOUND)
                return
            try:
                request = self.read_json()
                response = collect_temu_fetch(request, default_evidence_root=self.evidence_root)
                self.write_json(response)
            except Exception as exc:
                self.write_json(
                    {
                        "status": "INTERNAL_ERROR",
                        "error": {"code": "INTERNAL_ERROR", "message": str(exc)},
                    },
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                )

        def read_json(self) -> dict[str, Any]:
            content_length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(content_length).decode("utf-8-sig") if content_length else "{}"
            value = json.loads(raw)
            if not isinstance(value, dict):
                raise ValueError("Request body must be a JSON object.")
            return value

        def write_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
            encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(int(status))
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def log_message(self, format: str, *args: Any) -> None:
            return

    return ThreadingHTTPServer(address, TemuCollectorHandler)


def collect_temu_fetch(request: dict[str, Any], *, default_evidence_root: Path) -> dict[str, Any]:
    target_id = clean_target_id(str(request.get("target_id") or ""))
    if not target_id:
        return error_response("INVALID_TARGET", "target_id is required.")
    store_url = str(request.get("store_url") or "")
    evidence_root = Path(str(request.get("evidence_root") or default_evidence_root))
    target_dir = evidence_root / target_id
    target_dir.mkdir(parents=True, exist_ok=True)

    if wants_browser_capture(request):
        return collect_from_authorized_browser(request, target_id=target_id, store_url=store_url, target_dir=target_dir)

    source_file = materialize_source_file(request, target_dir)
    if source_file is None:
        return error_response(
            "SOURCE_UNAVAILABLE",
            "Provide raw_payload, har, or source_file captured from an authorized browser/session.",
            target_id=target_id,
            store_url=store_url,
        )

    raw_products_file = ingest_evidence_file(source_file, target_dir / "raw_products.json")
    products = json.loads(raw_products_file.read_text(encoding="utf-8"))
    return {
        "status": "OK",
        "target_id": target_id,
        "store_url": store_url,
        "raw_products_file": str(raw_products_file),
        "product_count": len(products),
        "source_type": source_type_for(source_file),
    }


def wants_browser_capture(request: dict[str, Any]) -> bool:
    capture_mode = str(request.get("capture_mode") or "").strip().lower()
    source_type = str(request.get("source_type") or "").strip().upper()
    return capture_mode in ("browser", "authorized_browser") or source_type == "AUTHORIZED_BROWSER_SESSION"


def collect_from_authorized_browser(
    request: dict[str, Any],
    *,
    target_id: str,
    store_url: str,
    target_dir: Path,
) -> dict[str, Any]:
    if not store_url:
        return error_response("INVALID_URL", "store_url is required for browser capture.", target_id=target_id)
    tenant_id = parse_positive_int(request.get("tenant_id"))
    if tenant_id is None:
        return error_response("AUTH_REQUIRED", "tenant_id is required for authorized browser capture.", target_id=target_id)

    timeout_ms = parse_positive_int(request.get("timeout_ms")) or 45_000
    headless = parse_bool(request.get("headless"), default=True)
    captured_payloads: list[dict[str, Any]] = []
    captured_products: list[dict[str, Any]] = []
    stats: dict[str, Any] = {
        "captured_json_responses": 0,
        "captured_payloads": 0,
        "captured_products_raw": 0,
        "unique_products": 0,
        "final_url": "",
        "page_title": "",
        "auth_redirected": False,
        "risk_hint": "",
    }
    meta_file = target_dir / "meta.json"

    def persist_meta() -> None:
        # best effort: 失败时也要写 meta.json，便于 monitor_job.error_detail 溯源
        try:
            write_json_source(meta_file, stats)
        except Exception:
            pass

    def on_response(response: Any) -> None:
        payload = read_json_response(response)
        if payload is None:
            return
        stats["captured_json_responses"] += 1
        products = extract_raw_products(payload)
        if not products:
            return
        captured_payloads.append(payload)
        captured_products.extend(products)
        stats["captured_payloads"] = len(captured_payloads)
        stats["captured_products_raw"] = len(captured_products)

    try:
        with open_temu_context(tenant_id, headless=headless) as (_, context):
            page = context.new_page()
            page.on("response", on_response)
            page.goto(store_url, wait_until="domcontentloaded", timeout=timeout_ms)
            stats["final_url"] = getattr(page, "url", "") or ""
            try:
                stats["page_title"] = page.title() or ""
            except Exception:
                stats["page_title"] = ""
            if requires_auth(stats["final_url"]):
                stats["auth_redirected"] = True
                persist_meta()
                return error_response(
                    "AUTH_REQUIRED",
                    "Authorized browser session is not logged in or was redirected to login.",
                    target_id=target_id,
                    store_url=store_url,
                    meta=stats,
                    meta_file=str(meta_file),
                )
            try:
                page.wait_for_load_state("networkidle", timeout=min(timeout_ms, 8_000))
            except Exception:
                pass
            deadline = time.monotonic() + max(timeout_ms / 1000.0, 0)
            while not captured_products and time.monotonic() < deadline:
                try:
                    page.wait_for_timeout(500)
                except Exception:
                    break
            stats["final_url"] = getattr(page, "url", "") or stats["final_url"]
            try:
                stats["page_title"] = page.title() or stats["page_title"]
            except Exception:
                pass
    except Exception as exc:
        message = str(exc)
        code = "RISK_BLOCKED" if is_risk_block_message(message) else "SOURCE_UNAVAILABLE"
        stats["risk_hint"] = "RISK_BLOCKED" if code == "RISK_BLOCKED" else ""
        persist_meta()
        return error_response(code, message or "Authorized browser capture failed.", target_id=target_id, store_url=store_url)

    products = dedupe_products(captured_products)
    stats["unique_products"] = len(products)
    if not products:
        persist_meta()
        return error_response(
            "NO_PRODUCTS",
            "Authorized browser capture completed but no product payload was observed.",
            target_id=target_id,
            store_url=store_url,
            meta=stats,
            meta_file=str(meta_file),
        )

    raw_payload_file = target_dir / "raw_payload.json"
    raw_products_file = target_dir / "raw_products.json"
    payload_to_write: Any = captured_payloads[0] if len(captured_payloads) == 1 else {"responses": captured_payloads}
    write_json_source(raw_payload_file, payload_to_write)
    write_json_source(raw_products_file, products)
    write_json_source(meta_file, stats)
    return {
        "status": "OK",
        "target_id": target_id,
        "store_url": store_url,
        "raw_payload_file": str(raw_payload_file),
        "raw_products_file": str(raw_products_file),
        "meta_file": str(meta_file),
        "meta": stats,
        "product_count": len(products),
        "source_type": "AUTHORIZED_BROWSER_SESSION",
    }


def read_json_response(response: Any) -> Any | None:
    headers = getattr(response, "headers", {}) or {}
    content_type = str(headers.get("content-type") or headers.get("Content-Type") or "").lower()
    if content_type and "json" not in content_type:
        return None
    try:
        return response.json()
    except Exception:
        pass
    try:
        text = response.text()
    except Exception:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def parse_positive_int(value: Any) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def parse_bool(value: Any, *, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("1", "true", "yes", "y", "on")


def is_risk_block_message(message: str) -> bool:
    lowered = (message or "").lower()
    return any(token in lowered for token in ("risk", "captcha", "verify", "challenge", "blocked"))


def materialize_source_file(request: dict[str, Any], target_dir: Path) -> Path | None:
    if "raw_payload" in request:
        return write_json_source(target_dir / "raw_payload.json", request["raw_payload"])
    if "payload" in request:
        return write_json_source(target_dir / "payload.json", request["payload"])
    if "har" in request:
        return write_json_source(target_dir / "capture.har", request["har"])
    source_file = str(request.get("source_file") or "").strip()
    if source_file:
        path = Path(source_file)
        return path if path.exists() else None
    return None


def write_json_source(path: Path, value: Any) -> Path:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def source_type_for(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".har":
        return "HAR"
    return "API_PAYLOAD"


def clean_target_id(value: str) -> str:
    if not value or any(ch in value for ch in "\\/:*?\"<>|"):
        return ""
    return value


def error_response(code: str, message: str, **extra: Any) -> dict[str, Any]:
    payload = {
        "status": code,
        "error": {"code": code, "message": message},
    }
    payload.update(extra)
    return payload


def run_server(*, host: str, port: int, evidence_root: Path) -> None:
    server = create_server((host, port), default_evidence_root=evidence_root)
    try:
        server.serve_forever()
    finally:
        server.server_close()
