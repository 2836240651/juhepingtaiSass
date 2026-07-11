#!/usr/bin/env python3
"""Probe AliExpress violation list APIs."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.browser.aliexpress_context import open_aliexpress_context, wait_for_ae_login
from app.config import AE_VIOLATION_PAGE

MARKERS = (
    "violation",
    "penalty",
    "fine",
    "punish",
    "违规",
    "处罚",
    "罚款",
)


def main() -> None:
    tenant_id = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    hits: list[dict] = []

    with open_aliexpress_context(tenant_id, headless=True) as (_, ctx):
        page = ctx.new_page()

        def on_response(response) -> None:
            try:
                if response.status != 200:
                    return
                url = response.url
                lowered = url.lower()
                if not any(token in lowered for token in ("mtop", "violation", "penalty", "punish", "performance", "scm-supplier")):
                    return
                body = response.json()
                text = json.dumps(body, ensure_ascii=False) if isinstance(body, dict) else ""
                if any(marker in text for marker in MARKERS) or any(marker in lowered for marker in MARKERS):
                    hits.append(
                        {
                            "url": url,
                            "method": response.request.method,
                            "post": (response.request.post_data or "")[:400],
                            "api": body.get("api") if isinstance(body, dict) else None,
                            "totalCount": body.get("totalCount") if isinstance(body, dict) else None,
                            "data_len": len(body.get("data") or []) if isinstance(body, dict) else 0,
                            "sample": text[:600],
                        }
                    )
            except Exception:
                return

        page.on("response", on_response)
        page.goto(AE_VIOLATION_PAGE, wait_until="domcontentloaded", timeout=120_000)
        wait_for_ae_login(page, tenant_id=tenant_id)
        page.wait_for_timeout(20_000)

    out = ROOT / "ae_violation_hits.json"
    out.write_text(json.dumps(hits, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"hits={len(hits)} saved={out}")
    for item in hits[:12]:
        print(json.dumps(item, ensure_ascii=False)[:500])
        print("---")


if __name__ == "__main__":
    main()
