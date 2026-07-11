"""
Temu 全托管运营数据爬虫

Playwright 持久化浏览器 + 卖家后台 API（与 Commander Agent 同路径）
"""
from __future__ import annotations

import time
from datetime import date

from app.browser.context import (
    close_tenant_profile_browsers,
    ensure_logged_in,
    get_or_open_seller_page,
    open_temu_context,
    wait_for_login_and_mall,
)
from app.browser.profile_lock import (
    clear_profile_lock,
    is_profile_locked,
    read_session_cache,
    write_session_cache,
)
from app.browser.session_state import cache_payload_from_status, session_ready
from app.config import is_headless
from app.crawler.mapper import map_sales_batches
from app.crawler.temu_api import TemuApiClient


def ensure_profile_available(tenant_id: int, *, timeout_seconds: int = 30) -> None:
    cached = read_session_cache(tenant_id, max_age_seconds=1800)
    if cached and session_ready(cached) and is_profile_locked(tenant_id):
        close_tenant_profile_browsers(tenant_id)
        clear_profile_lock(tenant_id)
        time.sleep(1)
        return

    deadline = time.monotonic() + max(0, timeout_seconds)
    while is_profile_locked(tenant_id) and time.monotonic() < deadline:
        time.sleep(2)

    if is_profile_locked(tenant_id):
        cached = read_session_cache(tenant_id, max_age_seconds=1800)
        if cached and session_ready(cached):
            close_tenant_profile_browsers(tenant_id)
            clear_profile_lock(tenant_id)
            time.sleep(1)
            return
        raise RuntimeError(
            "Temu 登录窗口仍在使用中。请关闭 CrossHub 弹出的登录浏览器，再点击「刷新数据」。"
        )


def crawl_temu_sales_live(report_day: str | None = None, *, tenant_id: int = 1) -> dict:
    report_time = report_day or date.today().isoformat()
    cached = read_session_cache(tenant_id, max_age_seconds=1800)

    ensure_profile_available(tenant_id)
    close_tenant_profile_browsers(tenant_id)

    with open_temu_context(tenant_id, headless=is_headless()) as (_, context):
        page = get_or_open_seller_page(context)
        if cached and session_ready(cached):
            mall_id = ensure_logged_in(page)
        else:
            mall_id = wait_for_login_and_mall(
                page,
                tenant_id=tenant_id,
                timeout_seconds=90,
                on_poll=lambda status: write_session_cache(
                    tenant_id,
                    cache_payload_from_status(tenant_id, status),
                ),
            )
        client = TemuApiClient(page)
        shop_name, shop_id = client.get_shop_info()
        batches = client.fetch_all_sales()
        rows = map_sales_batches(
            batches,
            shop_id=shop_id,
            shop_name=shop_name,
            report_time=report_time,
            tenant_id=tenant_id,
        )
        shops = [{"shop_id": shop_id, "shop_name": shop_name, "is_upload": True, "tenant_id": tenant_id}]
        write_session_cache(
            tenant_id,
            cache_payload_from_status(tenant_id, {
                "logged_in": True,
                "mall_id": mall_id,
                "mall_count": 1,
                "requires_auth": False,
            }),
        )
        return {"report_time": report_time, "shops": shops, "rows": rows}


def crawl_temu_sales(report_day: str | None = None, *, use_seed: bool = False, tenant_id: int = 1) -> dict:
    if use_seed:
        raise RuntimeError("种子数据模式已关闭，请完成 Temu 登录后使用真实爬取")
    return crawl_temu_sales_live(report_day, tenant_id=tenant_id)
