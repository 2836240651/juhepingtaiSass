#!/usr/bin/env python3
"""Split service/*.java into interface (service/) + impl (service/impl/)."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "src/main/java/com/crosshub/temu/service"
IMPL = ROOT / "impl"
IMPL.mkdir(exist_ok=True)

CLASS_RE = re.compile(r"public class (\w+)")
IMPORT_RE = re.compile(r"^import .+;$", re.MULTILINE)
PUBLIC_METHOD_RE = re.compile(
    r"^    public (?!class |static class |record)(\S.*?)\([^;]*\)\s*(?:throws [\w.,\s]+)?\s*\{",
    re.MULTILINE,
)


def collect_public_api(text: str, class_name: str) -> str:
    lines: list[str] = []
    in_nested = False
    brace_depth = 0
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("public static class "):
            in_nested = True
            brace_depth = 0
            lines.append(line)
            continue
        if in_nested:
            brace_depth += line.count("{") - line.count("}")
            lines.append(line)
            if brace_depth <= 0 and "}" in line:
                in_nested = False
            continue
        if stripped.startswith("public record "):
            lines.append(line)
            continue
        m = re.match(r"^    public (?!class |static class |record)(\S.*?)\([^;]*\)\s*(?:throws [\w.,\s]+)?\s*\{", line)
        if m:
            sig = m.group(0).strip()
            if sig.endswith("{"):
                sig = sig[:-1].strip()
            if f"{class_name}(" in sig:
                continue
            lines.append("    " + sig.rstrip(";") + ";")
    return "\n".join(lines)


def filter_imports(imports: list[str], body: str) -> list[str]:
    kept: list[str] = []
    for imp in imports:
        if imp.startswith("import org.springframework.stereotype"):
            continue
        simple = imp.replace("import ", "").replace(";", "").split(".")[-1]
        if simple in body or f"{simple}<" in body or f"{simple} " in body:
            kept.append(imp)
    std = []
    for token in ("List", "Map", "Optional", "Set"):
        if token in body and f"import java.util.{token};" not in kept:
            std.append(f"import java.util.{token};")
    return sorted(set(kept + std))


def refactor(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    m = CLASS_RE.search(text)
    if not m:
        return
    cls = m.group(1)
    if not cls.endswith("Service"):
        return

    iface_name = cls
    impl_name = cls + "Impl"
    imports = IMPORT_RE.findall(text)
    api_body = collect_public_api(text, cls)
    iface_imports = filter_imports(imports, api_body)

    iface_lines = ["package com.crosshub.temu.service;", ""]
    iface_lines.extend(iface_imports)
    if iface_imports:
        iface_lines.append("")
    iface_lines.append(f"public interface {iface_name} {{")
    iface_lines.append(api_body)
    iface_lines.append("}")
    iface_lines.append("")
    path.write_text("\n".join(iface_lines), encoding="utf-8")

    impl_text = text.replace(
        "package com.crosshub.temu.service;",
        "package com.crosshub.temu.service.impl;",
    )
    impl_text = impl_text.replace(
        f"public class {cls}",
        f"public class {impl_name} implements {iface_name}",
    )
    impl_lines = ["package com.crosshub.temu.service.impl;", "", f"import com.crosshub.temu.service.{iface_name};"]
    for line in impl_text.splitlines()[1:]:
        if line.startswith("package "):
            continue
        impl_lines.append(line)
    (IMPL / f"{impl_name}.java").write_text("\n".join(impl_lines) + "\n", encoding="utf-8")
    print(f"OK {cls}")


def main() -> None:
    for path in sorted(ROOT.glob("*.java")):
        refactor(path)


if __name__ == "__main__":
    main()
