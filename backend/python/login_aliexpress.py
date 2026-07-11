#!/usr/bin/env python3
"""AliExpress 卖家后台首次登录：python login_aliexpress.py --tenant-id 1"""
from __future__ import annotations

import argparse
import sys

from app.browser.aliexpress_context import get_or_open_csp_page, open_aliexpress_context
from app.config import resolve_tenant_id


def main() -> None:
    parser = argparse.ArgumentParser(description="AliExpress 卖家后台登录（有头浏览器）")
    parser.add_argument("--tenant-id", type=int, help="租户 ID")
    args = parser.parse_args()

    try:
        tenant_id = resolve_tenant_id(args.tenant_id)
    except ValueError as exc:
        print(f"错误: {exc}", file=sys.stderr)
        sys.exit(2)

    print(f"正在打开 AliExpress 卖家后台登录窗口（tenant={tenant_id}）...")
    print("请在浏览器中完成登录后关闭窗口。")

    with open_aliexpress_context(tenant_id, headless=False) as (_, context):
        page = get_or_open_csp_page(context)
        page.wait_for_timeout(300_000)

    print("登录窗口已关闭，Profile 已保存。")


if __name__ == "__main__":
    main()
