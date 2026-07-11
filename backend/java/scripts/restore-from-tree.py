#!/usr/bin/env python3
"""Restore backend Java sources from a git tree object."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TREE = "a5e0b43c04f6680b31d5a3c1df866bf6ccbb421f"
PREFIX = "backend/java/src/main/java"


def main() -> None:
    src_root = ROOT / PREFIX / "com" / "crosshub"
    if src_root.exists():
        shutil.rmtree(src_root)
    files = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", TREE, "--", PREFIX],
        cwd=ROOT,
        text=True,
    ).strip().splitlines()
    for rel in files:
        dest = ROOT / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        data = subprocess.check_output(["git", "show", f"{TREE}:{rel}"], cwd=ROOT)
        dest.write_bytes(data)
    print(f"Restored {len(files)} files from tree {TREE}")


if __name__ == "__main__":
    main()
