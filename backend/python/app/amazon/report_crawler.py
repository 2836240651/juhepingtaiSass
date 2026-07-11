"""Amazon 紫鸟 WebDriver 爬取（多 scope）。"""
from __future__ import annotations

import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from app.amazon.parsers.account_health import parse_seller_central_text
from app.amazon.parsers.seller_pages import (
    EXTRACT_AD_CAMPAIGNS_JS,
    EXTRACT_ADS_SUMMARY_JS,
    EXTRACT_BR_GRID_JS,
    EXTRACT_BUSINESS_REPORT_JS,
    EXTRACT_CATALOG_JS,
    EXTRACT_COUPONS_JS,
    EXTRACT_INVENTORY_JS,
    EXTRACT_MESSAGES_JS,
    EXTRACT_ORDERS_JS,
    EXTRACT_PERFORMANCE_TABLE_JS,
    EXTRACT_REVIEWS_JS,
    EXTRACT_SHIPMENTS_JS,
    parse_cases_from_text,
    parse_coupons_from_text,
    parse_reviews_from_text,
    parse_seller_news_from_text,
    parse_shipments_from_text,
)
from app.ziniao.client import ZiniaoClient, ZiniaoConfig

HOME_URL = "https://sellercentral.amazon.com/home"
ORDERS_URL = "https://sellercentral.amazon.com/orders-v3/unshipped"
MESSAGES_URL = "https://sellercentral.amazon.com/messaging/inbox"
REVIEWS_URL = "https://sellercentral.amazon.com/feedback-manager/index.html"
COUPON_URLS = [
    "https://sellercentral.amazon.com/seller-promotions/coupon/home",
    "https://sellercentral.amazon.com/promotions/manage",
    "https://sellercentral.amazon.com/promotions/list",
]
SHIPMENT_URLS = [
    "https://sellercentral.amazon.com/fba/inbound-shipment/summary",
    "https://sellercentral.amazon.com/fba/shippingqueue",
    "https://sellercentral.amazon.com/gp/fba/inbound-shipment-workflow/index.html",
]
REPORTS_URL = "https://sellercentral.amazon.com/business-reports/detail/sales-traffic-by-asin"
REPORT_URLS = [
    REPORTS_URL,
    "https://sellercentral.amazon.com/business-reports/detail/sales-traffic-by-asin?cols=%2F0%2F1",
]
INVENTORY_URLS = [
    "https://sellercentral.amazon.com/myinventory/inventory",
    "https://sellercentral.amazon.com/myinventory/inventory?fulfilledBy=all",
    "https://sellercentral.amazon.com/inventory",
    "https://sellercentral.amazon.com/inventoryplanning/manageinventoryhealth",
]
CATALOG_URLS = [HOME_URL, *INVENTORY_URLS, *REPORT_URLS]
ADS_URLS = [
    "https://advertising.amazon.com/cm/campaigns",
    "https://sellercentral.amazon.com/cm/campaigns",
    "https://sellercentral.amazon.com/ads/campaigns",
    "https://sellercentral.amazon.com/ads/reports",
]
HEALTH_URL = "https://sellercentral.amazon.com/performance/account/health"

CAPTURE_DIR = Path(__file__).resolve().parents[3] / "data" / "amazon-captures"

PRODUCT_SYNC_SCOPES = frozenset({"daily", "insights", "reports"})


class AmazonLoginRequiredError(RuntimeError):
    def __init__(self, message: str, *, capture_path: str = "") -> None:
        super().__init__(message)
        self.capture_path = capture_path


def _now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _extract_debug_port(start_result: dict[str, Any]) -> int:
    for key in ("debuggingPort", "debugPort", "debugging_port", "cdpPort", "port"):
        value = start_result.get(key)
        if value is not None and str(value).strip().isdigit():
            return int(str(value).strip())
    browser = start_result.get("browser")
    if isinstance(browser, dict):
        for key in ("debuggingPort", "debugPort", "debugging_port", "cdpPort", "port"):
            value = browser.get(key)
            if value is not None and str(value).strip().isdigit():
                return int(str(value).strip())
    raise RuntimeError(f"startBrowser 未返回 debuggingPort: {start_result!r}")


