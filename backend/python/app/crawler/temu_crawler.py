"""
Temu 全托管运营数据爬虫

- 默认：Playwright 持久化浏览器 + 卖家后台 API（与 Commander Agent 同路径）
- 回退：--seed 使用本地 demo_sales.json
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from app.browser.context import get_or_open_seller_page, open_temu_context
from app.crawler.mapper import map_sales_batches
from app.crawler.temu_api import TemuApiClient

SEED_PATH = Path(__file__).resolve().parents[1] / "seed" / "demo_sales.json"


def load_seed() -> dict:
    with SEED_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def crawl_temu_sales_seed(report_day: str | None = None) -> dict:
    report_time = report_day or date.today().isoformat()
    seed = load_seed()
    shops = seed.get("shops", [])
    rows = []
    for item in seed.get("products", []):
        row = dict(item)
        row["platform"] = "temu"
        row["report_time"] = report_time
        row["status"] = str(row.get("status", "300"))
        rows.append(row)
    return {"report_time": report_time, "shops": shops, "rows": rows}


def crawl_temu_sales_live(report_day: str | None = None) -> dict:
    report_time = report_day or date.today().isoformat()

    with open_temu_context() as (_, context):
        page = get_or_open_seller_page(context)
        client = TemuApiClient(page)
        shop_name, shop_id = client.get_shop_info()
        batches = client.fetch_all_sales()
        rows = map_sales_batches(
            batches,
            shop_id=shop_id,
            shop_name=shop_name,
            report_time=report_time,
        )
        shops = [{"shop_id": shop_id, "shop_name": shop_name, "is_upload": True}]
        return {"report_time": report_time, "shops": shops, "rows": rows}


def crawl_temu_sales(report_day: str | None = None, *, use_seed: bool = False) -> dict:
    if use_seed:
        return crawl_temu_sales_seed(report_day)
    return crawl_temu_sales_live(report_day)
