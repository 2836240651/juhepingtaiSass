#!/usr/bin/env python3
"""CLI entry for Temu mall snapshot pipeline."""

from app.external_snapshot.ctf_website.temu_mall_snapshot_pipeline import main

if __name__ == "__main__":
    raise SystemExit(main())
