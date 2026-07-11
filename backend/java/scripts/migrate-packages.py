#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "src/main/java/com/crosshub/temu"
WEB = ROOT / "web"
CTRL = ROOT / "controller"
MIG = ROOT / "config" / "migration"

DTO_IMPORTS = {
    "AuthController.java": [
        "import com.crosshub.temu.dto.request.auth.LoginRequest;",
        "import com.crosshub.temu.dto.request.auth.RegisterRequest;",
    ],
    "PlatformAccountController.java": [
        "import com.crosshub.temu.dto.request.platform.BatchBindRequest;",
        "import com.crosshub.temu.dto.request.platform.BindRequest;",
        "import com.crosshub.temu.dto.request.platform.StorePayload;",
    ],
    "TenantMemberController.java": [
        "import com.crosshub.temu.dto.request.common.StatusRequest;",
        "import com.crosshub.temu.dto.request.tenant.MemberPayload;",
        "import com.crosshub.temu.dto.request.tenant.MemberRequest;",
        "import com.crosshub.temu.dto.request.tenant.MemberScopeRequest;",
        "import com.crosshub.temu.dto.request.tenant.ScopePayload;",
    ],
    "WarehouseSiteController.java": [
        "import com.crosshub.temu.dto.request.common.StatusRequest;",
        "import com.crosshub.temu.dto.request.warehouse.SitePayload;",
    ],
    "WarehouseStaffController.java": [
        "import com.crosshub.temu.dto.request.common.StatusRequest;",
        "import com.crosshub.temu.dto.request.warehouse.StaffPayload;",
    ],
}

REPLACEMENTS = {
    "PlatformAccountService.StorePayload": "StorePayload",
    "TenantMemberService.MemberPayload": "MemberPayload",
    "TenantMemberService.ScopePayload": "ScopePayload",
    "WarehouseSiteService.SitePayload": "SitePayload",
    "WarehouseStaffService.StaffPayload": "StaffPayload",
    "ScopeRequest": "MemberScopeRequest",
    "TemuCrawlService.CrawlConflictException": "CrawlConflictException",
}


def strip_inner_records(text: str) -> str:
    return re.sub(r"\n\s*public record [\s\S]*?\n\}", "", text)


def migrate_controller(path: Path) -> None:
    if path.name == "TemuCrawlController.java":
        return
    text = path.read_text(encoding="utf-8")
    text = text.replace("package com.crosshub.temu.web;", "package com.crosshub.temu.controller;")
    for old, new in REPLACEMENTS.items():
        text = text.replace(old, new)
    text = strip_inner_records(text)
    for imp in DTO_IMPORTS.get(path.name, []):
        if imp not in text:
            text = text.replace("import org.springframework.web.bind.annotation.*;", imp + "\nimport org.springframework.web.bind.annotation.*;", 1)
    (CTRL / path.name).write_text(text, encoding="utf-8")
    print("controller", path.name)


def migrate_migrations() -> None:
    MIG.mkdir(parents=True, exist_ok=True)
    for path in sorted((ROOT / "config").glob("V*.java")):
        text = path.read_text(encoding="utf-8")
        text = text.replace("package com.crosshub.temu.config;", "package com.crosshub.temu.config.migration;")
        (MIG / path.name).write_text(text, encoding="utf-8")
        path.unlink()
        print("migration", path.name)
    tenant = ROOT / "config" / "TenantSchemaMigration.java"
    if tenant.exists():
        text = tenant.read_text(encoding="utf-8")
        text = text.replace("package com.crosshub.temu.config;", "package com.crosshub.temu.config.migration;")
        (MIG / tenant.name).write_text(text, encoding="utf-8")
        tenant.unlink()


def main() -> None:
    CTRL.mkdir(parents=True, exist_ok=True)
    for path in sorted(WEB.glob("*.java")):
        migrate_controller(path)
    for path in sorted(WEB.glob("*.java")):
        if path.name != "TemuCrawlController.java":
            path.unlink()
    if (WEB / "TemuCrawlController.java").exists():
        (WEB / "TemuCrawlController.java").unlink()
    migrate_migrations()
    if WEB.exists() and not any(WEB.iterdir()):
        WEB.rmdir()


if __name__ == "__main__":
    main()
