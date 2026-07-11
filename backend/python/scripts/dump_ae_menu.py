#!/usr/bin/env python3
"""Dump CSP menu links for order discovery."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.browser.aliexpress_context import open_aliexpress_context, wait_for_ae_login
from app.config import AE_CSP_HOME


def walk(items: list, out: list) -> None:
    for item in items or []:
        name = str(item.get("name") or "")
        link = str(item.get("link") or "")
        if link:
            out.append((name, link))
        walk(item.get("menu") or item.get("children") or item.get("subMenu") or [], out)


def main() -> None:
    tenant_id = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    menu_body = None

    with open_aliexpress_context(tenant_id, headless=True) as (_, ctx):
        page = ctx.new_page()

        def on_response(response) -> None:
            nonlocal menu_body
            try:
                if "menu.get" in response.url and response.status == 200:
                    menu_body = response.json()
            except Exception:
                return

        page.on("response", on_response)
        page.goto(AE_CSP_HOME, wait_until="domcontentloaded", timeout=120_000)
        wait_for_ae_login(page, tenant_id=tenant_id)
        page.wait_for_timeout(8000)

    links: list[tuple[str, str]] = []
    if menu_body:
        data = menu_body.get("data")
        if isinstance(data, str):
            data = json.loads(data)
        module = (data or {}).get("module") or data or {}
        walk(module.get("leftMenu") or [], links)
        walk(module.get("headMenu") or [], links)

    keywords = ("订单", "order", "Order", "销售", "履约", "发货", "入库", "采购", "JIT", "仓")
    for name, link in links:
        text = f"{name} {link}"
        if any(key in text for key in keywords):
            print(f"{name}\t{link}")


if __name__ == "__main__":
    main()
