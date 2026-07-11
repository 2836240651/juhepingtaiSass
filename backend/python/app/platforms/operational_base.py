"""多平台运营数据爬取适配器基类（区别于竞店 MonitorPlatformAdapter）。"""
from __future__ import annotations

from typing import Any


class PlatformOperationalAdapter:
    platform: str = ""

    def crawl_and_ingest(
        self,
        *,
        tenant_id: int,
        report_day: str | None = None,
        use_seed: bool = False,
        scope: str = "all",
    ) -> dict[str, Any]:
        raise NotImplementedError
