#!/usr/bin/env python3
"""Capture warehouse purchase order API from AE page."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.browser.aliexpress_context import open_aliexpress_context, wait_for_ae_login

WH_PAGE = "https://gsp.aliexpress.com/m_apps/ascp/aechoice.purchase_stockup_for_aechoice"


def main() -> None:
    tenant_id = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    hits: list[dict] = []

    with open_aliexpress_context(tenant_id, headless=True) as (_, ctx):
        page = ctx.new_page()

        def on_response(response) -> None:
            try:
                if response.status != 200:
                    return
                url = response.url
                if "scm-supplier" not in url and "purchase" not in url.lower():
                    return
                body = response.json()
                hits.append(
                    {
                        "url": url,
                        "method": response.request.method,
                        "post": (response.request.post_data or "")[:500],
                        "totalCount": body.get("totalCount"),
                        "data_len": len(body.get("data") or []),
                    }
                )
            except Exception:
                return

        page.on("response", on_response)
        page.goto(WH_PAGE, wait_until="domcontentloaded", timeout=120_000)
        wait_for_ae_login(page, tenant_id=tenant_id)
        page.wait_for_timeout(20_000)

    out = ROOT / "ae_warehouse_hits.json"
    out.write_text(json.dumps(hits, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"hits={len(hits)} saved={out}")
    for item in hits[:10]:
        print(item)


if __name__ == "__main__":
    main()
