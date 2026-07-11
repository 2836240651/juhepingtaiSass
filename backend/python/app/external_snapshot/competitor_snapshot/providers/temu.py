from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from app.external_snapshot.competitor_snapshot.models import SnapshotStatus, error_response, success_response, utc_now_iso
from app.external_snapshot.ctf_website import temu_competitor_analysis as analyzer


class TemuProvider:
    platform = "temu"

    def capabilities(self) -> dict[str, Any]:
        return {
            "platform": self.platform,
            "source_type": "AUTHORIZED_INTERNAL_COLLECTOR",
            "analysis_route": "boards/ctf-website",
            "requires_auth": False,
            "uses_browser": False,
            "risk_block_possible": False,
            "production_scheduling": "EVIDENCE_DRIVEN",
            "supported_evidence": [
                "options.ctf_page_card_products",
                "options.ctf_page_card_file",
                "evidence.raw_payload_json",
                "evidence.har",
            ],
            "supported_fields": [
                "product_id",
                "product_name",
                "price",
                "sales",
                "listed_at",
                "product_url",
                "category",
                "image_url",
                "stock_status",
            ],
        }

    def fetch_snapshot(self, request: dict[str, Any]) -> dict[str, Any]:
        store_url = str(request.get("store_url") or "")
        if store_url and not is_temu_store_url(store_url):
            return error_response(
                SnapshotStatus.INVALID_URL,
                request,
                "Temu provider requires a valid temu.com mall URL.",
                source=self.capabilities(),
            )

        options = request.get("options") or {}
        has_inline_evidence = "ctf_page_card_products" in options
        has_file_evidence = bool(options.get("ctf_page_card_file"))
        if not has_inline_evidence and not has_file_evidence:
            return error_response(
                SnapshotStatus.SOURCE_UNAVAILABLE,
                request,
                "Temu snapshots require boards/ctf-website page-card evidence.",
                source=self.capabilities(),
            )

        raw_products, load_error = load_page_card_products(options)
        if load_error:
            return error_response(
                SnapshotStatus.SOURCE_UNAVAILABLE,
                request,
                "Failed to load boards/ctf-website page-card evidence.",
                load_error,
                self.capabilities(),
            )
        if not raw_products:
            return error_response(
                SnapshotStatus.NO_PRODUCTS,
                request,
                "boards/ctf-website page-card evidence did not contain products.",
                source=self.capabilities(),
            )

        return self._snapshot_from_page_cards(request, store_url, raw_products)

    def _snapshot_from_page_cards(self, request: dict[str, Any], store_url: str, raw_products: list[dict[str, Any]]) -> dict[str, Any]:
        captured_at = str(request.get("captured_at") or utc_now_iso())
        store_id = extract_mall_id(store_url) or str(request.get("store_id") or "")
        limit = int(request.get("limit") or len(raw_products))
        latest_limit = int((request.get("options") or {}).get("latest_limit") or min(max(limit, 0), 12))
        analysis = analyzer.analyze_products(
            raw_products,
            store_id=store_id,
            latest_limit=latest_limit,
            captured_at=captured_at,
        )
        normalized = [analyzer.normalize_card(item) for item in raw_products]
        normalized = [item for item in normalized if item]
        if not normalized:
            return error_response(
                SnapshotStatus.PARSER_CHANGED,
                request,
                "Page-card products were present but required fields could not be normalized.",
                source=self.capabilities(),
            )

        normalized.sort(key=lambda item: item["goods_id_num"], reverse=True)
        products = [snapshot_product_from_card(item, captured_at) for item in normalized[: max(limit, 0)]]
        completeness = "FULL" if len(products) >= len(normalized) else "PARTIAL"
        snapshot = {
            "captured_at": captured_at,
            "store_id": store_id,
            "store_url": store_url,
            "total_products": len(normalized),
            "fetched_count": len(products),
            "completeness": completeness,
            "products": products,
            "analysis": {
                "project_board": analysis["project_board"],
                "method": analysis["method"],
                "snapshot_summary": analysis["snapshot_summary"],
                "latest_listings": analysis["latest_listings"],
                "abnormal_sales": analysis["abnormal_sales"],
            },
        }
        return success_response(request, self.capabilities(), snapshot, SnapshotStatus.OK)


def load_page_card_products(options: dict[str, Any]) -> tuple[list[dict[str, Any]], str]:
    if "ctf_page_card_products" in options:
        value = options.get("ctf_page_card_products")
        if not isinstance(value, list):
            return [], "options.ctf_page_card_products must be a list."
        return [item for item in value if isinstance(item, dict)], ""

    evidence_path = str(options.get("ctf_page_card_file") or "")
    if not evidence_path:
        return [], ""
    path = Path(evidence_path)
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        return [], str(exc)
    except json.JSONDecodeError as exc:
        return [], str(exc)
    if isinstance(loaded, list):
        return [item for item in loaded if isinstance(item, dict)], ""
    if isinstance(loaded, dict):
        for key in ("raw_products", "page_card_products", "products"):
            value = loaded.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)], ""
    return [], "ctf_page_card_file must contain a product list or an object with raw_products/page_card_products/products."


def snapshot_product_from_card(item: dict[str, Any], captured_at: str) -> dict[str, Any]:
    return {
        "product_id": item["product_id"],
        "product_name": item["product_name"],
        "price": item["price"],
        "sales": item["sales"],
        "listed_at": captured_at,
        "listed_at_confidence": "INFERRED",
        "product_url": item["product_url"],
        "category": None,
        "image_url": "",
        "stock_status": "UNKNOWN",
        "rating": item.get("rating"),
        "reviews": item.get("reviews"),
    }


def is_temu_store_url(url: str) -> bool:
    parsed = urlparse(html.unescape(url))
    host = parsed.netloc.lower()
    if not (host == "www.temu.com" or host.endswith(".temu.com")):
        return False
    query = parse_qs(parsed.query)
    return parsed.path.endswith("/mall.html") or "mall_id" in query


def extract_mall_id(url: str) -> str:
    if not url:
        return ""
    parsed = urlparse(html.unescape(url))
    return parse_qs(parsed.query).get("mall_id", [""])[0]
