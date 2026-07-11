"""E2E: HangZhouYiTuo tenant — Ziniao discover, bind Amazon, sync."""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
JAVA = os.environ.get("JAVA_API_URL", "http://localhost:18080")
ACCOUNT = "HangZhouYiTuo"
PASSWORD = "HangZhouYiTuo"
POLL = 3
MAX_WAIT = 300


def login() -> tuple[str, int]:
    res = requests.post(
        f"{JAVA}/api/auth/login",
        json={"account": ACCOUNT, "password": PASSWORD, "portalRole": "boss"},
        timeout=30,
    )
    res.raise_for_status()
    body = res.json()
    if body.get("code") not in (0, None) and not body.get("success", True):
        raise RuntimeError(f"login failed: {body}")
    data = body.get("data") or body
    token = data.get("token") or data.get("access_token")
    tenant_id = int(data.get("tenant_id") or 0)
    if not token:
        raise RuntimeError(f"no token: {body}")
    return token, tenant_id


def hdr(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def get_json(token: str, path: str) -> dict:
    r = requests.get(f"{JAVA}{path}", headers=hdr(token), timeout=60)
    r.raise_for_status()
    return r.json()


def post_json(token: str, path: str, payload: dict | None = None) -> dict:
    r = requests.post(f"{JAVA}{path}", headers=hdr(token), json=payload or {}, timeout=120)
    r.raise_for_status()
    return r.json()


def wait_job(token: str, path: str, label: str) -> dict:
    deadline = time.time() + MAX_WAIT
    while time.time() < deadline:
        body = get_json(token, path)
        job = body.get("data") or body
        status = job.get("status")
        print(f"  [{label}] status={status}")
        if status == "success":
            return job
        if status == "failed":
            raise RuntimeError(f"{label} failed: {job.get('error_message') or job}")
        time.sleep(POLL)
    raise TimeoutError(f"{label} timeout")


def ensure_agent(token: str) -> str:
    status = (get_json(token, "/api/amazon/integration/status").get("data") or {})
    if status.get("agent_online"):
        print("Agent already online for this tenant")
        nodes = get_json(token, "/api/agent/nodes").get("data") or []
        if nodes:
            return ""
    reg = post_json(token, "/api/agent/register", {"name": "HangZhou Agent"})
    data = reg.get("data") or reg
    agent_token = data.get("agent_token") or data.get("token")
    if not agent_token:
        raise RuntimeError(f"register agent failed: {reg}")
    print(f"Registered agent token: {agent_token[:12]}...")
    env_path = ROOT / "backend" / "python" / ".env"
    text = env_path.read_text(encoding="utf-8")
    if "AGENT_TOKEN=" in text:
        lines = []
        for line in text.splitlines():
            if line.startswith("AGENT_TOKEN="):
                lines.append(f"AGENT_TOKEN={agent_token}")
            else:
                lines.append(line)
        env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Updated backend/python/.env AGENT_TOKEN — restart Agent manually if needed")
    return agent_token


def main() -> int:
    print("=== 1. Login HangZhouYiTuo ===")
    token, tenant_id = login()
    print(f"tenant_id={tenant_id}")

    print("\n=== 2. Integration status ===")
    before = get_json(token, "/api/amazon/integration/status").get("data") or {}
    print(json.dumps(before, ensure_ascii=False, indent=2))

    print("\n=== 3. Register Agent (if needed) ===")
    agent_token = ensure_agent(token)

    if not before.get("agent_online"):
        print("\nNOTE: Agent offline — restart with scripts/run-agent.ps1 after token update")
        status2 = get_json(token, "/api/amazon/integration/status").get("data") or {}
        if not status2.get("agent_online"):
            print("Waiting 15s for agent heartbeat...")
            time.sleep(15)
            status2 = get_json(token, "/api/amazon/integration/status").get("data") or {}
        print("status after wait:", json.dumps(status2, ensure_ascii=False))
        if not status2.get("agent_online"):
            print("ERROR: Agent still offline. Start agent and re-run from step 4.")
            return 2

    print("\n=== 4. Ziniao discover ===")
    discover = post_json(token, "/api/amazon/ziniao/discover")
    job_id = (discover.get("data") or discover).get("job_id") or (discover.get("data") or discover).get("task_id")
    if not job_id:
        raise RuntimeError(f"no discover job id: {discover}")
    job = wait_job(token, f"/api/amazon/ziniao/discover/{job_id}", "discover")
    stores = job.get("stores") or []
    print(f"discovered {len(stores)} browsers")
    for s in stores[:5]:
        print(" ", s.get("browser_name") or s.get("browserName"), s.get("browser_id") or s.get("browserId"))

    candidates = get_json(token, "/api/amazon/ziniao/candidates").get("data") or []
    amazon = [
        c for c in candidates
        if "amazon" in str(c.get("platform_name") or c.get("platformName") or "").lower()
        or "amazon" in str(c.get("browser_name") or c.get("browserName") or "").lower()
    ]
    if not amazon:
        amazon = candidates
    if not amazon:
        print("No ziniao candidates — check WebDriver / 紫鸟 login")
        return 3

    print(f"\n=== 5. Bind {len(amazon)} Amazon store(s) ===")
    bind_payload = {
        "stores": [
            {
                "browser_id": c.get("browser_id") or c.get("browserId"),
                "browser_oauth": c.get("browser_oauth") or c.get("browserOauth") or "",
                "browser_name": c.get("browser_name") or c.get("browserName") or "",
                "platform_name": c.get("platform_name") or c.get("platformName") or "Amazon",
                "store_username": c.get("store_username") or c.get("storeUsername") or "",
                "browser_ip": c.get("browser_ip") or c.get("browserIp") or "",
            }
            for c in amazon[:3]
        ]
    }
    bound = post_json(token, "/api/amazon/ziniao/bind", bind_payload)
    print(json.dumps(bound, ensure_ascii=False, indent=2)[:2000])

    accounts = get_json(token, "/api/platform-accounts?platform=amazon").get("data") or []
    print(f"bound amazon accounts: {len(accounts)}")

    for scope in ("account_health", "daily", "insights"):
        print(f"\n=== 6. Sync scope={scope} ===")
        sync = post_json(token, "/api/amazon/sync", {"scope": scope})
        sync_data = sync.get("data") or sync
        job_id = sync_data.get("job_id")
        if not job_id and sync_data.get("jobs"):
            job_id = sync_data["jobs"][0].get("job_id")
        job = wait_job(token, f"/api/amazon/sync/{job_id}", scope)
        print("summary:", json.dumps(job.get("result_summary") or {}, ensure_ascii=False))

    daily = get_json(token, "/api/amazon/daily").get("data") or {}
    insights = get_json(token, "/api/amazon/insights").get("data") or {}
    metrics = {m.get("metric_key"): m.get("value") for m in (daily.get("account_metrics") or [])}
    print("\n=== 7. Results ===")
    print("metrics sample:", json.dumps(metrics, ensure_ascii=False))
    print("buyer_messages:", len(daily.get("buyer_messages") or []))
    print("reviews:", len(daily.get("reviews") or []))
    if daily.get("reviews"):
        print("review[0]:", json.dumps(daily["reviews"][0], ensure_ascii=False))
    print("products:", len(insights.get("products") or []))
    print("outbound:", len(insights.get("outbound_orders") or []))

    db = sqlite3.connect(ROOT / "backend" / "data" / "crosshub.db")
    rows = db.execute(
        "SELECT id, store_name, external_shop_id FROM platform_account WHERE tenant_id=? AND platform='amazon'",
        (tenant_id,),
    ).fetchall()
    print("DB amazon accounts tenant", tenant_id, ":", rows)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        raise
