#!/usr/bin/env python3
"""Restructure com.crosshub.temu into multi-platform packages under com.crosshub."""
from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

JAVA_ROOT = Path(__file__).resolve().parents[1]
SRC = JAVA_ROOT / "src/main/java/com/crosshub"
LEGACY_ROOT = SRC / "temu"
STAGING_ROOT = SRC / "_legacy_temu_pkg"
TEST_OLD = JAVA_ROOT / "src/test/java/com/crosshub/temu"

TEMU_EXTRA = {"OperationalCrawlRunner.java", "CrawlConflictException.java", "TemuMapper.java"}
MONITOR_EXTRA = {"TimedProcessRunner.java", "MonitorReportFile.java", "MonitorScheduler.java"}


@dataclass
class Move:
    src: Path
    dest: Path
    old_package: str
    new_package: str
    class_name: str


def classify_by_name(name: str) -> str | None:
    if name == "CrosshubTemuApplication.java":
        return "app"
    if name in ("ApiResult.java", "AppErrorCode.java", "ApiExceptionHandler.java"):
        return "common"
    if name.startswith("Amazon") or name.startswith("Ziniao"):
        return "amazon"
    if name.startswith("AliExpress"):
        return "aliexpress"
    if name.startswith("Temu") or name in TEMU_EXTRA:
        return "temu"
    if name.startswith("Agent") or name.startswith("Integration"):
        return "agent"
    if name.startswith("Warehouse") or name.startswith("UserWarehouse"):
        return "warehouse"
    if name.startswith("Monitor") or name in MONITOR_EXTRA:
        return "monitor"
    if name.startswith("AssignedTask") or name.startswith("OpsFeedback"):
        return "task"
    if name.startswith("PlatformAccount"):
        return "platform"
    if name.startswith("Auth") or name.startswith("AppUser") or name.startswith("Jwt"):
        return "auth"
    if name.startswith(
        ("Tenant", "Member", "Menu", "DataScope", "SysMenu", "UserMenuGrant", "UserPlatformScope", "UserShopScope")
    ):
        return "tenant"
    return None


def layer_from_rel(rel: Path) -> str:
    parts = rel.parts
    if "controller" in parts:
        return "controller"
    if "service" in parts and "impl" in parts:
        return "service.impl"
    if "service" in parts:
        return "service"
    if "entity" in parts:
        return "entity"
    if "repository" in parts:
        return "repository"
    if "mapper" in parts:
        return "mapper"
    if "common" in parts:
        return ""
    if "security" in parts:
        return ""
    if "config" in parts:
        return "migration" if "migration" in parts else ""
    if "dto" in parts:
        return "dto"
    return ""


def classify(rel: Path) -> tuple[str, str]:
    name = rel.name
    parts = rel.parts

    if name == "CrosshubTemuApplication.java":
        return ("app", "")

    if "common" in parts:
        return ("common", layer_from_rel(rel))

    if "security" in parts:
        return ("security", "")

    if "config" in parts:
        return ("config", "migration" if "migration" in parts else "")

    if "dto" in parts:
        if "request" in parts:
            idx = parts.index("request")
            if idx + 1 < len(parts) - 1:
                return (parts[idx + 1], "dto")
        if "model" in parts:
            idx = parts.index("model")
            domain = parts[idx + 1] if idx + 1 < len(parts) - 1 else "temu"
            return (domain, "dto")

    module = classify_by_name(name)
    if not module:
        raise RuntimeError(f"Cannot classify: {rel}")
    return (module, layer_from_rel(rel))


def package_for(module: str, layer: str) -> str:
    if module == "app":
        return "com.crosshub"
    if layer:
        return f"com.crosshub.{module}.{layer.replace('/', '.')}"
    return f"com.crosshub.{module}"


def target_path(module: str, layer: str, name: str) -> Path:
    if module == "app":
        return SRC / "CrosshubApplication.java"
    if layer:
        return SRC / module / layer.replace(".", "/") / name
    return SRC / module / name


