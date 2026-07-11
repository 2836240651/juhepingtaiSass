#!/usr/bin/env python3
"""Capture JIT page network for price/detail APIs."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.browser.aliexpress_context import open_aliexpress_context, wait_for_ae_login
from app.config import AE_JIT_ORDER_PAGE

PRICE_MARKERS = ("price", "amount", "fee", "settle", "supply", "单价", "金额", "售价")


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
                lowered = url.lower()
                if "scm-supplier" not in lowered and "dchain" not in lowered:
                    return
                body = response.json()
                text = json.dumps(body, ensure_ascii=False)
                if any(marker in text.lower() for marker in PRICE_MARKERS) or any(
                    marker in url for marker in ("queryListV2", "trade", "package", "settle")
                ):
                    hits.append({"url": url, "method": response.request.method, "sample": text[:1500]})
            except Exception:
                return

        page.on("response", on_response)
        page.goto(AE_JIT_ORDER_PAGE, wait_until="domcontentloaded", timeout=120_000)
        wait_for_ae_login(page, tenant_id=tenant_id)
        page.wait_for_timeout(25_000)

    out = ROOT / "ae_jit_price_hits.json"
    out.write_text(json.dumps(hits, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"hits={len(hits)} saved={out}")
    for item in hits[:10]:
        print(item["url"])
        print(item["sample"][:400])
        print("---")


if __name__ == "__main__":
    main()
