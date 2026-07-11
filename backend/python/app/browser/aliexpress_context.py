"""AliExpress 卖家后台浏览器上下文（持久化 Profile）。"""
from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Generator

from playwright.sync_api import BrowserContext, Page, Playwright, sync_playwright

from app.browser.context import _launch_kwargs, human_pause
from app.browser.stealth import STEALTH_INIT_SCRIPT
from app.config import (
    AE_CSP_HOME,
    AE_LOGIN_POLL_SECONDS,
    AE_LOGIN_WAIT_SECONDS,
    is_ae_headless,
    resolve_aliexpress_profile_dir,
)


def is_login_page(url: str) -> bool:
    lowered = (url or "").lower()
    return "login.aliexpress.com" in lowered or "/login" in lowered


def wait_for_ae_login(page: Page, *, tenant_id: int) -> None:
    deadline = time.time() + AE_LOGIN_WAIT_SECONDS
    while time.time() < deadline:
        url = page.url or ""
        if not is_login_page(url) and "aliexpress.com" in url.lower():
            human_pause()
            return
        if time.time() >= deadline:
            break
        time.sleep(AE_LOGIN_POLL_SECONDS)
    raise RuntimeError(
        f"AliExpress 卖家后台未登录（tenant={tenant_id}），"
        f"请先运行: py login_aliexpress.py --tenant-id {tenant_id}"
    )


@contextmanager
def open_aliexpress_context(
    tenant_id: int,
    *,
    headless: bool | None = None,
) -> Generator[tuple[Playwright, BrowserContext], None, None]:
    profile_dir = resolve_aliexpress_profile_dir(tenant_id)
    profile_dir.mkdir(parents=True, exist_ok=True)
    resolved_headless = is_ae_headless() if headless is None else headless

    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            str(profile_dir),
            **(_launch_kwargs(resolved_headless)),
        )
        context.add_init_script(STEALTH_INIT_SCRIPT)
        try:
            yield playwright, context
        finally:
            context.close()


def get_or_open_csp_page(context: BrowserContext) -> Page:
    for page in context.pages:
        if "aliexpress.com" in (page.url or ""):
            return page
    page = context.new_page()
    page.goto(AE_CSP_HOME, wait_until="domcontentloaded", timeout=120_000)
    return page
