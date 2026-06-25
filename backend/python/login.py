#!/usr/bin/env python3
"""手动登录 Temu 卖家后台（保留 Cookie 到持久化浏览器配置）"""
from __future__ import annotations

import sys

from app.browser.context import open_temu_context
from app.config import MALL_STORAGE_KEY, PROFILE_DIR, TEMU_SELLER_HOME


def main() -> None:
    print("=" * 60)
    print("Temu 登录助手")
    print(f"浏览器配置目录: {PROFILE_DIR}")
    print("请在打开的浏览器中完成登录，并进入卖家后台选择店铺。")
    print("完成后回到此窗口按 Enter 保存会话并退出。")
    print("=" * 60)

    with open_temu_context() as (_, context):
        page = context.new_page()
        page.goto(TEMU_SELLER_HOME, wait_until="domcontentloaded", timeout=120_000)
        try:
            input("\n登录并选好店铺后，按 Enter 继续...")
        except KeyboardInterrupt:
            print("\n已取消")
            sys.exit(1)

        # 登录后页面可能会跳转，直接 evaluate 可能遇到 Execution context destroyed
        mall_id = None
        for _ in range(6):
            try:
                page.wait_for_load_state("domcontentloaded", timeout=30_000)
                mall_id = page.evaluate(f"() => localStorage.getItem({MALL_STORAGE_KEY!r})")
                if mall_id:
                    break
            except Exception:
                # 尝试用当前最活跃页面再读一次
                try:
                    page = context.pages[-1]
                except Exception:
                    pass

        print(f"当前店铺 ID: {mall_id or '(未检测到，请确认已选店铺)'}")

    print("会话已保存。可运行: py crawl.py")


if __name__ == "__main__":
    main()
