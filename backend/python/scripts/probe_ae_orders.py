#!/usr/bin/env python3
"""Capture all mtop payloads on AE order page and find order rows."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.browser.aliexpress_context import open_aliexpress_context, wait_for_ae_login
from app.config import AE_ORDER_PAGE

ORDER_MARKERS = (
    "tradeOrder",
    "orderId",
    "orderNo",
    "buyerName",
    "productName",
    "orderStatus",
    "fulfillment",
    "order_id",
    "order_no",
)


def main() -> None:
    tenant_id = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    hits: list[dict] = []

    with open_aliexpress_context(tenant_id, headless=True) as (_, ctx):
        page = ctx.new_page()

        def on_response(response) -> None:
            try:
                if response.status != 200 or "mtop" not in response.url:
                    return
                body = response.json()
                text = json.dumps(body, ensure_ascii=False)
                if any(marker in text for marker in ORDER_MARKERS):
                    hits.append({"url": response.url, "body": body})
            except Exception:
                return

        page.on("response", on_response)
        page.goto(AE_ORDER_PAGE, wait_until="domcontentloaded", timeout=120_000)
        wait_for_ae_login(page, tenant_id=tenant_id)
        page.wait_for_timeout(12_000)

        for text in ("今日", "近7天", "待发货", "待出库", "全部", "查询", "搜索", "刷新"):
            try:
                page.get_by_text(text, exact=False).first.click(timeout=1500)
                page.wait_for_timeout(2500)
            except Exception:
                pass

        script_urls = page.evaluate(
            """() => Array.from(document.scripts).map(s => s.src).filter(Boolean)"""
        )
        order_scripts = [u for u in script_urls if "order" in u.lower()][:10]

        out = ROOT / "ae_mtop_hits.json"
        out.write_text(json.dumps(hits, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"hits={len(hits)} saved={out}")
        for item in hits[:5]:
            api = item["body"].get("api")
            print("api", api)
            print(json.dumps(item["body"], ensure_ascii=False)[:500])
            print("---")
        print("order scripts", order_scripts[:5])


if __name__ == "__main__":
    main()
