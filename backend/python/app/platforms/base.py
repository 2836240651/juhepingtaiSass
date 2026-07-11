"""Base adapter contract for competitor monitor platforms."""
from __future__ import annotations


class MonitorPlatformAdapter:
    def crawl_target(self, *, tenant_id: int, target: dict, max_products: int) -> dict:
        raise NotImplementedError
