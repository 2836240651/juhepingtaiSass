"""Discover crawlable Temu competitor candidates from front-end search pages."""
from __future__ import annotations

from collections import OrderedDict
from urllib.parse import parse_qs, quote, urlparse

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from app.browser.context import close_tenant_profile_browsers, human_pause, open_temu_context
from app.crawler.competitor_crawler import (
    extract_name,
    extract_price,
    extract_sales_signal,
    is_browser_profile_error,
    is_temu_frontend_blocked,
    page_contains_store_unavailable,
)

DEFAULT_DISCOVERY_KEYWORD = "fishing tackle"
DEFAULT_DISCOVERY_REGION = "za"
DEFAULT_DISCOVERY_LIMIT = 10


def build_search_url(keyword: str = DEFAULT_DISCOVERY_KEYWORD, region: str = DEFAULT_DISCOVERY_REGION) -> str:
    normalized_region = (region or DEFAULT_DISCOVERY_REGION).strip().strip("/") or DEFAULT_DISCOVERY_REGION
    normalized_keyword = (keyword or DEFAULT_DISCOVERY_KEYWORD).strip() or DEFAULT_DISCOVERY_KEYWORD
    return f"https://www.temu.com/{normalized_region}/search_result.html?search_key={quote(normalized_keyword)}"


def discover_competitor_candidates(
    *,
    tenant_id: int,
    keyword: str = DEFAULT_DISCOVERY_KEYWORD,
    region: str = DEFAULT_DISCOVERY_REGION,
    limit: int = DEFAULT_DISCOVERY_LIMIT,
) -> dict:
    search_url = build_search_url(keyword, region)
    close_tenant_profile_browsers(tenant_id)
    try:
        items = discover_raw_items(tenant_id, search_url, max_items=max(limit * 4, 24))
    except RuntimeError as exc:
        message = str(exc)
        if message.startswith("COMPETITOR_"):
            raise
        if is_browser_profile_error(message):
            items = retry_discovery_after_closing_profile(tenant_id, search_url, max_items=max(limit * 4, 24), original=exc)
        else:
            raise RuntimeError(f"COMPETITOR_CRAWL_FAILED: {message or 'Competitor discovery failed'}") from exc
    except Exception as exc:
        message = str(exc)
        if is_browser_profile_error(message):
            items = retry_discovery_after_closing_profile(tenant_id, search_url, max_items=max(limit * 4, 24), original=exc)
        else:
            raise RuntimeError(f"COMPETITOR_CRAWL_FAILED: {message or 'Competitor discovery failed'}") from exc

    candidates = build_discovery_candidates(items, search_url=search_url, keyword=keyword, limit=limit)
    if not candidates:
        raise RuntimeError(
            "COMPETITOR_DISCOVERY_NO_RESULTS: No fishing tackle candidates were found on Temu ZA. "
            "Try again later or use a manual competitor URL."
        )
    return {
        "keyword": keyword,
        "region": region,
        "searchUrl": search_url,
        "candidates": candidates,
    }


def discover_raw_items(tenant_id: int, search_url: str, *, max_items: int) -> list[dict]:
    with open_temu_context(tenant_id, headless=True) as (_, context):
        page = context.new_page()
        return extract_search_items_from_url(page, search_url, max_items=max_items)


def retry_discovery_after_closing_profile(tenant_id: int, search_url: str, *, max_items: int, original: Exception) -> list[dict]:
    close_tenant_profile_browsers(tenant_id)
    try:
        return discover_raw_items(tenant_id, search_url, max_items=max_items)
    except Exception as exc:
        message = str(exc)
        if message.startswith("COMPETITOR_"):
            raise
        if is_browser_profile_error(message):
            raise RuntimeError(
                "COMPETITOR_BROWSER_PROFILE_UNAVAILABLE: Temu buyer-side browser profile could not be opened after force-closing tenant browser windows."
            ) from exc
        raise RuntimeError(f"COMPETITOR_CRAWL_FAILED: {message or str(original) or 'Competitor discovery failed'}") from exc


def extract_search_items_from_url(page: Page, url: str, *, max_items: int = 40) -> list[dict]:
    if is_temu_frontend_blocked(url):
        raise RuntimeError(
            "COMPETITOR_FRONTEND_LOGIN_REQUIRED: Temu frontend login or verification is required before discovering competitors."
        )
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=35_000)
    except PlaywrightTimeoutError as exc:
        raise RuntimeError(
            "COMPETITOR_NAVIGATION_TIMEOUT: Timed out opening the Temu discovery search page."
        ) from exc
    human_pause()
    if is_temu_frontend_blocked(page.url):
        raise RuntimeError(
            "COMPETITOR_FRONTEND_LOGIN_REQUIRED: Temu frontend login or verification is required before discovering competitors."
        )
    if page_contains_store_unavailable(page):
        raise RuntimeError("COMPETITOR_STORE_UNAVAILABLE: Temu reports this discovery page is unavailable in the current region/session.")
    try:
        page.wait_for_load_state("networkidle", timeout=8_000)
    except Exception:
        pass

    for _ in range(2):
        page.mouse.wheel(0, 900)
        human_pause()

    return extract_search_items_from_page(page, max_items=max_items)


