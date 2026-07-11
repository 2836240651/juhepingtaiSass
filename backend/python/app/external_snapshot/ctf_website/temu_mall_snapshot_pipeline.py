"""One-command Temu mall snapshot pipeline for the SaaS worker."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import ROOT, is_headless, resolve_profile_dir, resolve_tenant_id
from app.external_snapshot.ctf_website import temu_competitor_analysis
from app.external_snapshot.ctf_website.temu_page_card_lib import (
    build_snapshot,
    canonical_mall_url,
    collect_with_playwright,
    default_output_paths,
    load_raw_products_input,
    parse_mall_id,
    render_report_md,
    write_json,
)


def run_pipeline(
    store_url: str,
    *,
    root: Path,
    tenant_id: int | None = None,
    latest_limit: int = 15,
    headless: bool | None = None,
    scroll_rounds: int = 10,
    wait_ms: int = 1500,
    input_file: str = "",
    skip_collect: bool = False,
    user_data_dir: str = "",
    storage_state: str = "",
    interactive: bool = False,
    use_default_profile: bool = True,
) -> dict[str, Any]:
    mall_id = parse_mall_id(store_url)
    paths = default_output_paths(mall_id, root)
    canonical_url = canonical_mall_url(store_url)
    profile_dir = user_data_dir
    if not profile_dir and tenant_id is not None:
        profile_dir = str(resolve_profile_dir(tenant_id))
        use_default_profile = False

    if skip_collect and input_file:
        snapshot = json.loads(Path(input_file).read_text(encoding="utf-8"))
        if "raw_products" not in snapshot:
            snapshot = build_snapshot(load_raw_products_input(snapshot), canonical_url, source="imported")
    elif input_file:
        imported = json.loads(Path(input_file).read_text(encoding="utf-8"))
        snapshot = build_snapshot(
            load_raw_products_input(imported),
            canonical_url,
            source="browser-export",
            extra_collection={"imported_from": str(input_file)},
        )
    else:
        snapshot = collect_with_playwright(
            canonical_url,
            headless=is_headless() if headless is None else headless,
            scroll_rounds=scroll_rounds,
            wait_ms=wait_ms,
            user_data_dir=profile_dir,
            storage_state=storage_state,
            interactive=interactive,
            use_default_profile=use_default_profile,
            profile_root=root,
        )

    write_json(paths["raw_products"], snapshot)
    if snapshot["status"] not in {"OK", "PARTIAL_OK"} or not snapshot["raw_products"]:
        manifest = {
            "status": snapshot["status"],
            "mall_id": mall_id,
            "store_url": canonical_url,
            "paths": {key: str(value) for key, value in paths.items()},
            "message": snapshot.get("collection", {}).get("message", "Collection produced no analyzable products."),
            "final_url": snapshot.get("collection", {}).get("final_url"),
            "next_command": snapshot.get("collection", {}).get("next_command"),
        }
        write_json(paths["manifest"], manifest)
        return manifest

    analysis = temu_competitor_analysis.analyze_products(
        snapshot["raw_products"],
        store_id=mall_id,
        latest_limit=latest_limit,
        captured_at=snapshot["captured_at"],
    )
    write_json(paths["analysis"], analysis)
    paths["report"].write_text(render_report_md(analysis, snapshot), encoding="utf-8")
    manifest = {
        "status": "OK",
        "completed_at": datetime.now(timezone.utc).astimezone().isoformat(),
        "mall_id": mall_id,
        "store_url": canonical_url,
        "pipeline": [
            "collect_page_cards",
            "normalize_raw_products",
            "analyze_latest_and_outliers",
            "render_report",
        ],
        "counts": {
            "raw_products": len(snapshot["raw_products"]),
            "latest_listings": len(analysis["latest_listings"]),
            "abnormal_sales": len(analysis["abnormal_sales"]),
        },
        "paths": {key: str(value) for key, value in paths.items()},
    }
    write_json(paths["manifest"], manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Temu mall snapshot pipeline end-to-end.")
    parser.add_argument("--store-url", required=True, help="Temu mall URL containing mall_id")
    parser.add_argument("--root", default=str(ROOT), help="Worker root for exports/reports")
    parser.add_argument("--tenant-id", type=int, default=None, help="Reuse tenant browser profile")
    parser.add_argument("--latest-limit", type=int, default=15)
    parser.add_argument("--headless", action="store_true", help="Use headless Playwright")
    parser.add_argument("--scroll-rounds", type=int, default=10)
    parser.add_argument("--wait-ms", type=int, default=1500)
    parser.add_argument("--input", default="", help="Reuse browser export or raw_products JSON")
    parser.add_argument("--skip-collect", action="store_true")
    parser.add_argument("--user-data-dir", default="")
    parser.add_argument("--storage-state", default="")
    parser.add_argument("--interactive", action="store_true")
    parser.add_argument("--no-default-profile", action="store_true")
    args = parser.parse_args()

    tenant_id = resolve_tenant_id(args.tenant_id) if args.tenant_id else None
    manifest = run_pipeline(
        args.store_url,
        root=Path(args.root).resolve(),
        tenant_id=tenant_id,
        latest_limit=args.latest_limit,
        headless=args.headless,
        scroll_rounds=args.scroll_rounds,
        wait_ms=args.wait_ms,
        input_file=args.input,
        skip_collect=args.skip_collect,
        user_data_dir=args.user_data_dir,
        storage_state=args.storage_state,
        interactive=args.interactive,
        use_default_profile=not args.no_default_profile,
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0 if manifest.get("status") == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
