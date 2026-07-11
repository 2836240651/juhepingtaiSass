#!/usr/bin/env python3
"""CLI wrapper kept for scripts/ctf-website compatibility."""

from app.external_snapshot.ctf_website.temu_mall_snapshot_pipeline import main

if __name__ == "__main__":
    raise SystemExit(main())
