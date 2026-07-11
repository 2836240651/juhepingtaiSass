#!/usr/bin/env python3
"""Probe JIT consign orders API response."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.browser.aliexpress_context import open_aliexpress_context, wait_for_ae_login

JIT_PAGE = "https://gsp.aliexpress.com/m_apps/ascp/aechoice.purchase_jit_order_list"


def main() -> None:
    tenant_id = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    jit_resp = {}

    with open_aliexpress_context(tenant_id, headless=True) as (_, ctx):
        page = ctx.new_page()

        def on_response(response) -> None:
            if "queryJitConsignOrders" not in response.url or response.status != 200:
                return
            try:
                jit_resp["body"] = response.json()
            except Exception:
                return

        page.on("response", on_response)
        page.goto(JIT_PAGE, wait_until="domcontentloaded", timeout=120_000)
        wait_for_ae_login(page, tenant_id=tenant_id)
        page.wait_for_timeout(25_000)

    body = jit_resp.get("body") or {}
    print("totalCount", body.get("totalCount"))
    print(json.dumps((body.get("data") or [])[:2], ensure_ascii=False, indent=2)[:3000])


if __name__ == "__main__":
    main()
