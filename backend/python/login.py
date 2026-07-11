#!/usr/bin/env python3

"""手动登录 Temu 卖家后台（保留 Cookie 到租户隔离的浏览器配置）"""

from __future__ import annotations



import argparse

import json

import sys



from app.browser.context import (

    describe_session,

    ensure_logged_in,

    get_or_open_seller_page,

    open_temu_context,

)

from app.config import TEMU_SELLER_HOME, resolve_profile_dir, resolve_tenant_id





def main() -> None:

    parser = argparse.ArgumentParser(description="Temu 首次登录（按租户隔离 Profile）")

    parser.add_argument("--tenant-id", type=int, help="租户 ID（必填，或设置 TENANT_ID）")

    args = parser.parse_args()



    try:

        tenant_id = resolve_tenant_id(args.tenant_id)

    except ValueError as exc:

        print(f"错误: {exc}", file=sys.stderr)

        sys.exit(2)



    profile_dir = resolve_profile_dir(tenant_id)

    print("=" * 60)

    print("Temu 登录助手")

    print(f"租户 ID: {tenant_id}")

    print(f"浏览器配置目录: {profile_dir}")

    print()

    print("步骤：")

    print("  1. 在打开的 Chrome 中登录 Temu 卖家后台（手机号 + 验证码/密码）")

    print("  2. 登录成功后应进入 agentseller.temu.com 首页（不是 authentication 页）")

    print("  3. 若有多个店铺，在左上角切换到要同步的店铺")

    print("  4. 回到此窗口按 Enter 保存会话")

    print("=" * 60)



    with open_temu_context(tenant_id) as (_, context):

        page = context.new_page()

        page.goto(TEMU_SELLER_HOME, wait_until="domcontentloaded", timeout=120_000)

        try:

            input("\n完成登录并选好店铺后，按 Enter 继续...")

        except KeyboardInterrupt:

            print("\n已取消")

            sys.exit(1)



        active = page

        for candidate in reversed(context.pages):

            if "agentseller.temu.com" in (candidate.url or ""):

                active = candidate

                break

        page = active



        status = describe_session(page)

        print("\n当前会话状态：")

        print(json.dumps(status, ensure_ascii=False, indent=2))



        if status["requires_auth"]:

            print(

                "\n仍未登录：当前停留在认证页。请重新运行本脚本，在浏览器里完成登录后再按 Enter。",

                file=sys.stderr,

            )

            sys.exit(1)



        try:

            mall_id = ensure_logged_in(page)

        except RuntimeError as exc:

            print(f"\n{exc}", file=sys.stderr)

            sys.exit(1)



        mall_name = ""

        for mall in status.get("malls") or []:

            if str(mall.get("mallId")) == mall_id:

                mall_name = str(mall.get("mallName") or "")

                break



        label = f"{mall_name} ({mall_id})" if mall_name else mall_id

        print(f"\n已保存店铺会话: {label}")

        print(f"可运行: py crawl.py --tenant-id {tenant_id}")





if __name__ == "__main__":

    main()

