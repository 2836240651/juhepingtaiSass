#!/usr/bin/env python3
from __future__ import annotations

import json
import urllib.error
import urllib.request


BASE = "http://127.0.0.1:18080"


def request(method: str, path: str, token: str | None = None, body: dict | None = None) -> tuple[int, dict | str]:
    data = None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            return exc.code, json.loads(raw)
        except Exception:
            return exc.code, raw


def main() -> None:
    status, payload = request(
        "POST",
        "/api/auth/login",
        body={"account": "admin@crosshub.cn", "password": "12345678", "portal_role": "boss"},
    )
    print("login", status)
    if status != 200 or not isinstance(payload, dict) or "data" not in payload:
        print("login failed payload:", payload)
        return
    token = (payload.get("data") or {}).get("token")
    if not token:
        print("login token missing:", payload)
        return

    checks = [
        ("GET", "/api/temu/shops", None),
        ("GET", "/api/temu/session", None),
        ("POST", "/api/temu/login/open", {}),
        ("GET", "/api/temu/operational", None),
        ("GET", "/api/amazon/sp-api/status", None),
        ("GET", "/api/amazon/integration/status", None),
        ("GET", "/api/amazon/daily", None),
        ("GET", "/api/amazon/insights", None),
        ("GET", "/api/aliexpress/operational", None),
        ("GET", "/api/aliexpress/orders/today", None),
        ("GET", "/api/aliexpress/violations", None),
        ("GET", "/api/aliexpress/hot-broadcasts", None),
        ("POST", "/api/aliexpress/crawl", {"report_time": None}),
    ]
    failures = []
    for method, path, body in checks:
        s, p = request(method, path, token=token, body=body)
        code = p.get("code") if isinstance(p, dict) else None
        ok = s < 500 and (code in (0, 200, None) or s in (202,))
        print(f"{method} {path} -> http={s} code={code} {'OK' if ok else 'FAIL'}")
        if not ok:
            failures.append(f"{method} {path}")

    if failures:
        print("FAILED endpoints:", ", ".join(failures))
        return
    print("ALL smoke checks passed")


if __name__ == "__main__":
    main()