def _save_capture(page, *, store_name: str, suffix: str) -> str:
    CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^\w\-]+", "_", store_name or "amazon")[:40]
    path = CAPTURE_DIR / f"{safe_name}_{suffix}_{int(time.time())}.png"
    page.screenshot(path=str(path), full_page=True)
    return str(path)


def _looks_logged_in(body_text: str, url: str) -> bool:
    body = body_text or ""
    lowered = body.lower()
    if "/home" in (url or "") and ("全局快照" in body or "global snapshot" in lowered):
        return True
    if "账户状况" in body or "account health" in lowered:
        return True
    if "seller central" in lowered or "卖家平台" in body:
        return "sign in" not in lowered and "sign-in" not in lowered
    return False


def _require_seller_logged_in(page, body_text: str, *, store_name: str = "") -> None:
    if _looks_login_page(body_text, page.url):
        capture = _save_capture(page, store_name=store_name, suffix="login")
        raise AmazonLoginRequiredError(
            f"Amazon 卖家后台未登录，截图: {capture}",
            capture_path=capture,
        )
    if not _looks_logged_in(body_text, page.url):
        capture = _save_capture(page, store_name=store_name, suffix="login")
        raise AmazonLoginRequiredError(
            f"Amazon 卖家后台会话无效，请在紫鸟中重新登录 Seller Central。截图: {capture}",
            capture_path=capture,
        )


def _annotate_product_sync(result: dict[str, Any], scope: str) -> None:
    if scope not in PRODUCT_SYNC_SCOPES:
        return
    products = result.get("products") or []
    if products:
        result["product_sync_warning"] = ""
        return
    capture_path = str(result.get("capture_path") or "").strip()
    if capture_path:
        result["product_sync_warning"] = "NO_ASIN_ROWS"
        return
    result["product_sync_warning"] = "NO_ASIN_ROWS"


def _looks_login_page(body_text: str, url: str) -> bool:
    body = body_text or ""
    lowered = body.lower()
    if "sign in" in lowered or "sign-in" in lowered:
        return "seller central" not in lowered and "卖家平台" not in body
    if "登录" in body and "账户状况" not in body and "全局快照" not in body:
        return True
    if "/ap/signin" in (url or "").lower():
        return True
    return False


def _goto(page, url: str, wait_ms: int = 10000) -> str:
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_timeout(wait_ms)
    return page.inner_text("body")


def _crawl_page_list(page, url: str, js: str, text_parser, wait_ms: int = 12000, scroll: bool = False) -> list:
    try:
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(wait_ms)
        if scroll:
            page.evaluate("() => { window.scrollTo(0, document.body.scrollHeight); }")
            page.wait_for_timeout(2500)
        body = page.inner_text("body")
        if _looks_login_page(body, page.url):
            return []
        rows = page.evaluate(js) or []
        if isinstance(rows, list) and rows:
            return rows
        return text_parser(body) if text_parser else []
    except Exception:
        return []


def _crawl_first_match(page, urls: list[str], js: str, text_parser, wait_ms: int = 12000, scroll: bool = False) -> list:
    for url in urls:
        rows = _crawl_page_list(page, url, js, text_parser, wait_ms, scroll)
        if rows:
            return rows
    return []


_STATUS_ONLY_RE = re.compile(
    r"^(在售|停售|缺货|active|inactive|out of stock|–|-)$",
    re.I,
)
_ASIN_RE = re.compile(r"^[A-Z0-9]{10}$", re.I)


def _parse_money_text(value: Any) -> float:
    if value is None:
        return 0.0
    cleaned = re.sub(r"[^\d.-]", "", str(value))
    try:
        return float(cleaned) if cleaned else 0.0
    except ValueError:
        return 0.0


def _has_product_activity(raw: dict[str, Any]) -> bool:
    revenue = _parse_money_text(raw.get("revenue_30d") or raw.get("revenue7d"))
    orders = _parse_money_text(raw.get("orders_30d") or raw.get("orders7d"))
    inventory = _parse_money_text(raw.get("inventory") or raw.get("units_on_hand"))
    return revenue > 0 or orders > 0 or inventory > 0


