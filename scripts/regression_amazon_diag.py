#!/usr/bin/env python3
"""Amazon 回归诊断：服务、DB、同步任务、产品快照。"""
from __future__ import annotations

import json
import sqlite3
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "backend" / "data" / "crosshub.db"
CAPTURE_DIR = ROOT / "backend" / "data" / "amazon-captures"


def http_get(url: str, headers: dict | None = None, timeout: int = 8) -> tuple[int, str]:
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")[:2000]
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:2000]
        return exc.code, body
    except Exception as exc:  # noqa: BLE001
        return -1, str(exc)


def main() -> None:
    print("=== Amazon Regression Diagnostics ===")
    print("time:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    for url in (
        "http://localhost:5173/",
        "http://localhost:18080/actuator/health",
        "http://127.0.0.1:18765/health",
    ):
        code, body = http_get(url)
        print(f"\n[HTTP] {url} -> {code}")
        if body:
            print(body[:300].replace("\n", " "))

    if not DB.exists():
        print("\n[DB] missing:", DB)
        return

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    print("\n[DB] amazon_product_snapshot count:", conn.execute(
        "select count(*) from amazon_product_snapshot"
    ).fetchone()[0])

    rows = conn.execute(
        """
        select asin, product_name, revenue_30d, orders_30d, synced_at
        from amazon_product_snapshot
        order by synced_at desc, rank_no asc
        limit 5
        """
    ).fetchall()
    if rows:
        print("[DB] sample products:")
        for r in rows:
            print(dict(r))
    else:
        print("[DB] no product rows")

    print("\n[DB] active sync jobs:")
    for r in conn.execute(
        """
        select id, scope, status, started_at, finished_at, substr(coalesce(error_message,''),1,120) err
        from amazon_sync_job
        where status in ('pending','running')
        order by started_at desc
        """
    ):
        print(dict(r))

    print("\n[DB] latest sync jobs:")
    for r in conn.execute(
        """
        select id, scope, status, started_at, finished_at, substr(coalesce(error_message,''),1,120) err
        from amazon_sync_job
        order by started_at desc
        limit 6
        """
    ):
        print(dict(r))

    print("\n[DB] running agent tasks:")
    for r in conn.execute(
        """
        select id, status, task_type, created_at, started_at, finished_at,
               substr(coalesce(error_message,''),1,120) err
        from agent_task
        where status='running'
        order by created_at desc
        """
    ):
        print(dict(r))

    task = conn.execute(
        """
        select id, status, result_json, error_message, finished_at
        from agent_task
        where task_type='amazon_sync'
        order by created_at desc
        limit 1
        """
    ).fetchone()
    if task:
        print("\n[DB] latest amazon_sync agent_task:", task["id"], task["status"], task["finished_at"])
        if task["error_message"]:
            print("  err:", task["error_message"][:200])
        if task["result_json"]:
            try:
                data = json.loads(task["result_json"])
                products = data.get("products") or []
                metrics = data.get("metrics") or []
                print("  result products:", len(products))
                print("  result metrics:", len(metrics))
                if products:
                    print("  first product:", json.dumps(products[0], ensure_ascii=False)[:240])
            except json.JSONDecodeError as exc:
                print("  result_json parse error:", exc)

    agents = conn.execute(
        """
        select id, name, status, last_heartbeat_at, ziniao_online
        from integration_agent
        order by last_heartbeat_at desc
        limit 3
        """
    ).fetchall()
    print("\n[DB] agents:")
    for r in agents:
        print(dict(r))

    accounts = conn.execute(
        """
        select id, store_name, platform, integration_mode, external_shop_id
        from platform_account
        where lower(platform)='amazon'
        order by bound_at desc
        limit 5
        """
    ).fetchall()
    print("\n[DB] amazon accounts:")
    for r in accounts:
        print(dict(r))

    captures = sorted(CAPTURE_DIR.glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)[:8]
    print("\n[CAPTURE] latest screenshots:", len(captures))
    for p in captures:
        print(" ", p.name, datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"))


if __name__ == "__main__":
    main()
