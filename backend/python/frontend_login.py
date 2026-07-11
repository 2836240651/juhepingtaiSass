#!/usr/bin/env python3
"""Manual login helper for Temu buyer/front-end pages.

This intentionally does not reuse login.py because login.py is scoped to the
seller backend. The browser profile is still tenant-isolated, so competitor
crawls can reuse the saved front-end cookies and verification state.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

from app.browser.context import close_tenant_profile_browsers, human_pause, open_temu_context
from app.config import resolve_profile_dir, resolve_tenant_id

DEFAULT_FRONTEND_URL = "https://www.temu.com/"
DEFAULT_CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]


def is_frontend_blocked(url: str) -> bool:
    normalized = (url or "").lower()
    return (
        "/login.html" in normalized
        or "login_scene=" in normalized
        or "bgn_verification" in normalized
        or "verification" in normalized
        or "challenge" in normalized
    )


def is_temu_frontend_url(url: str) -> bool:
    host = (urlparse(url or "").hostname or "").lower()
    return host == "www.temu.com" or host.endswith(".temu.com")


def describe_frontend_page(page) -> dict:
    cookies = page.context.cookies("https://www.temu.com/")
    cookie_names = sorted({cookie.get("name", "") for cookie in cookies if cookie.get("name")})
    text = ""
    try:
        body = page.locator("body")
        if body.count():
            text = body.inner_text(timeout=5_000)[:500]
    except Exception:
        text = ""
    return {
        "url": page.url,
        "title": page.title(),
        "is_temu_frontend": is_temu_frontend_url(page.url),
        "requires_login_or_verification": is_frontend_blocked(page.url),
        "cookie_count": len(cookies),
        "cookie_names": cookie_names[:30],
        "body_preview": text,
    }


def find_chrome_executable() -> str:
    env_path = os.getenv("CHROME_PATH", "").strip()
    candidates = [env_path] if env_path else []
    candidates.extend(DEFAULT_CHROME_PATHS)
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return candidate
    return "chrome"


def run_manual_chrome_login(tenant_id: int, url: str, profile_dir: Path, *, json_only: bool) -> None:
    chrome = find_chrome_executable()
    profile_dir.mkdir(parents=True, exist_ok=True)
    close_tenant_profile_browsers(tenant_id)
    command = [
        chrome,
        f"--user-data-dir={profile_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-session-crashed-bubble",
        "--new-window",
        url,
    ]

    if not json_only:
        print("\nOpening normal Chrome for Temu front-end login...")
        print("Important:")
        print("  1. Use the opened Chrome window to finish Temu/Google login or verification.")
        print("  2. Confirm the page returns to www.temu.com and is no longer about:blank/login/verification.")
        print("  3. Close that Chrome window completely.")
        print("  4. Come back here and press Enter.")

    process = subprocess.Popen(command)
    try:
        input("\nClose the Chrome login window after success, then press Enter...")
    except KeyboardInterrupt:
        print("\nCancelled", file=sys.stderr)
        sys.exit(1)

    if process.poll() is None:
        print(
            "\nChrome is still running with the tenant profile. Close it before running competitor crawl.",
            file=sys.stderr,
        )
        sys.exit(1)

    if not json_only:
        print(f"\nSaved Temu front-end browser profile for tenant {tenant_id}: {profile_dir}")
        print("You can now run competitor crawl or click analysis in the app.")


def run_playwright_login(tenant_id: int, url: str, *, json_only: bool) -> None:
    profile_dir = resolve_profile_dir(tenant_id)
    if not json_only:
        print("\nOpening Playwright-controlled Chrome for Temu front-end login...")

    with open_temu_context(tenant_id) as (_, context):
        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=120_000)
        human_pause()

        try:
            input("\nPress Enter after front-end login/verification is complete...")
        except KeyboardInterrupt:
            print("\nCancelled", file=sys.stderr)
            sys.exit(1)

        active = page
        for candidate in reversed(context.pages):
            if is_temu_frontend_url(candidate.url or ""):
                active = candidate
                break

        status = describe_frontend_page(active)
        if json_only:
            print(json.dumps(status, ensure_ascii=False))
        else:
            print("\nCurrent front-end session:")
            print(json.dumps(status, ensure_ascii=False, indent=2))

        if not status["is_temu_frontend"]:
            print("\nNot on a Temu front-end page. Please rerun and complete login on www.temu.com.", file=sys.stderr)
            sys.exit(1)
        if status["requires_login_or_verification"]:
            print("\nStill on login/verification. Please complete it before pressing Enter.", file=sys.stderr)
            sys.exit(1)

        if not json_only:
            print(f"\nSaved Temu front-end session. You can now run competitor crawl for tenant {tenant_id}.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Temu front-end login helper")
    parser.add_argument("--tenant-id", type=int, help="Tenant ID, or TENANT_ID env")
    parser.add_argument(
        "--url",
        default=DEFAULT_FRONTEND_URL,
        help="Temu front-end URL to open, default: https://www.temu.com/",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the final session status as JSON only at the end",
    )
    parser.add_argument(
        "--mode",
        choices=("manual", "playwright"),
        default="manual",
        help="manual opens normal Chrome for OAuth; playwright keeps the old controlled-browser flow",
    )
    parser.add_argument(
        "--open-only",
        action="store_true",
        help="Open normal Chrome with the tenant profile and exit immediately; used by Java API prompts",
    )
    args = parser.parse_args()

    try:
        tenant_id = resolve_tenant_id(args.tenant_id)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(2)

    profile_dir = resolve_profile_dir(tenant_id)
    if args.open_only:
        profile_dir = resolve_profile_dir(tenant_id)
        profile_dir.mkdir(parents=True, exist_ok=True)
        close_tenant_profile_browsers(tenant_id)
        command = [
            find_chrome_executable(),
            f"--user-data-dir={profile_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-session-crashed-bubble",
            "--new-window",
            args.url,
        ]
        subprocess.Popen(command)
        result = {
            "tenant_id": tenant_id,
            "profile_dir": str(profile_dir),
            "url": args.url,
            "opened": True,
        }
        if args.json:
            print(json.dumps(result, ensure_ascii=False))
        else:
            print(f"Opened Temu front-end login window for tenant {tenant_id}: {args.url}")
        return

    if not args.json:
        print("=" * 72)
        print("Temu front-end login helper")
        print(f"Tenant ID: {tenant_id}")
        print(f"Browser profile: {profile_dir}")
        print(f"Open URL: {args.url}")
        print(f"Mode: {args.mode}")
        print()
        print("Steps:")
        if args.mode == "manual":
            print("  1. Complete Temu buyer-side login or verification in the opened normal Chrome window.")
            print("  2. Make sure the page is back on www.temu.com and no longer on about:blank/login/verification.")
            print("  3. Close that Chrome window completely so the profile is unlocked.")
            print("  4. Return to this terminal and press Enter.")
        else:
            print("  1. Complete Temu buyer-side login or verification in the opened Chrome window.")
            print("  2. Make sure the page is back on www.temu.com and no longer on login/verification.")
            print("  3. Return to this terminal and press Enter to save the session.")
        print("=" * 72)

    if args.mode == "manual":
        run_manual_chrome_login(tenant_id, args.url, profile_dir, json_only=args.json)
    else:
        run_playwright_login(tenant_id, args.url, json_only=args.json)


if __name__ == "__main__":
    main()