def is_valid_product_row(raw: dict[str, Any]) -> bool:
    asin = str(raw.get("asin") or "").strip().upper()
    if not _ASIN_RE.match(asin):
        return False
    name = str(raw.get("product_name") or raw.get("productName") or "").strip()
    if not name or _STATUS_ONLY_RE.match(name):
        return False
    return _has_product_activity(raw) or len(name) >= 6


def filter_valid_product_rows(products: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in products if isinstance(row, dict) and is_valid_product_row(row)]


def _format_money_str(value: Any) -> str:
    amount = _parse_money_text(value)
    if amount <= 0:
        return ""
    return f"{amount:,.2f}"


def _enrich_product_rows(products: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for raw in products:
        if not isinstance(raw, dict) or not is_valid_product_row(raw):
            continue
        row = dict(raw)
        revenue = _parse_money_text(row.get("revenue_30d"))
        spend = _parse_money_text(row.get("ad_spend_30d"))
        if revenue > 0:
            row["revenue_30d"] = _format_money_str(revenue)
        if spend > 0:
            row["ad_spend_30d"] = _format_money_str(spend)
        acos_raw = row.get("acos")
        try:
            acos = float(str(acos_raw).replace("%", "").strip()) if acos_raw not in (None, "") else 0.0
        except ValueError:
            acos = 0.0
        if acos <= 0 and spend > 0 and revenue > 0:
            acos = round(spend / revenue * 100, 1)
            row["acos"] = acos
        if not row.get("tacos") and acos > 0:
            row["tacos"] = acos
        enriched.append(row)
    return enriched


def _merge_campaign_ads_into_products(
    products: list[dict[str, Any]],
    campaigns: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not products or not campaigns:
        return products
    merged = [dict(item) for item in products if isinstance(item, dict)]
    for campaign in campaigns:
        if not isinstance(campaign, dict):
            continue
        spend = _parse_money_text(campaign.get("ad_spend_30d"))
        if spend <= 0:
            continue
        asin = str(campaign.get("asin") or "").strip().upper()
        campaign_name = str(campaign.get("campaign_name") or "").strip().lower()
        acos_raw = campaign.get("acos")
        try:
            acos = float(str(acos_raw).replace("%", "").strip()) if acos_raw not in (None, "") else 0.0
        except ValueError:
            acos = 0.0

        target = None
        if asin:
            target = next((p for p in merged if str(p.get("asin") or "").upper() == asin), None)
        if target is None and campaign_name:
            for product in merged:
                name = str(product.get("product_name") or "").strip().lower()
                if len(name) >= 6 and name in campaign_name:
                    target = product
                    break
        if target is None and len(merged) == 1:
            target = merged[0]

        if target is None:
            continue
        existing_spend = _parse_money_text(target.get("ad_spend_30d"))
        total_spend = existing_spend + spend
        target["ad_spend_30d"] = _format_money_str(total_spend)
        revenue = _parse_money_text(target.get("revenue_30d"))
        if acos > 0:
            target["acos"] = acos
        elif revenue > 0 and total_spend > 0:
            target["acos"] = round(total_spend / revenue * 100, 1)
        if not target.get("tacos") and target.get("acos"):
            target["tacos"] = target["acos"]
    return merged


def _evaluate_js(page, js: str) -> list:
    try:
        rows = page.evaluate(js) or []
        if isinstance(rows, list) and rows:
            return rows
    except Exception:
        pass
    for frame in page.frames:
        try:
            rows = frame.evaluate(js) or []
            if isinstance(rows, list) and rows:
                return rows
        except Exception:
            continue
    return []


def _click_report_apply(page) -> None:
    try:
        page.evaluate(
            """
            () => {
              const nodes = [...document.querySelectorAll('button, kat-button, input[type=submit]')];
              const btn = nodes.find((node) => /apply|应用|run report|刷新|更新|generate/i.test(
                (node.innerText || node.value || '').trim()
              ));
              if (btn) btn.click();
            }
            """
        )
        page.wait_for_timeout(6000)
    except Exception:
        pass


def _crawl_ads_data(page) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    summary: dict[str, Any] = {}
    campaigns: list[dict[str, Any]] = []
    seen_campaigns: set[str] = set()
    for url in ADS_URLS:
        try:
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_timeout(14000)
            body = page.inner_text("body")
            if _looks_login_page(body, page.url):
                continue
            if not summary.get("ad_spend_30d") and not summary.get("acos"):
                candidate = page.evaluate(EXTRACT_ADS_SUMMARY_JS) or {}
                if isinstance(candidate, dict):
                    for key, value in candidate.items():
                        if value and not summary.get(key):
                            summary[key] = value
            rows = _evaluate_js(page, EXTRACT_AD_CAMPAIGNS_JS)
            for row in rows:
                if not isinstance(row, dict):
                    continue
                key = str(row.get("asin") or row.get("campaign_name") or "")
                if key and key in seen_campaigns:
                    continue
                if key:
                    seen_campaigns.add(key)
                campaigns.append(row)
        except Exception:
            continue
    return summary, campaigns


def _crawl_business_report(page, *, store_name: str = "") -> list[dict[str, Any]]:
    for url in REPORT_URLS:
        try:
            page.goto(url, wait_until="domcontentloaded")
            try:
                page.wait_for_load_state("networkidle", timeout=35000)
            except Exception:
                pass
            _click_report_apply(page)
            page.wait_for_timeout(8000)
            for selector in ("table tbody tr", "kat-table", "[role='grid']"):
                try:
                    page.wait_for_selector(selector, timeout=12000)
                    break
                except Exception:
                    continue
            page.evaluate("() => { window.scrollTo(0, document.body.scrollHeight); }")
            page.wait_for_timeout(3000)
            body = page.inner_text("body")
            if _looks_login_page(body, page.url):
                continue
            if not re.search(r"(sales|traffic|asin|销售额|流量|ordered product|business report)", body, re.I):
                _save_capture(page, store_name=store_name, suffix="br_nodata")
                continue
            rows = _evaluate_js(page, EXTRACT_BR_GRID_JS)
            if not rows:
                rows = _evaluate_js(page, EXTRACT_BUSINESS_REPORT_JS)
            if not rows:
                rows = _evaluate_js(page, EXTRACT_CATALOG_JS)
            valid = filter_valid_product_rows(rows)
            if valid:
                return valid
            if rows:
                _save_capture(page, store_name=store_name, suffix="br_invalid")
            else:
                _save_capture(page, store_name=store_name, suffix="br_nodata")
        except Exception:
            continue
    return []


def _crawl_inventory_products(page, *, store_name: str = "") -> list[dict[str, Any]]:
    for url in INVENTORY_URLS:
        try:
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_timeout(12000)
            body = page.inner_text("body")
            if _looks_login_page(body, page.url):
                continue
            rows = _evaluate_js(page, EXTRACT_INVENTORY_JS)
            if not rows:
                rows = _evaluate_js(page, EXTRACT_CATALOG_JS)
            valid = filter_valid_product_rows(rows)
            if valid:
                return valid
            if rows:
                _save_capture(page, store_name=store_name, suffix="inv_invalid")
        except Exception:
            continue
    return []


def _crawl_catalog_products(page, *, store_name: str = "") -> list[dict[str, Any]]:
    for url in CATALOG_URLS:
        try:
            page.goto(url, wait_until="domcontentloaded")
            try:
                page.wait_for_load_state("networkidle", timeout=25000)
            except Exception:
                pass
            if url in REPORT_URLS:
                _click_report_apply(page)
            page.wait_for_timeout(8000)
            page.evaluate("() => { window.scrollTo(0, document.body.scrollHeight); }")
            page.wait_for_timeout(2500)
            body = page.inner_text("body")
            if _looks_login_page(body, page.url):
                continue
            rows = _evaluate_js(page, EXTRACT_CATALOG_JS)
            if not rows and url in REPORT_URLS:
                rows = _evaluate_js(page, EXTRACT_BUSINESS_REPORT_JS)
            valid = filter_valid_product_rows(rows)
            if valid:
                return valid
            if rows:
                _save_capture(page, store_name=store_name, suffix="catalog_invalid")
        except Exception:
            continue
    return []


def _merge_product_catalog(
    primary: list[dict[str, Any]],
    fallback: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for row in [*fallback, *primary]:
        if not isinstance(row, dict):
            continue
        asin = str(row.get("asin") or "").strip().upper()
        if not asin:
            continue
        current = merged.get(asin, {})
        combined = {**current, **row, "asin": asin}
        if not combined.get("product_name") and current.get("product_name"):
            combined["product_name"] = current["product_name"]
        if not combined.get("revenue_30d") and current.get("revenue_30d"):
            combined["revenue_30d"] = current["revenue_30d"]
        merged[asin] = combined
    return list(merged.values())[:50]


def _crawl_operational_lists(page) -> tuple[list, list]:
    coupons = _crawl_first_match(
        page,
        COUPON_URLS,
        EXTRACT_COUPONS_JS,
        parse_coupons_from_text,
        14000,
    )
    shipments = _crawl_first_match(
        page,
        SHIPMENT_URLS,
        EXTRACT_SHIPMENTS_JS,
        parse_shipments_from_text,
        14000,
        scroll=True,
    )
    return coupons, shipments


def _merge_ads_metrics(metrics: list[dict[str, Any]], ads_summary: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(ads_summary, dict):
        return metrics
    merged = list(metrics)
    seen = {item.get("metric_key") for item in merged if isinstance(item, dict)}
    spend = ads_summary.get("ad_spend_30d") or ads_summary.get("adSpend30d")
    if spend and "ad_spend_today" not in seen:
        merged.append(
            {
                "metric_key": "ad_spend_today",
                "metric_label": "广告花费（广告后台）",
                "value_text": f"US${spend}",
                "threshold_text": "",
                "status": "normal",
                "trend": "stable",
                "note_text": "来自广告活动页",
            }
        )
    acos = ads_summary.get("acos")
    if acos and "ad_acos_snapshot" not in seen:
        merged.append(
            {
                "metric_key": "ad_acos_snapshot",
                "metric_label": "广告 ACOS",
                "value_text": f"{acos}%",
                "threshold_text": "",
                "status": "normal",
                "trend": "stable",
                "note_text": "来自广告活动页",
            }
        )
    return merged


def crawl_amazon(
    *,
    scope: str = "account_health",
    browser_id: str = "",
    browser_oauth: str = "",
    store_name: str = "",
) -> dict[str, Any]:
    if not browser_id and not browser_oauth:
        raise ValueError("缺少 browser_id 或 browser_oauth")

    normalized_scope = (scope or "account_health").strip().lower()
    ziniao = ZiniaoClient(ZiniaoConfig.from_env())
    ziniao.ensure_webdriver_client(wait_seconds=20)

    start_result = ziniao.start_browser(
        browser_id=browser_id or None,
        browser_oauth=browser_oauth or None,
    )
    debug_port = _extract_debug_port(start_result)

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("缺少 playwright，请执行 pip install -r backend/python/requirements.txt") from exc

    result: dict[str, Any] = {
        "synced_at": _now_text(),
        "metrics": [],
        "products": [],
        "outbound_orders": [],
        "buyer_messages": [],
        "reviews": [],
        "coupons": [],
        "seller_news": [],
        "shipments": [],
        "cases": [],
        "page_url": "",
        "capture_path": "",
    }

    with sync_playwright() as playwright:
        browser = playwright.chromium.connect_over_cdp(f"http://127.0.0.1:{debug_port}")
        try:
            context = browser.contexts[0] if browser.contexts else browser.new_context()
            page = context.pages[0] if context.pages else context.new_page()
            page.set_default_timeout(90000)

            home_text = _goto(page, HOME_URL)
            result["page_url"] = page.url
            _require_seller_logged_in(page, home_text, store_name=store_name)

            if normalized_scope in {"account_health", "daily", "insights", "reports"}:
                result["metrics"] = parse_seller_central_text(home_text)
                if normalized_scope in {"daily", "insights"}:
                    result["seller_news"] = parse_seller_news_from_text(home_text)
                    result["cases"] = parse_cases_from_text(home_text)

            if normalized_scope in {"daily", "insights", "reports"}:
                home_products: list[dict[str, Any]] = []
                try:
                    home_products = filter_valid_product_rows(_evaluate_js(page, EXTRACT_CATALOG_JS))
                except Exception:
                    home_products = []

                report_products = _crawl_business_report(page, store_name=store_name)
                inventory_products = _crawl_inventory_products(page, store_name=store_name)
                report_products = _merge_product_catalog(
                    _merge_product_catalog(report_products, inventory_products),
                    home_products,
                )
                if not report_products:
                    report_products = _crawl_catalog_products(page, store_name=store_name)
                if report_products:
                    result["products"] = _enrich_product_rows(report_products)

            if normalized_scope in {"insights", "reports", "daily"}:
                ads_summary, ad_campaigns = _crawl_ads_data(page)
                if ads_summary:
                    result["metrics"] = _merge_ads_metrics(result.get("metrics") or [], ads_summary)
                if ad_campaigns and result.get("products"):
                    result["products"] = _merge_campaign_ads_into_products(
                        result.get("products") or [],
                        ad_campaigns,
                    )

            if normalized_scope in {"daily", "reports"}:
                coupons, shipments = _crawl_operational_lists(page)
                if coupons:
                    result["coupons"] = coupons
                if shipments:
                    result["shipments"] = shipments

            if normalized_scope == "reports":
                try:
                    _goto(page, ORDERS_URL, 8000)
                    orders = page.evaluate(EXTRACT_ORDERS_JS) or []
                    if isinstance(orders, list):
                        result["outbound_orders"] = orders
                except Exception:
                    pass

            if normalized_scope == "daily":
                try:
                    msg_text = _goto(page, MESSAGES_URL, 8000)
                    if not _looks_login_page(msg_text, page.url):
                        messages = page.evaluate(EXTRACT_MESSAGES_JS) or []
                        if isinstance(messages, list) and messages:
                            result["buyer_messages"] = messages
                except Exception:
                    pass
                try:
                    page.goto(REVIEWS_URL, wait_until="domcontentloaded")
                    page.wait_for_timeout(15000)
                    rev_text = page.inner_text("body")
                    if not _looks_login_page(rev_text, page.url):
                        reviews = page.evaluate(EXTRACT_REVIEWS_JS) or []
                        if isinstance(reviews, list) and reviews:
                            result["reviews"] = reviews
                        else:
                            result["reviews"] = parse_reviews_from_text(rev_text)
                except Exception:
                    pass
                if not result["cases"]:
                    result["cases"] = parse_cases_from_text(home_text)
                if not result.get("coupons") or not result.get("shipments"):
                    coupons, shipments = _crawl_operational_lists(page)
                    if coupons and not result.get("coupons"):
                        result["coupons"] = coupons
                    if shipments and not result.get("shipments"):
                        result["shipments"] = shipments

            if normalized_scope in {"daily", "insights"}:
                try:
                    _goto(page, ORDERS_URL, 8000)
                    orders = page.evaluate(EXTRACT_ORDERS_JS) or []
                    if isinstance(orders, list):
                        result["outbound_orders"] = orders
                except Exception:
                    pass

            if normalized_scope == "account_health" and not result["metrics"]:
                health_text = _goto(page, HEALTH_URL, 8000)
                result["metrics"] = parse_seller_central_text(health_text)

            if not _looks_logged_in(home_text, HOME_URL) and not result["metrics"] and not result["products"]:
                capture = _save_capture(page, store_name=store_name, suffix="empty")
                raise RuntimeError(f"卖家平台页面未解析到数据，截图: {capture}")

            if normalized_scope == "account_health" and not result["metrics"]:
                capture = _save_capture(page, store_name=store_name, suffix="empty")
                raise RuntimeError(f"未解析到账户状况指标，截图: {capture}")

            _annotate_product_sync(result, normalized_scope)
            if result.get("product_sync_warning") == "NO_ASIN_ROWS" and not result.get("capture_path"):
                latest = sorted(CAPTURE_DIR.glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
                if latest:
                    result["capture_path"] = str(latest[0])

            return result
        finally:
            try:
                browser.close()
            except Exception:
                pass
            try:
                ziniao.stop_browser(
                    browser_id=browser_id or None,
                    browser_oauth=browser_oauth or None,
                )
            except Exception:
                pass


def crawl_account_health(**kwargs: Any) -> dict[str, Any]:
    return crawl_amazon(scope="account_health", **kwargs)