def extract_search_items_from_page(page: Page, *, max_items: int = 40) -> list[dict]:
    return page.evaluate(
        """
        ({ maxItems }) => {
          const anchors = Array.from(document.querySelectorAll('a[href]'));
          const seen = new Set();
          const rows = [];
          const productHints = /(goods|product|item|sku|_oak|\\bg-\\d|\\bpd-\\d)/i;
          const pricePattern = /(?:US)?\\$\\s*\\d|(?:^|\\s)R\\s*\\d/i;
          const textOf = (node) => ((node && (node.innerText || node.textContent)) || '')
            .replace(/[ \\t]+/g, ' ')
            .trim();
          const cardTextFor = (anchor) => {
            let node = anchor;
            let best = textOf(anchor);
            for (let depth = 0; node && depth < 7; depth += 1) {
              const current = textOf(node);
              if (current && pricePattern.test(current) && current.length >= best.length) {
                return current;
              }
              if (current.length > best.length && current.length < 1200) best = current;
              node = node.parentElement;
            }
            return best;
          };
          const mallLinkFor = (anchor) => {
            let node = anchor;
            for (let depth = 0; node && depth < 7; depth += 1) {
              const mallLink = node.querySelector && node.querySelector('a[href*="mall_id"], a[href*="mall.html"]');
              if (mallLink && mallLink.href) return mallLink.href;
              node = node.parentElement;
            }
            return '';
          };
          for (const anchor of anchors) {
            const href = anchor.href || anchor.getAttribute('href') || '';
            const cardText = cardTextFor(anchor);
            if (!href || seen.has(href)) continue;
            if (!productHints.test(href) && !pricePattern.test(cardText)) continue;
            if (cardText.length < 12 || !pricePattern.test(cardText)) continue;
            seen.add(href);
            rows.push({ url: href, text: cardText, mallUrl: mallLinkFor(anchor) });
            if (rows.length >= maxItems) break;
          }
          return rows;
        }
        """,
        {"maxItems": max_items},
    ) or []


def build_discovery_candidates(
    items: list[dict],
    *,
    search_url: str,
    keyword: str,
    limit: int = DEFAULT_DISCOVERY_LIMIT,
) -> list[dict]:
    grouped: OrderedDict[str, dict] = OrderedDict()
    fallback_products: list[dict] = []

    for item in items or []:
        product = normalize_sample_product(item)
        if not product["name"] or product["price"] <= 0:
            continue
        mall_id = mall_id_from_item(item)
        if not mall_id:
            fallback_products.append(product)
            continue
        key = f"mall:{mall_id}"
        if key not in grouped:
            grouped[key] = {
                "label": product["name"],
                "url": mall_url(mall_id),
                "sourceType": "shop",
                "sourceKeyword": keyword,
                "sampleProducts": [],
            }
        grouped[key]["sampleProducts"].append(product)

    candidates = list(grouped.values())
    if not candidates and fallback_products:
        candidates.append(
            {
                "label": f"{keyword} 搜索结果候选源",
                "url": search_url,
                "sourceType": "search",
                "sourceKeyword": keyword,
                "sampleProducts": fallback_products[: min(len(fallback_products), 10)],
            }
        )

    result = []
    for rank, candidate in enumerate(candidates[:limit], start=1):
        samples = candidate["sampleProducts"][:5]
        result.append(
            {
                "rank": rank,
                "label": candidate["label"][:80],
                "url": candidate["url"],
                "host": host_of(candidate["url"]),
                "sourceKeyword": candidate["sourceKeyword"],
                "sourceType": candidate["sourceType"],
                "sampleProductCount": len(candidate["sampleProducts"]),
                "sampleProducts": samples,
                "crawlable": bool(samples),
            }
        )
    return result


def normalize_sample_product(item: dict) -> dict:
    text = item.get("text", "")
    url = item.get("url", "")
    return {
        "name": extract_name(text, "Temu fishing product"),
        "url": url,
        "price": extract_price(text),
        "salesSignal": extract_sales_signal(text),
    }


def mall_id_from_item(item: dict) -> str:
    for url in (item.get("mallUrl", ""), item.get("url", "")):
        parsed = urlparse(url or "")
        query = parse_qs(parsed.query)
        for key in ("mall_id", "mallId", "mallid"):
            values = query.get(key)
            if values and values[0]:
                return values[0][:80]
    return ""


def mall_url(mall_id: str) -> str:
    return f"https://www.temu.com/mall.html?mall_id={mall_id}"


def host_of(url: str) -> str:
    try:
        return urlparse(url).hostname or ""
    except Exception:
        return ""
