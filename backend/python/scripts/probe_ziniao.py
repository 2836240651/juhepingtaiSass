#!/usr/bin/env python3
"""探测紫鸟 WebDriver：启动开发者模式 → 拉取店铺列表。"""
from __future__ import annotations

import json
import sys

from app.ziniao.client import ZiniaoClient, ZiniaoConfig


def main() -> int:
    try:
        config = ZiniaoConfig.from_env()
    except ValueError as exc:
        print(f"配置错误: {exc}", file=sys.stderr)
        return 2

    client = ZiniaoClient(config)
    print(f"==> 企业: {config.company}")
    print(f"==> 账号: {config.username}")
    print(f"==> 端口: {config.socket_port}")

    print("==> 启动/检测紫鸟 WebDriver 模式...")
    try:
        client.ensure_webdriver_client(wait_seconds=20)
    except (FileNotFoundError, TimeoutError) as exc:
        print(f"失败: {exc}", file=sys.stderr)
        return 1

    print("==> 拉取店铺列表 getBrowserList ...")
    try:
        stores = client.get_browser_list()
    except RuntimeError as exc:
        print(f"失败: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(stores, ensure_ascii=False, indent=2))
    print(f"\n共 {len(stores)} 个紫鸟店铺")
    amazon = [
        s for s in stores
        if "amazon" in str(s.get("platform_name", "")).lower()
        or "亚马逊" in str(s.get("platform_name", ""))
    ]
    if amazon:
        print(f"其中 Amazon 相关: {len(amazon)} 个")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
