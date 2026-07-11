"""AliExpress 运营爬取适配器。"""
from __future__ import annotations

from typing import Any

from app.ingest_aliexpress import run_aliexpress_ingest
from app.platforms.operational_base import PlatformOperationalAdapter


class AliExpressOperationalAdapter(PlatformOperationalAdapter):
    platform = "aliexpress"

    def crawl_and_ingest(
        self,
        *,
        tenant_id: int,
        report_day: str | None = None,
        use_seed: bool = False,
        scope: str = "all",
    ) -> dict[str, Any]:
        if use_seed:
            raise RuntimeError("AliExpress 种子数据模式已关闭，请完成卖家后台登录后使用真实爬取")
        result = run_aliexpress_ingest(
            report_day,
            tenant_id=tenant_id,
            scope=scope,
        )
        return {
            "platform": self.platform,
            **result,
        }