def read_package(text: str) -> str:
    text = text.lstrip("\ufeff")
    m = re.search(r"^package\s+([\w.]+);", text, flags=re.MULTILINE)
    return m.group(1) if m else ""


def set_package(text: str, pkg: str) -> str:
    text = text.lstrip("\ufeff")
    return re.sub(r"^package\s+[\w.]+;", f"package {pkg};", text, count=1, flags=re.MULTILINE)


def collect_moves(root: Path) -> list[Move]:
    moves: list[Move] = []
    for path in sorted(root.rglob("*.java")):
        rel = path.relative_to(root)
        module, layer = classify(rel)
        dest = target_path(module, layer, path.name)
        if path.name == "CrosshubTemuApplication.java":
            dest = SRC / "CrosshubApplication.java"
        old_pkg = read_package(path.read_text(encoding="utf-8"))
        new_pkg = package_for(module, layer)
        class_name = path.stem
        moves.append(Move(path, dest, old_pkg, new_pkg, class_name))
    return moves


def apply_moves(moves: list[Move]) -> dict[str, str]:
    fqn_map: dict[str, str] = {}
    for move in moves:
        text = move.src.read_text(encoding="utf-8")
        text = set_package(text, move.new_package)
        if move.class_name == "CrosshubTemuApplication":
            text = text.replace("CrosshubTemuApplication", "CrosshubApplication")
        move.dest.parent.mkdir(parents=True, exist_ok=True)
        move.dest.write_text(text, encoding="utf-8")
        if move.old_package and move.new_package:
            old_fqn = f"{move.old_package}.{move.class_name}"
            new_fqn = f"{move.new_package}.{move.class_name}"
            if old_fqn != new_fqn:
                fqn_map[old_fqn] = new_fqn
    return fqn_map


def rewrite_all_java(java_roots: list[Path], fqn_map: dict[str, str]) -> None:
    ordered = sorted(fqn_map.items(), key=lambda item: len(item[0]), reverse=True)
    for root in java_roots:
        if not root.exists():
            continue
        for path in root.rglob("*.java"):
            text = path.read_text(encoding="utf-8")
            original = text
            for old, new in ordered:
                text = text.replace(old, new)
            if text != original:
                path.write_text(text, encoding="utf-8")


def migrate_tests(fqn_map: dict[str, str]) -> None:
    if not TEST_OLD.exists():
        return
    for path in sorted(TEST_OLD.rglob("*.java")):
        rel = path.relative_to(TEST_OLD)
        name = path.name
        module = classify_by_name(name)
        if not module:
            module = "monitor" if "Monitor" in name or "TimedProcessRunner" in name else "temu" if "Temu" in name else "common"
        layer = layer_from_rel(rel)
        if not layer:
            if "controller" in rel.parts:
                layer = "controller"
            elif "impl" in rel.parts:
                layer = "service.impl"
            elif "service" in rel.parts:
                layer = "service"
        dest = JAVA_ROOT / "src/test/java/com/crosshub" / module / layer.replace(".", "/") / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        text = set_package(path.read_text(encoding="utf-8"), package_for(module, layer))
        dest.write_text(text, encoding="utf-8")
    rewrite_all_java([JAVA_ROOT / "src/test/java"], fqn_map)


def cleanup(staging: Path) -> None:
    if staging.exists():
        shutil.rmtree(staging)
    if TEST_OLD.exists():
        shutil.rmtree(TEST_OLD)


def main() -> None:
    if not LEGACY_ROOT.exists():
        raise SystemExit(f"Legacy package root not found: {LEGACY_ROOT}")
    if STAGING_ROOT.exists():
        shutil.rmtree(STAGING_ROOT)
    shutil.move(str(LEGACY_ROOT), str(STAGING_ROOT))
    try:
        moves = collect_moves(STAGING_ROOT)
        fqn_map = apply_moves(moves)
        rewrite_all_java([SRC, JAVA_ROOT / "src/test/java"], fqn_map)
        migrate_tests(fqn_map)
        print(f"Restructured {len(moves)} sources; {len(fqn_map)} FQN mappings")
    finally:
        cleanup(STAGING_ROOT)


if __name__ == "__main__":
    main()
