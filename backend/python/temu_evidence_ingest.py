#!/usr/bin/env python3
"""Import Temu HAR/API payload evidence into raw_products.json for monitor worker."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from app.platforms.temu_evidence import ingest_evidence_file


def default_evidence_root() -> Path:
    return Path(os.environ.get("CROSSHUB_MONITOR_EVIDENCE_DIR", Path(__file__).resolve().parent / "exports" / "ctf-website"))


def run_import(*, source_file: Path, target_id: str, evidence_root: Path | None = None) -> dict:
    root = evidence_root or default_evidence_root()
    target_dir = root / target_id
    output_file = ingest_evidence_file(source_file, target_dir / "raw_products.json")
    products = json.loads(output_file.read_text(encoding="utf-8"))
    return {
        "status": "ok",
        "target_id": target_id,
        "source_file": str(source_file),
        "raw_products_file": str(output_file),
        "product_count": len(products),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert Temu HAR/API payload evidence to raw_products.json")
    parser.add_argument("--source-file", required=True, type=Path, help="HAR file or JSON API payload captured from an authorized browser session")
    parser.add_argument("--target-id", required=True, help="monitor_target id, e.g. mt_xxx")
    parser.add_argument("--evidence-root", type=Path, default=None, help="Evidence root; defaults to CROSSHUB_MONITOR_EVIDENCE_DIR or backend/python/exports/ctf-website")
    args = parser.parse_args()
    result = run_import(source_file=args.source_file, target_id=args.target_id, evidence_root=args.evidence_root)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
