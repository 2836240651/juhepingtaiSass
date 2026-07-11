"""Shared Temu mall page-card collection and normalization helpers."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

PRICE_JPY_RE = re.compile(r"([\d,]+)\s*円")
PRICE_GENERIC_RE = re.compile(r"(?:¥|￥|\$|€|£)\s?([\d.,]+)")
SOLD_JP_RE = re.compile(r"([\d,]+(?:\.\d+)?)\s*万\s*販売|([\d,]+)\s*販売")
SOLD_EN_RE = re.compile(r"([\d.,]+)\s*(K|M|万)?\+?\s*sold", re.I)
RATING_JP_RE = re.compile(r"5つ星中\s*([\d.]+)")
RATING_EN_RE = re.compile(r"(\d(?:\.\d)?)\s*(?:stars?|★)", re.I)
REVIEW_JP_RE = re.compile(r"([\d,]+)\s*件のレビュー")
REVIEW_EN_RE = re.compile(r"([\d,]+)\s*(?:reviews?|ratings?)", re.I)
LISTED_JP_RE = re.compile(r"TEMUで(\d+)年前に販売開始")
TITLE_PREFIX_RE = re.compile(r"^(?:アイテム画像|一押し商品|AD)\s+")

DOM_EXTRACT_JS = """() => {
  const out = [];
  const seen = new Set();
  for (const a of document.querySelectorAll('a[href*="-g-"]')) {
    const href = a.href || '';
    const m = href.match(/-g-(\\d+)\\.html/);
    if (!m) continue;
    const goodsId = m[1];
    if (seen.has(goodsId)) continue;
    seen.add(goodsId);
    const card = a.closest('[data-tooltip], [class*="goods"], [class*="product"], li, article, div') || a;
    const text = (card?.innerText || '').replace(/\\s+/g, ' ').trim();
    const title = (a.getAttribute('aria-label') || a.title || '').trim();
    out.push({ goods_id: goodsId, goods_id_num: Number(goodsId), title, title_clean: title, href, text, source: 'dom' });
  }
  return out;
}"""

DISMISS_OVERLAYS_JS = """() => {
  const closeCandidates = Array.from(document.querySelectorAll('button, [role="button"], svg, [aria-label]'));
  for (const el of closeCandidates) {
    const label = (el.getAttribute('aria-label') || el.innerText || '').trim();
    if (label === '×' || label.includes('閉') || label.toLowerCase().includes('close')) {
      try { el.click(); return true; } catch (e) {}
    }
  }
  document.querySelectorAll('[role="dialog"], [class*="modal"], [class*="dialog"]').forEach((el) => {
    try { el.remove(); } catch (e) {}
  });
  return false;
}"""


def parse_mall_id(store_url: str) -> str:
    parsed = urlparse(store_url)
    mall_id = parse_qs(parsed.query).get("mall_id", [""])[0]
    if mall_id:
        return mall_id
    raise ValueError("store_url must include mall_id query parameter")


def canonical_mall_url(store_url: str) -> str:
    mall_id = parse_mall_id(store_url)
    return f"https://www.temu.com/jp/mall.html?mall_id={mall_id}"


def default_output_paths(mall_id: str, root: Path | None = None) -> dict[str, Path]:
    root = root or Path.cwd()
    export_dir = root / "exports" / "ctf-website" / f"temu-mall-{mall_id}"
    report_dir = root / "reports" / "misc" / f"temu-mall-{mall_id}"
    return {
        "export_dir": export_dir,
        "report_dir": report_dir,
        "raw_products": export_dir / "raw_products.json",
        "analysis": report_dir / "analysis.json",
        "report": report_dir / "report.md",
        "manifest": report_dir / "run-manifest.json",
    }


def product_name_from_url(product_url: str, goods_id: str) -> str:
    segment = unquote(urlparse(product_url).path).rstrip("/").split("/")[-1]
    suffix = f"-g-{goods_id}.html"
    if segment.endswith(suffix):
        segment = segment[: -len(suffix)]
    else:
        segment = re.sub(r"-g-\d+\.html$", "", segment)
    return segment.replace("-", " ").strip()


def parse_price(text: str) -> float | None:
    match = PRICE_JPY_RE.search(text) or PRICE_GENERIC_RE.search(text)
    if not match:
        return None
    return float(match.group(1).replace(",", ""))


def parse_sold_num(text: str) -> tuple[int | None, str]:
    match = SOLD_JP_RE.search(text)
    if match:
        if match.group(1):
            return int(float(match.group(1).replace(",", "")) * 10000), match.group(0)
        return int(match.group(2).replace(",", "")), match.group(0)
    match = SOLD_EN_RE.search(text.replace(",", ""))
    if not match:
        return None, ""
    value = float(match.group(1))
    suffix = (match.group(2) or "").upper()
    if suffix == "K":
        value *= 1000
    elif suffix == "M":
        value *= 1_000_000
    elif suffix == "万":
        value *= 10000
    return int(value), match.group(0)


def parse_title(item: dict[str, Any]) -> str:
    title = str(item.get("title") or item.get("title_clean") or "").strip()
    title = TITLE_PREFIX_RE.sub("", title)
    if title and "新しいタブで開く" not in title:
        return title
    text = str(item.get("text") or "")
    text = re.sub(r"^AD\s+", "", text)
    text = re.sub(r"クイック ルック\s*", "", text)
    text = re.sub(r"一押し商品\s*", "", text)
    text = re.sub(r"新しいタブで開く。?\s*", "", text)
    text = re.sub(r"\s+\d[\d,]*円.*$", "", text)
    text = text.strip()
    if text:
        return text
    return product_name_from_url(str(item.get("href") or ""), str(item.get("goods_id") or ""))


def normalize_item(item: dict[str, Any]) -> dict[str, Any]:
    text = str(item.get("text") or "")
    sold_num = item.get("sold_num")
    sold_text = str(item.get("sold_text") or "")
    if sold_num in (None, ""):
        sold_num, sold_text = parse_sold_num(text)
    rating_match = RATING_JP_RE.search(text) or RATING_EN_RE.search(text)
    review_match = REVIEW_JP_RE.search(text) or REVIEW_EN_RE.search(text)
    listed_match = LISTED_JP_RE.search(text)
    goods_id = str(item.get("goods_id") or "")
    return {
        "goods_id": goods_id,
        "goods_id_num": int(goods_id),
        "title": parse_title(item),
        "title_clean": parse_title(item),
        "href": str(item.get("href") or ""),
        "price_yen": parse_price(text) if item.get("price_yen") in (None, "") else item.get("price_yen"),
        "sold_num": sold_num,
        "sold_text": sold_text,
        "rating": float(rating_match.group(1)) if rating_match else item.get("rating"),
        "reviews": int(str(review_match.group(1)).replace(",", "")) if review_match else item.get("reviews"),
        "listed_years_ago": int(listed_match.group(1)) if listed_match else item.get("listed_years_ago"),
        "source": item.get("source", "dom"),
    }


def load_raw_products_input(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        if isinstance(payload.get("raw_products"), list):
            return payload["raw_products"]
        value = payload.get("result", {}).get("value", payload)
        if isinstance(value, dict):
            for key in ("products", "all", "raw_products"):
                if isinstance(value.get(key), list):
                    return value[key]
    raise ValueError("Unsupported raw products input format")


def build_snapshot(
    raw_items: list[dict[str, Any]],
    store_url: str,
    *,
    captured_at: str | None = None,
    source: str,
    extra_collection: dict[str, Any] | None = None,
) -> dict[str, Any]:
    captured_at = captured_at or datetime.now(timezone.utc).astimezone().isoformat()
    mall_id = parse_mall_id(store_url)
    normalized = [normalize_item(item) for item in raw_items if item.get("goods_id")]
    normalized = [item for item in normalized if item["goods_id"]]
    normalized.sort(key=lambda row: int(row["goods_id"]), reverse=True)
    status = "OK" if normalized else "NO_PRODUCTS"
    collection = {"source": source, "product_count": len(normalized), "completeness": "PARTIAL"}
    if extra_collection:
        collection.update(extra_collection)
    return {
        "status": status,
        "captured_at": captured_at,
        "target": {"platform": "temu", "mall_id": mall_id, "store_url": canonical_mall_url(store_url)},
        "collection": collection,
        "raw_products": normalized,
    }


def render_report_md(analysis: dict[str, Any], snapshot: dict[str, Any]) -> str:
    lines = [
        f"# Temu Mall {analysis['target']['store_id']} 采集报告",
        "",
        f"- 采集时间: {analysis['captured_at']}",
        f"- mall_id: {analysis['target']['store_id']}",
        f"- 可见商品数: {analysis['snapshot_summary']['analyzable_count']}",
        f"- 完整度: {snapshot['collection'].get('completeness', 'PARTIAL')}",
        f"- 采集来源: {snapshot['collection'].get('source', 'unknown')}",
        f"- 销量异常阈值 (IQR 上界): {analysis['snapshot_summary']['sales_outlier_threshold']}",
        "",
        "## 最新上架候选 Top 10",
        "",
        "| # | goods_id | 销量 | 价格(JPY) | 商品名 |",
        "|---|----------|------|-----------|--------|",
    ]
    for index, item in enumerate(analysis["latest_listings"][:10], start=1):
        name = item["product_name"].replace("|", "/")[:70]
        lines.append(
            f"| {index} | {item['product_id']} | {item['sales']['value']} | {item['price']['amount']} | {name} |"
        )
    lines.extend(["", "## 销量异常", "", "| # | goods_id | 销量 | 阈值 | 商品名 |", "|---|----------|------|------|--------|"])
    for index, item in enumerate(analysis["abnormal_sales"], start=1):
        name = item["product_name"].replace("|", "/")[:70]
        lines.append(
            f"| {index} | {item['product_id']} | {item['sales']['value']} | {item['threshold']} | {name} |"
        )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- `latest_listings` 使用 goods_id 降序作为上新代理，置信度 INFERRED。",
            "- `abnormal_sales` 使用当前可见商品销量的 IQR 上界。",
            "- 建议定时重复本流水线，用差分确认真正新品与销量增速。",
        ]
    )
    return "\n".join(lines) + "\n"


def _extract_dom_products(page) -> list[dict[str, Any]]:
    return page.evaluate(DOM_EXTRACT_JS)


def _safe_extract_dom_products(page, retries: int = 3, wait_ms: int = 1000) -> list[dict[str, Any]]:
    last_error: Exception | None = None
    for _ in range(retries):
        try:
            return _extract_dom_products(page)
        except Exception as exc:
            last_error = exc
            page.wait_for_timeout(wait_ms)
    if last_error is not None:
        raise last_error
    return []


def default_playwright_profile_dir(root: Path | None = None) -> Path:
    if root is None:
        from app.config import PROFILE_ROOT

        return PROFILE_ROOT / "competitor-page-card"
    return root / "exports" / "ctf-website" / ".playwright-temu-profile"


def is_login_page(url: str, title: str) -> bool:
    lowered_url = url.lower()
    lowered_title = title.lower()
    return "login.html" in lowered_url or "로그인" in lowered_title or lowered_title.endswith("| login")


def recover_from_login_redirect(page, canonical_url: str) -> bool:
    current_url = page.url
    if "login.html" not in current_url.lower():
        return False
    parsed = urlparse(current_url)
    from_url = parse_qs(parsed.query).get("from", [""])[0]
    target = unquote(from_url) if from_url else canonical_url
    if not target:
        return False
    page.goto(target, wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(1200)
    page.evaluate(DISMISS_OVERLAYS_JS)
    page.keyboard.press("Escape")
    page.wait_for_timeout(600)
    return True


def wait_until_products_visible(page, canonical_url: str, *, timeout_ms: int, interactive: bool) -> int:
    if interactive:
        print(
            "\n[interactive] 浏览器已打开。\n"
            "1. 如看到登录弹窗，请手动关闭（或按 Esc）\n"
            "2. 确认页面出现商品卡片后，回到终端按 Enter 继续采集...\n",
            flush=True,
        )
        try:
            input()
        except EOFError:
            page.wait_for_timeout(min(timeout_ms, 15000))
        return page.evaluate("() => document.querySelectorAll('a[href*=\"-g-\"]').length")

    deadline = timeout_ms
    step = 1500
    elapsed = 0
    while elapsed < deadline:
        if recover_from_login_redirect(page, canonical_url):
            elapsed += step
            continue
        page.evaluate(DISMISS_OVERLAYS_JS)
        page.keyboard.press("Escape")
        count = page.evaluate("() => document.querySelectorAll('a[href*=\"-g-\"]').length")
        if count:
            return int(count)
        page.wait_for_timeout(step)
        elapsed += step
    return 0


def prepare_temu_page(page, canonical_url: str, *, wait_ms: int, interactive: bool, ready_timeout_ms: int) -> None:
    page.goto("https://www.temu.com/jp/", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(min(wait_ms, 2500))
    page.evaluate(DISMISS_OVERLAYS_JS)
    page.keyboard.press("Escape")
    page.goto(canonical_url, wait_until="domcontentloaded", timeout=90000)
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass
    page.wait_for_timeout(wait_ms)
    recover_from_login_redirect(page, canonical_url)
    page.evaluate(DISMISS_OVERLAYS_JS)
    page.keyboard.press("Escape")
    page.wait_for_timeout(800)
    wait_until_products_visible(page, canonical_url, timeout_ms=ready_timeout_ms, interactive=interactive)


def collect_with_playwright(
    store_url: str,
    *,
    headless: bool = False,
    scroll_rounds: int = 10,
    wait_ms: int = 1500,
    locale: str = "ja-JP",
    user_data_dir: str = "",
    storage_state: str = "",
    interactive: bool = False,
    use_default_profile: bool = True,
    ready_timeout_ms: int = 45000,
    profile_root: Path | None = None,
) -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    mall_id = parse_mall_id(store_url)
    canonical_url = canonical_mall_url(store_url)
    captured_at = datetime.now(timezone.utc).astimezone().isoformat()
    products: dict[str, dict[str, Any]] = {}
    profile_dir = user_data_dir or (str(default_playwright_profile_dir(profile_root)) if use_default_profile else "")
    storage_state_path = storage_state

    with sync_playwright() as playwright:
        browser = None
        if profile_dir:
            Path(profile_dir).mkdir(parents=True, exist_ok=True)
            context = playwright.chromium.launch_persistent_context(
                profile_dir,
                headless=headless,
                locale=locale,
                viewport={"width": 1440, "height": 2200},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                ),
            )
            page = context.pages[0] if context.pages else context.new_page()
        else:
            browser = playwright.chromium.launch(headless=headless)
            context_kwargs: dict[str, Any] = {
                "locale": locale,
                "viewport": {"width": 1440, "height": 2200},
                "user_agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                ),
            }
            if storage_state_path:
                context_kwargs["storage_state"] = storage_state_path
            context = browser.new_context(**context_kwargs)
            page = context.new_page()

        prepare_temu_page(
            page,
            canonical_url,
            wait_ms=wait_ms,
            interactive=interactive,
            ready_timeout_ms=ready_timeout_ms,
        )

        for _ in range(scroll_rounds):
            for item in _safe_extract_dom_products(page):
                goods_id = str(item["goods_id"])
                current = products.setdefault(goods_id, item)
                for key, value in item.items():
                    if value not in (None, ""):
                        current[key] = value
                current.setdefault("source", "dom")
            page.evaluate("window.scrollBy(0, Math.max(window.innerHeight, 900));")
            page.wait_for_timeout(wait_ms)

        title = page.title()
        current_url = page.url
        body_text = page.evaluate("() => (document.body && document.body.innerText) || ''")
        if browser is not None:
            browser.close()
        else:
            if profile_dir:
                storage_state_path = str(Path(profile_dir) / "storage-state.json")
                context.storage_state(path=storage_state_path)
            context.close()

    snapshot = build_snapshot(
        list(products.values()),
        canonical_url,
        captured_at=captured_at,
        source="playwright-dom",
        extra_collection={
            "page_title": title,
            "final_url": current_url,
            "scroll_rounds": scroll_rounds,
            "headless": headless,
            "locale": locale,
            "user_data_dir": profile_dir or None,
            "storage_state": storage_state_path or None,
            "interactive": interactive,
        },
    )
    if is_login_page(current_url, title):
        snapshot["status"] = "AUTH_REQUIRED"
        snapshot["collection"]["message"] = (
            "Temu redirected Playwright to login. Re-run with --interactive to manually dismiss the popup, "
            "or pass --input <browser-export.json>."
        )
        snapshot["collection"]["next_command"] = (
            "python backend/python/temu_mall_snapshot_pipeline.py "
            f'--store-url "{canonical_url}" --interactive'
        )
    elif any(token in body_text.lower() for token in ("captcha", "verify", "security check", "robot")):
        if snapshot["status"] == "OK":
            snapshot["collection"]["risk_hint"] = "LOGIN_OR_RISK_PAGE_DETECTED"
        else:
            snapshot["status"] = "RISK_BLOCKED"
    snapshot["target"]["mall_id"] = mall_id
    return snapshot


def _walk_api_payload(payload: Any, products: dict[str, dict[str, Any]]) -> None:
    if isinstance(payload, dict):
        goods_id = str(payload.get("goodsId") or payload.get("goods_id") or "").strip()
        if goods_id.isdigit():
            title = str(payload.get("goodsName") or payload.get("title") or payload.get("name") or "").strip()
            href = str(payload.get("linkUrl") or payload.get("link_url") or payload.get("seoLink") or "").strip()
            if href and not href.startswith("http"):
                href = "https://www.temu.com" + href
            if title or href:
                products.setdefault(
                    goods_id,
                    {
                        "goods_id": goods_id,
                        "goods_id_num": int(goods_id),
                        "title": title,
                        "title_clean": title,
                        "href": href,
                        "sold_num": payload.get("soldQuantity") or payload.get("soldNum"),
                        "sold_text": str(payload.get("soldText") or ""),
                        "price_yen": payload.get("minOnSalePrice") or payload.get("price"),
                        "rating": payload.get("goodsScore") or payload.get("rating"),
                        "reviews": payload.get("reviewNum") or payload.get("reviews"),
                        "source": "api",
                    },
                )
        for value in payload.values():
            _walk_api_payload(value, products)
    elif isinstance(payload, list):
        for value in payload:
            _walk_api_payload(value, products)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
