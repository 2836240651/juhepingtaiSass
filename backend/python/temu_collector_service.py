#!/usr/bin/env python3
"""Run the Temu evidence HTTP collector service."""
from __future__ import annotations

import argparse
import os
from pathlib import Path

from app.platforms.temu_collector_service import run_server


def default_evidence_root() -> Path:
    return Path(os.environ.get("CROSSHUB_MONITOR_EVIDENCE_DIR", Path(__file__).resolve().parent / "exports" / "ctf-website"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Temu evidence HTTP collector")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=18082)
    parser.add_argument("--evidence-root", type=Path, default=default_evidence_root())
    args = parser.parse_args()
    print(f"temu_collector_listening=http://{args.host}:{args.port}", flush=True)
    print(f"temu_collector_evidence_root={args.evidence_root}", flush=True)
    run_server(host=args.host, port=args.port, evidence_root=args.evidence_root)


if __name__ == "__main__":
    main()
