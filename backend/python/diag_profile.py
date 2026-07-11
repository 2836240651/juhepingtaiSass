#!/usr/bin/env python3
"""诊断 Temu 浏览器 Profile 登录/选店状态"""
from __future__ import annotations

import argparse
import json

from app.browser.context import describe_session, get_or_open_seller_page, open_temu_context
from app.config import resolve_tenant_id


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tenant-id", type=int, required=True)
    args = parser.parse_args()
    tenant_id = resolve_tenant_id(args.tenant_id)

    with open_temu_context(tenant_id) as (_, ctx):
        page = get_or_open_seller_page(ctx)
        page.wait_for_load_state("domcontentloaded", timeout=60_000)
        page.wait_for_timeout(2000)
        print(json.dumps(describe_session(page), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
