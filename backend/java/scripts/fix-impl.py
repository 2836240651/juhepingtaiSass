#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

IMPL = Path(__file__).resolve().parents[1] / "src/main/java/com/crosshub/temu/service/impl"

REPLACEMENTS = {
    "public DataScopeService(": "public DataScopeServiceImpl(",
    "public MemberScopeService(": "public MemberScopeServiceImpl(",
    "public MenuService(": "public MenuServiceImpl(",
    "public PlatformAccountService(": "public PlatformAccountServiceImpl(",
    "public TemuCrawlAuthService(": "public TemuCrawlAuthServiceImpl(",
    "public TemuCrawlService(": "public TemuCrawlServiceImpl(",
    "public TemuOperationalService(": "public TemuOperationalServiceImpl(",
    "public TemuWarningService(": "public TemuWarningServiceImpl(",
    "public TenantMemberService(": "public TenantMemberServiceImpl(",
    "public TenantRegistrationService(": "public TenantRegistrationServiceImpl(",
    "public WarehouseOrderService(": "public WarehouseOrderServiceImpl(",
    "public WarehouseSiteService(": "public WarehouseSiteServiceImpl(",
    "public WarehouseStaffService(": "public WarehouseStaffServiceImpl(",
    "TemuCrawlService.CrawlConflictException": "CrawlConflictException",
    "TemuWarningService.LowSaleWarning": "LowSaleWarning",
    "TemuWarningService.InventoryWarning": "InventoryWarning",
    "TemuWarningService.ReplenishResult": "ReplenishResult",
    "PlatformAccountService.StorePayload": "StorePayload",
    "TenantMemberService.MemberPayload": "MemberPayload",
    "TenantMemberService.ScopePayload": "ScopePayload",
    "WarehouseSiteService.SitePayload": "SitePayload",
    "WarehouseStaffService.StaffPayload": "StaffPayload",
}

IMPORTS_BY_FILE = {
    "TemuCrawlServiceImpl.java": [
        "import com.crosshub.temu.service.CrawlConflictException;",
        "import com.crosshub.temu.service.TemuCrawlAuthService;",
        "import com.crosshub.temu.service.DataScopeService;",
    ],
    "TemuCrawlAuthServiceImpl.java": [
        "import com.crosshub.temu.service.DataScopeService;",
    ],
    "TemuOperationalServiceImpl.java": [
        "import com.crosshub.temu.service.DataScopeService;",
        "import com.crosshub.temu.service.TemuWarningService;",
        "import com.crosshub.temu.dto.model.temu.InventoryWarning;",
        "import com.crosshub.temu.dto.model.temu.LowSaleWarning;",
        "import com.crosshub.temu.mapper.TemuMapper;",
    ],
    "TemuWarningServiceImpl.java": [
        "import com.crosshub.temu.dto.model.temu.InventoryWarning;",
        "import com.crosshub.temu.dto.model.temu.LowSaleWarning;",
        "import com.crosshub.temu.dto.model.temu.ReplenishResult;",
    ],
    "PlatformAccountServiceImpl.java": [
        "import com.crosshub.temu.dto.request.platform.StorePayload;",
        "import com.crosshub.temu.mapper.TemuMapper;",
    ],
    "TenantMemberServiceImpl.java": [
        "import com.crosshub.temu.dto.request.tenant.MemberPayload;",
        "import com.crosshub.temu.dto.request.tenant.ScopePayload;",
        "import com.crosshub.temu.service.MemberScopeService;",
    ],
    "WarehouseSiteServiceImpl.java": [
        "import com.crosshub.temu.dto.request.warehouse.SitePayload;",
    ],
    "WarehouseStaffServiceImpl.java": [
        "import com.crosshub.temu.dto.request.warehouse.StaffPayload;",
    ],
    "TenantMemberServiceImpl.java": [
        "import com.crosshub.temu.service.MemberScopeService;",
        "import com.crosshub.temu.dto.request.tenant.MemberPayload;",
        "import com.crosshub.temu.dto.request.tenant.ScopePayload;",
    ],
}


def strip_records(text: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    skip = 0
    for i, line in enumerate(lines):
        if skip > 0:
            skip -= 1
            continue
        if re.match(r"\s*public record \w+\(", line):
            depth = 0
            j = i
            while j < len(lines):
                depth += lines[j].count("(") - lines[j].count(")")
                if ");" in lines[j] or lines[j].strip().endswith(") {}"):
                    skip = j - i
                    break
                if lines[j].strip() == ") {}":
                    skip = j - i
                    break
                j += 1
            continue
        out.append(line)
    return "\n".join(out)


def main() -> None:
    for path in sorted(IMPL.glob("*.java")):
        text = path.read_text(encoding="utf-8")
        for old, new in REPLACEMENTS.items():
            text = text.replace(old, new)
        text = strip_records(text)
        for imp in IMPORTS_BY_FILE.get(path.name, []):
            if imp not in text:
                text = text.replace(
                    f"import com.crosshub.temu.service.{path.name.replace('Impl.java', '')};",
                    f"import com.crosshub.temu.service.{path.name.replace('Impl.java', '')};\n{imp}",
                    1,
                )
        # fix logger class names
        text = re.sub(
            r"LoggerFactory\.getLogger\((\w+)Service\.class\)",
            lambda m: f"LoggerFactory.getLogger({m.group(1)}ServiceImpl.class)",
            text,
        )
        path.write_text(text.rstrip() + "\n", encoding="utf-8")
        print("fixed", path.name)


if __name__ == "__main__":
    main()
