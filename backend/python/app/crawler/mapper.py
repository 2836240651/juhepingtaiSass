"""Temu API 响应 → temu_sale 表行"""
from __future__ import annotations

from app.config import STATUS_TO_CODE


def _price_status(code: int | None) -> str:
    if code == 2:
        return "open"
    if code == 3:
        return "close"
    return "none"


def map_sales_batches(
    batches: list[tuple[int, dict]],
    *,
    shop_id: str,
    shop_name: str,
    report_time: str,
    nickname: str = "",
    username: str = "",
    enterprise: str = "",
    user_id: int = 1,
) -> list[dict]:
    rows: list[dict] = []

    for status_num, payload in batches:
        status_str = STATUS_TO_CODE.get(status_num, "0")
        sub_orders = ((payload.get("result") or {}).get("subOrderList")) or []

        for order in sub_orders:
            skus = order.get("skuQuantityDetailList") or []
            for sku in skus:
                s30 = int(sku.get("lastThirtyDaysSaleVolume") or 0)
                if s30 == 0:
                    continue

                inv = sku.get("inventoryNumInfo") or {}
                wh_groups = sku.get("warehouseGroupList") or []
                son_storage = wh_groups[0] if wh_groups else ""

                rows.append(
                    {
                        "platform": "temu",
                        "status": status_str,
                        "report_time": report_time,
                        "shop_name": shop_name,
                        "shop_id": shop_id,
                        "tenant_id": 1,
                        "user_id": user_id,
                        "cost": 0,
                        "category_name": order.get("category") or "",
                        "img_url": order.get("productSkcPicture") or "",
                        "title": order.get("productName") or "",
                        "skc": str(order.get("productSkcId") or ""),
                        "spu": str(order.get("productId") or ""),
                        # ext_code 在真实场景可能是 SKC 级（重复）；优先用 skuExtCode 作为更细粒度唯一键
                        "ext_code": (
                            sku.get("skuExtCode")
                            or order.get("skcExtCode")
                            or str(sku.get("productSkuId") or "")
                        ),
                        "son_sku": str(sku.get("productSkuId") or ""),
                        "son_price": int(sku.get("supplierPrice") or 0),
                        "son_today_sales": int(sku.get("todaySaleVolume") or 0),
                        "son_sales_seven_days": int(sku.get("lastSevenDaysSaleVolume") or 0),
                        "son_sales_thirty_days": s30,
                        "join_site_time": int(order.get("onSalesDurationOffline") or 0),
                        "warehouse_available_stock": int(inv.get("warehouseInventoryNum") or 0),
                        "nickname": nickname,
                        "username": username,
                        "enterprise": enterprise,
                    }
                )
    return rows
