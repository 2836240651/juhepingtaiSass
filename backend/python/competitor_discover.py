#!/usr/bin/env python3
"""Discover Temu competitor candidates from a front-end search page."""
from __future__ import annotations

import argparse
import json
import sys

from app.config import resolve_tenant_id
from app.crawler.competitor_discovery import (
    DEFAULT_DISCOVERY_KEYWORD,
    DEFAULT_DISCOVERY_LIMIT,
    DEFAULT_DISCOVERY_REGION,
    discover_competitor_candidates,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Temu competitor discovery crawler")
    parser.add_argument("--tenant-id", type=int, help="Tenant ID")
    parser.add_argument("--keyword", default=DEFAULT_DISCOVERY_KEYWORD)
    parser.add_argument("--region", default=DEFAULT_DISCOVERY_REGION)
    parser.add_argument("--limit", type=int, default=DEFAULT_DISCOVERY_LIMIT)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        tenant_id = resolve_tenant_id(args.tenant_id)
        result = discover_competitor_candidates(
            tenant_id=tenant_id,
            keyword=args.keyword,
            region=args.region,
            limit=args.limit,
        )
    except Exception as exc:
        print(f"Competitor discovery failed: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(
            f"keyword={result['keyword']} region={result['region']} "
            f"candidates={len(result['candidates'])}"
        )


if __name__ == "__main__":
    main()
