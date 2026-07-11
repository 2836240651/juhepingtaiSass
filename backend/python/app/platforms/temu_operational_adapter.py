"""Temu 运营爬取适配器：包装现有 crawl + ingest 流程。"""
from __future__ import annotations

from typing import Any

from app.ingest import run_ingest
from app.platforms.operational_base import PlatformOperationalAdapter


class TemuOperationalAdapter(PlatformOperationalAdapter):
    platform = "temu"

    def crawl_and_ingest(
        self,
        *,
        tenant_id: int,
        report_day: str | None = None,
        use_seed: bool = False,
        scope: str = "all",
    ) -> dict[str, Any]:
        _ = scope
        result = run_ingest(report_day, use_seed=use_seed, tenant_id=tenant_id)
        return {
            "platform": self.platform,
            "tenant_id": result["tenant_id"],
            "report_time": result["report_time"],
            "shops": result["shops"],
            "rows": result["rows"],
            "orders": 0,
            "violations": 0,
            "products": result["rows"],
        }
