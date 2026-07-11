#!/usr/bin/env python3
"""Crawl a Temu competitor URL and persist a snapshot."""
from __future__ import annotations

import argparse
import json
import sys

from app.competitor_ingest import run_competitor_ingest
from app.config import resolve_tenant_id


def main() -> None:
    parser = argparse.ArgumentParser(description="Temu competitor crawler")
    parser.add_argument("--tenant-id", type=int, help="Tenant ID")
    parser.add_argument("--competitor-id", required=True, help="Competitor id from Java")
    parser.add_argument("--url", required=True, help="Temu competitor URL")
    parser.add_argument("--label", default="", help="Competitor label")
    parser.add_argument("--date", help="Snapshot date YYYY-MM-DD")
    parser.add_argument("--max-products", type=int, default=80)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        tenant_id = resolve_tenant_id(args.tenant_id)
        result = run_competitor_ingest(
            tenant_id=tenant_id,
            competitor_id=args.competitor_id,
            competitor_url=args.url,
            label=args.label,
            crawl_date=args.date,
            max_products=args.max_products,
        )
    except Exception as exc:
        print(f"Competitor crawl failed: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(
            f"tenant_id={result['tenant_id']} competitor_id={result['competitor_id']} "
            f"snapshot_date={result['snapshot_date']} rows={result['rows']}"
        )


if __name__ == "__main__":
    main()
