#!/usr/bin/env python3
"""Fix package declarations and imports after a partial restructure."""
from __future__ import annotations

import re
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src/main/java/com/crosshub"


def package_for(path: Path) -> str:
    rel = path.relative_to(SRC).with_suffix("")
    parts = rel.parts
    if parts[0] == "CrosshubApplication":
        return "com.crosshub"
    return "com.crosshub." + ".".join(parts[:-1])


def collect_fqn_map() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for path in SRC.rglob("*.java"):
        text = path.read_text(encoding="utf-8-sig")
        pkg = package_for(path)
        cls = path.stem
        old_m = re.search(r"^package\s+([\w.]+);", text, flags=re.MULTILINE)
        if old_m:
            old = f"{old_m.group(1)}.{cls}"
            new = f"{pkg}.{cls}"
            if old != new:
                mapping[old] = new
        text = re.sub(r"^package\s+[\w.]+;", f"package {pkg};", text, count=1, flags=re.MULTILINE)
        path.write_text(text, encoding="utf-8")
    return mapping


def rewrite_imports(fqn_map: dict[str, str]) -> None:
    ordered = sorted(fqn_map.items(), key=lambda item: len(item[0]), reverse=True)
    for path in SRC.rglob("*.java"):
        text = path.read_text(encoding="utf-8-sig")
        original = text
        for old, new in ordered:
            text = text.replace(old, new)
        if text != original:
            path.write_text(text, encoding="utf-8")


def main() -> None:
    fqn_map = collect_fqn_map()
    rewrite_imports(fqn_map)
    print(f"Fixed packages; {len(fqn_map)} FQN mappings")


if __name__ == "__main__":
    main()
