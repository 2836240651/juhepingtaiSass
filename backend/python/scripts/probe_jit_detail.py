#!/usr/bin/env python3
"""Probe JIT detail API for price fields."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.browser.aliexpress_context import open_aliexpress_context, get_or_open_csp_page, wait_for_ae_login
from app.crawler.aliexpress_api import AliExpressApiClient

DETAIL_API = "https://scm-supplier.aliexpress.com/dchain-seller-portal-ae/popChoicePackage/queryListV2"


def main() -> None:
    tenant_id = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    with open_aliexpress_context(tenant_id, headless=True) as (_, ctx):
        page = get_or_open_csp_page(ctx)
        wait_for_ae_login(page, tenant_id=tenant_id)
        client = AliExpressApiClient(page)
        rows = client.fetch_jit_consign_orders("2026-07-08")
        print("jit_rows", len(rows))
        if not rows:
            return
        sample = rows[0]
        print("keys", sorted(sample.keys()))
        print("items_keys", sorted((sample.get("items") or [{}])[0].keys()) if sample.get("items") else [])
        po = sample.get("purchaseOrderNo") or sample.get("consignOrderNo")
        client.ensure_session()
        payload = client._post_form(
            DETAIL_API,
            {
                "_scm_token_": client._scm_token,
                "purchaseOrderNos": po,
                "pageIndex": 1,
                "pageSize": 10,
            },
            referer="https://gsp.aliexpress.com/m_apps/ascp/aechoice.purchase_jit_order_list",
        )
        print("detail_total", payload.get("totalCount"))
        print(json.dumps((payload.get("data") or [])[:1], ensure_ascii=False, indent=2)[:4000])


if __name__ == "__main__":
    main()
