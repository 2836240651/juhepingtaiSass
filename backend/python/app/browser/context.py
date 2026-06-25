"""持久化浏览器上下文：保留 Temu 登录态与店铺选择"""
from __future__ import annotations

import random
import time
from contextlib import contextmanager
from typing import Generator

from playwright.sync_api import BrowserContext, Page, Playwright, sync_playwright

from app.browser.stealth import BROWSER_ARGS, IGNORE_DEFAULT_ARGS, STEALTH_INIT_SCRIPT
from app.config import (
    BROWSER_CHANNEL,
    HEADLESS,
    MALL_STORAGE_KEY,
    MAX_ACTION_DELAY_MS,
    MIN_ACTION_DELAY_MS,
    PROFILE_DIR,
    TEMU_SELLER_HOME,
)


def human_pause() -> None:
    delay = random.randint(MIN_ACTION_DELAY_MS, MAX_ACTION_DELAY_MS) / 1000.0
    time.sleep(delay)


def _launch_kwargs() -> dict:
    kwargs: dict = {
        "headless": HEADLESS,
        "args": BROWSER_ARGS,
        "ignore_default_args": IGNORE_DEFAULT_ARGS,
        "viewport": {"width": 1280, "height": 900},
        "locale": "zh-CN",
        "timezone_id": "Asia/Shanghai",
        "user_agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        ),
    }
    if BROWSER_CHANNEL:
        kwargs["channel"] = BROWSER_CHANNEL
    return kwargs


@contextmanager
def open_temu_context() -> Generator[tuple[Playwright, BrowserContext], None, None]:
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            **{k: v for k, v in _launch_kwargs().items() if k != "headless"},
            headless=HEADLESS,
        )
        context.add_init_script(STEALTH_INIT_SCRIPT)
        try:
            yield p, context
        finally:
            context.close()


def get_or_open_seller_page(context: BrowserContext) -> Page:
    for page in context.pages:
        if "agentseller.temu.com" in (page.url or ""):
            return page
    page = context.new_page()
    page.goto(TEMU_SELLER_HOME, wait_until="domcontentloaded", timeout=120_000)
    human_pause()
    return page


def read_mall_id(page: Page) -> str:
    mall_id = page.evaluate(f"() => localStorage.getItem({MALL_STORAGE_KEY!r})")
    mall_id = (mall_id or "").strip()
    if not mall_id or mall_id in ("null", "undefined"):
        raise RuntimeError(
            f"未读取到店铺 ID（localStorage.{MALL_STORAGE_KEY}）。"
            "请先运行 py login.py 登录 Temu 卖家后台并选择店铺。"
        )
    return mall_id


def ensure_logged_in(page: Page) -> str:
    """打开卖家首页并确认已登录、已选店铺。"""
    if "agentseller.temu.com" not in (page.url or ""):
        page.goto(TEMU_SELLER_HOME, wait_until="domcontentloaded", timeout=120_000)
        human_pause()

    # 登录页特征
    if "/login" in (page.url or "") or "seller.kuajingmaihuo.com" in (page.url or ""):
        raise RuntimeError("Temu 未登录。请运行: py login.py")

    return read_mall_id(page)
