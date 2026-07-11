from __future__ import annotations

import argparse
import json
import re
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse


def analyze_products(
    raw_products: list[dict[str, Any]],
    store_id: str = "",
    latest_limit: int = 12,
    captured_at: str | None = None,
) -> dict[str, Any]:
    captured_at = captured_at or datetime.now(timezone.utc).isoformat()
    products = [normalize_card(item) for item in raw_products]
    products = [item for item in products if item]
    products_by_newness = sorted(products, key=lambda item: item["goods_id_num"], reverse=True)
    sold_values = [item["sales"]["value"] for item in products if isinstance(item["sales"]["value"], int)]
    threshold = iqr_upper_fence(sold_values)

    latest = [
        {
            **public_product_fields(item),
            "listed_at": captured_at,
            "listed_at_confidence": "INFERRED",
            "basis": "GOODS_ID_DESC",
        }
        for item in products_by_newness[: max(latest_limit, 0)]
    ]
    outliers = [
        {
            **public_product_fields(item),
            "reason": "SALES_ABOVE_IQR_UPPER_FENCE",
            "threshold": threshold,
        }
        for item in products
        if threshold is not None and isinstance(item["sales"]["value"], int) and item["sales"]["value"] > threshold
    ]
    outliers.sort(key=lambda item: item["sales"]["value"] or 0, reverse=True)

    return {
        "status": "OK" if products else "NO_PRODUCTS",
        "analysis_status": "OK" if products else "UNAVAILABLE",
        "project_board": "ctf-website",
        "method": "TEMU_VISIBLE_PAGE_CARD_ANALYSIS",
        "captured_at": captured_at,
        "target": {
            "platform": "temu",
            "store_id": store_id,
        },
        "snapshot_summary": {
            "raw_count": len(raw_products),
            "analyzable_count": len(products),
            "latest_basis": "goods_id descending as a page-card newness proxy",
            "sales_outlier_basis": "IQR upper fence on current visible page-card sales",
            "sales_outlier_threshold": threshold,
        },
        "latest_listings": latest,
        "abnormal_sales": outliers,
    }


def normalize_card(item: dict[str, Any]) -> dict[str, Any]:
    goods_id = str(item.get("goods_id") or "").strip()
    goods_id_num = parse_int(item.get("goods_id_num") or goods_id)
    product_url = str(item.get("href") or "")
    product_name = recover_product_name(
        str(item.get("title_clean") or item.get("title") or "").strip(),
        product_url,
        goods_id,
    )
    if not goods_id or goods_id_num is None or not product_name:
        return {}
    sold_value = parse_int(item.get("sold_num"))
    return {
        "product_id": goods_id,
        "goods_id_num": goods_id_num,
        "product_name": product_name,
        "price": {
            "amount": parse_float(item.get("price_yen")),
            "currency": "JPY",
        },
        "sales": {
            "value": sold_value,
            "strength": sales_strength(sold_value),
            "raw_text": str(item.get("sold_text") or item.get("sold_num") or ""),
        },
        "rating": parse_float(item.get("rating")),
        "reviews": parse_int(item.get("reviews")),
        "product_url": product_url,
    }


def recover_product_name(raw_name: str, product_url: str, goods_id: str) -> str:
    url_name = product_name_from_url(product_url, goods_id)
    if url_name and (not raw_name or is_garbled_text(raw_name)):
        return url_name
    return raw_name or url_name


def is_garbled_text(text: str) -> bool:
    return "\ufffd" in text


def product_name_from_url(product_url: str, goods_id: str) -> str:
    if not product_url:
        return ""
    segment = unquote(urlparse(product_url).path).rstrip("/").split("/")[-1]
    if not segment:
        return ""
    suffix = f"-g-{goods_id}.html"
    if segment.endswith(suffix):
        segment = segment[: -len(suffix)]
    else:
        segment = re.sub(r"-g-\d+\.html$", "", segment)
    return segment.strip("- ").replace("-", " ").strip()


def public_product_fields(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "product_id": item["product_id"],
        "product_name": item["product_name"],
        "price": item["price"],
        "sales": item["sales"],
        "rating": item["rating"],
        "reviews": item["reviews"],
        "product_url": item["product_url"],
    }


def iqr_upper_fence(values: list[int]) -> float | None:
    if len(values) < 4:
        return None
    sorted_values = sorted(values)
    midpoint = len(sorted_values) // 2
    lower = sorted_values[:midpoint]
    upper = sorted_values[midpoint:] if len(sorted_values) % 2 == 0 else sorted_values[midpoint + 1 :]
    q1 = statistics.median(lower)
    q3 = statistics.median(upper)
    return float(q3 + 1.5 * (q3 - q1))


def sales_strength(value: int | None) -> str:
    if value is None:
        return "UNKNOWN"
    if value >= 5000:
        return "VERY_HIGH"
    if value >= 1000:
        return "HIGH"
    if value >= 100:
        return "MEDIUM"
    return "LOW"


def parse_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    text = str(value).replace(",", "").strip()
    multiplier = 1
    if text.endswith("\u4e07"):
        multiplier = 10000
        text = text[:-1]
    match = re.search(r"\d+(?:\.\d+)?", text)
    if not match:
        return None
    return int(float(match.group(0)) * multiplier)


def parse_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    match = re.search(r"\d+(?:\.\d+)?", str(value).replace(",", ""))
    return float(match.group(0)) if match else None


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze Temu visible page-card exports for competitor intelligence.")
    parser.add_argument("--input", required=True, help="raw_products.json produced from visible page-card extraction")
    parser.add_argument("--output", default="", help="optional output JSON path")
    parser.add_argument("--store-id", default="")
    parser.add_argument("--latest-limit", type=int, default=12)
    parser.add_argument("--captured-at", default="")
    args = parser.parse_args()

    raw_payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    if isinstance(raw_payload, dict) and isinstance(raw_payload.get("raw_products"), list):
        raw_products = raw_payload["raw_products"]
    else:
        raw_products = raw_payload if isinstance(raw_payload, list) else raw_payload
        if not isinstance(raw_products, list):
            raise SystemExit("input must be a product list or an object with raw_products")
    result = analyze_products(
        raw_products,
        store_id=args.store_id,
        latest_limit=args.latest_limit,
        captured_at=args.captured_at or None,
    )
    encoded = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
