"""Temu 卖家后台 API 客户端（通过浏览器上下文发请求，携带真实 Cookie + mallid）"""
from __future__ import annotations

import json
from typing import Any

from playwright.sync_api import APIResponse, Page

from app.browser.context import ensure_logged_in, human_pause
from app.config import TEMU_SALES_API, TEMU_USER_INFO_API


class TemuApiClient:
    def __init__(self, page: Page):
        self.page = page
        self.mall_id = ensure_logged_in(page)

    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "mallid": self.mall_id,
            "Origin": "https://agentseller.temu.com",
            "Referer": "https://agentseller.temu.com/",
        }

    def _post(self, url: str, body: dict[str, Any]) -> dict[str, Any]:
        human_pause()
        response: APIResponse = self.page.request.post(
            url,
            data=json.dumps(body),
            headers=self._headers(),
            timeout=60_000,
        )
        if not response.ok:
            text = response.text()[:500]
            raise RuntimeError(f"Temu API HTTP {response.status}: {text}")
        data = response.json()
        if not data.get("success"):
            raise RuntimeError(f"Temu API 业务失败: {json.dumps(data, ensure_ascii=False)[:500]}")
        return data

    def get_shop_info(self) -> tuple[str, str]:
        data = self._post(TEMU_USER_INFO_API, {})
        mall_list = (data.get("result") or {}).get("mallList") or []
        for mall in mall_list:
            if str(mall.get("mallId")) == self.mall_id:
                return mall.get("mallName") or "", str(mall.get("mallId"))
        raise RuntimeError(f"店铺 ID {self.mall_id} 不在账号店铺列表中")

    def fetch_sales_page(self, status_code: int, page_no: int, page_size: int = 100) -> dict[str, Any]:
        body = {
            "pageNo": page_no,
            "pageSize": page_size,
            "isLack": 0,
            "selectStatusList": [status_code],
        }
        return self._post(TEMU_SALES_API, body)

    def fetch_all_sales(self) -> list[tuple[int, dict[str, Any]]]:
        """返回 [(status_number, response_json), ...]"""
        status_map = {100: 10, 200: 11, 300: 12}
        batches: list[tuple[int, dict[str, Any]]] = []

        for status_str, status_num in status_map.items():
            page_no = 1
            while True:
                data = self.fetch_sales_page(status_num, page_no)
                sub_orders = ((data.get("result") or {}).get("subOrderList")) or []
                if not sub_orders:
                    break
                batches.append((status_num, data))
                page_no += 1
        return batches
