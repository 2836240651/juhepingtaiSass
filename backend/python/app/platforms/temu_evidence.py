"""Convert Temu browser/API evidence into worker-consumable raw_products.json."""
from __future__ import annotations

import base64
import json
import re
from pathlib import Path
from typing import Any


RAW_PRODUCTS_FILENAMES = ("raw_products.json",)
SOURCE_FILENAMES = ("raw_payload.json", "payload.json", "capture.har", "network.har")


def ensure_raw_products_file(evidence_dir: Path) -> Path | None:
    for filename in RAW_PRODUCTS_FILENAMES:
        raw_file = evidence_dir / filename
        if raw_file.exists():
            return raw_file
    for filename in SOURCE_FILENAMES:
        source_file = evidence_dir / filename
        if source_file.exists():
            return ingest_evidence_file(source_file, evidence_dir / "raw_products.json")
    return None


def ingest_evidence_file(source_file: Path, output_file: Path) -> Path:
    payload = json.loads(source_file.read_text(encoding="utf-8-sig"))
    products = extract_products_from_har(payload) if is_har_payload(payload) else extract_raw_products(payload)
    if not products:
        raise ValueError(f"No Temu products found in evidence file: {source_file}")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(products, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_file


def is_har_payload(payload: Any) -> bool:
    return isinstance(payload, dict) and isinstance(payload.get("log"), dict) and isinstance(payload["log"].get("entries"), list)


def extract_products_from_har(har_payload: dict[str, Any]) -> list[dict[str, Any]]:
    products: list[dict[str, Any]] = []
    for entry in har_payload.get("log", {}).get("entries", []):
        if not isinstance(entry, dict):
            continue
        content = ((entry.get("response") or {}).get("content") or {})
        if not isinstance(content, dict):
            continue
        text = str(content.get("text") or "")
        if not text:
            continue
        if content.get("encoding") == "base64":
            try:
                text = base64.b64decode(text).decode("utf-8", errors="replace")
            except Exception:
                continue
        try:
            response_payload = json.loads(text)
        except json.JSONDecodeError:
            continue
        products.extend(extract_raw_products(response_payload))
    return dedupe_products(products)


def extract_raw_products(payload: Any) -> list[dict[str, Any]]:
    products = []
    for item in walk_dicts(payload):
        product = normalize_product_candidate(item)
        if product:
            products.append(product)
    return dedupe_products(products)


def walk_dicts(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_dicts(child)


def normalize_product_candidate(item: dict[str, Any]) -> dict[str, Any]:
    goods_id = pick_text(item, "goods_id", "goodsId", "goodsID", "product_id", "productId", "id")
    href = pick_text(item, "href", "url", "linkUrl", "link_url", "product_url", "productUrl")
    if not goods_id:
        goods_id = extract_goods_id(href)
    title = pick_text(
        item,
        "title",
        "title_clean",
        "titleClean",
        "goods_name",
        "goodsName",
        "product_name",
        "productName",
        "name",
    )
    if not goods_id or not title:
        return {}
    price = pick_number(
        item,
        ("price_yen", "priceYen", "salePrice", "sale_price", "currentPrice", "current_price", "price", "priceInfo", "price_info"),
        nested_keys=("amount", "price", "value", "minPrice"),
    )
    sold_text = pick_text(item, "sold_text", "soldText", "salesText", "soldQuantityText")
    if not sold_text:
        sold_text = pick_text(item, "sold_num", "soldNum", "sold", "sales", "salesVolume", "soldQuantity", "sold_quantity")
    sold_num = pick_number(
        item,
        ("sold_num", "soldNum", "sold", "sales", "salesVolume", "soldQuantity", "sold_quantity"),
        nested_keys=("value", "count", "amount"),
    )
    return {
        "goods_id": str(goods_id),
        "title": title,
        "price_yen": price,
        "sold_num": int(sold_num or 0),
        "sold_text": sold_text or (str(int(sold_num)) if sold_num is not None else ""),
        "href": href or f"https://www.temu.com/goods-g-{goods_id}.html",
    }


def pick_text(item: dict[str, Any], *keys: str) -> str:
    for key in keys:
        if key in item and item[key] not in (None, ""):
            value = item[key]
            if isinstance(value, (str, int, float)) and not isinstance(value, bool):
                return str(value).strip()
    return ""


def pick_number(item: dict[str, Any], keys: tuple[str, ...], *, nested_keys: tuple[str, ...]) -> float | None:
    for key in keys:
        if key not in item:
            continue
        value = item[key]
        parsed = parse_number(value)
        if parsed is not None:
            return parsed
        if isinstance(value, dict):
            for nested_key in nested_keys:
                parsed = parse_number(value.get(nested_key))
                if parsed is not None:
                    return parsed
    return None


def parse_number(value: Any) -> float | None:
    if value in (None, "") or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).replace(",", "").strip()
    multiplier = 1
    if text.endswith("万"):
        multiplier = 10000
        text = text[:-1]
    match = re.search(r"\d+(?:\.\d+)?", text)
    return float(match.group(0)) * multiplier if match else None


def extract_goods_id(url: str) -> str:
    if not url:
        return ""
    for pattern in (r"[?&]goods_id=(\d+)", r"-g-(\d+)\.html", r"/goods/(\d+)"):
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return ""


def dedupe_products(products: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped = {}
    for product in products:
        goods_id = str(product.get("goods_id") or "")
        if goods_id and goods_id not in deduped:
            deduped[goods_id] = product
    return list(deduped.values())
