#!/usr/bin/env python3
"""Probe previously timing-out endpoints and check for long-running AliExpress crawl jobs."""
from __future__ import annotations

import json
import sqlite3
import urllib.error
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:18080"
DB = Path(__file__).resolve().parents[1] / "backend" / "data" / "crosshub.db"
TIMEOUT = 25


def request(method: str, path: str, token: str | None, body: dict | None = None, timeout: int = TIMEOUT) -> tuple[int, dict | str, float]:
    import time

    data = None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            elapsed = time.perf_counter() - started
            return resp.status, json.loads(raw) if raw else {}, elapsed
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        elapsed = time.perf_counter() - started
        try:
            return exc.code, json.loads(raw), elapsed
        except Exception:
            return exc.code, raw, elapsed
    except Exception as exc:
        elapsed = time.perf_counter() - started
        return 0, str(exc), elapsed


def login() -> str:
    status, payload, _ = request(
        "POST",
        "/api/auth/login",
        "",
        body={"account": "admin@crosshub.cn", "password": "12345678", "portal_role": "boss"},
    )
    if status != 200 or not isinstance(payload, dict):
        raise RuntimeError(f"login failed: {status} {payload}")
    token = (payload.get("data") or {}).get("token")
    if not token:
        raise RuntimeError(f"login token missing: {payload}")
    return token


def main() -> int:
    token = login()
    probes = [
        ("GET", "/api/temu/session", None),
        ("POST", "/api/temu/login/open", {}),
        ("POST", "/api/temu/competitors/discover", {"keyword": "fishing", "region": "za", "limit": 3}),
        ("GET", "/api/amazon/integration/status", None),
        ("GET", "/api/monitor/targets", None),
    ]
    failures = []
    for method, path, body in probes:
        probe_timeout = 95 if path.endswith("/competitors/discover") else TIMEOUT
        status, payload, elapsed = request(method, path, token, body, timeout=probe_timeout)
        code = payload.get("code") if isinstance(payload, dict) else None
        timed_out = elapsed >= probe_timeout - 0.5 or status == 0
        ok = not timed_out and status < 500 and (
            code in (0, 200, None)
            or (path.endswith("/competitors/discover") and status == 400)
        )
        print(f"{method} {path} -> http={status} code={code} elapsed={elapsed:.2f}s {'OK' if ok else 'FAIL'}")
        if not ok:
            failures.append(path)

    if not DB.exists():
        print(f"WARN: db missing at {DB}")
    else:
        conn = sqlite3.connect(DB)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, status, started_at, created_at
            FROM aliexpress_crawl_job
            WHERE status IN ('pending', 'running')
              AND (
                (status = 'running' AND started_at != '' AND datetime(started_at) < datetime('now', '-6 minutes'))
                OR (status = 'pending' AND created_at != '' AND datetime(created_at) < datetime('now', '-6 minutes'))
              )
            ORDER BY created_at DESC
            LIMIT 20
            """
        ).fetchall()
        conn.close()
        if rows:
            print("STALE AliExpress jobs (>6 min):")
            for row in rows:
                print(dict(row))
            failures.append("aliexpress_stale_running_jobs")
        else:
            print("No stale AliExpress crawl jobs (pending/running >6 min)")

    if failures:
        print("REGRESSION FAIL:", ", ".join(failures))
        return 1
    print("REGRESSION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
