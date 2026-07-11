"""AliExpress 运营数据入库。"""
from __future__ import annotations

from datetime import date, timedelta
import json
import sqlite3

from app.crawler.aliexpress_crawler import crawl_aliexpress_operational
from app.db import connect, init_schema, seed_users


def upsert_shops(conn: sqlite3.Connection, shops: list[dict], tenant_id: int) -> None:
    for shop in shops:
        conn.execute(
            """
            INSERT INTO aliexpress_shop (shop_id, tenant_id, shop_name)
            VALUES (?, ?, ?)
            ON CONFLICT(shop_id) DO UPDATE SET
              shop_name = excluded.shop_name,
              tenant_id = excluded.tenant_id
            """,
            (shop["shop_id"], tenant_id, shop.get("shop_name") or shop["shop_id"]),
        )


def replace_orders_for_day(
    conn: sqlite3.Connection,
    report_day: str,
    rows: list[dict],
    tenant_id: int,
) -> int:
    store_ids = sorted({r["store_id"] for r in rows})
    for store_id in store_ids:
        conn.execute(
            """
            DELETE FROM aliexpress_order
            WHERE tenant_id = ? AND report_day = ? AND store_id = ?
            """,
            (tenant_id, report_day, store_id),
        )

    sql = """
        INSERT INTO aliexpress_order (
          id, tenant_id, store_id, store_name, report_day, order_no, fulfillment_type,
          sku, product_name, quantity, amount, currency, country, status,
          ordered_at, ship_deadline, warehouse_name
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
          status = excluded.status,
          quantity = excluded.quantity,
          amount = excluded.amount,
          ordered_at = excluded.ordered_at,
          ship_deadline = excluded.ship_deadline,
          warehouse_name = excluded.warehouse_name
    """
    count = 0
    for row in rows:
        conn.execute(
            sql,
            (
                row["id"],
                tenant_id,
                row["store_id"],
                row.get("store_name") or "",
                report_day,
                row["order_no"],
                row["fulfillment_type"],
                row.get("sku") or "",
                row.get("product_name") or "",
                int(row.get("quantity") or 0),
                float(row.get("amount") or 0),
                row.get("currency") or "USD",
                row.get("country") or "",
                row.get("status") or "",
                row.get("ordered_at") or "",
                row.get("ship_deadline"),
                row.get("warehouse_name"),
            ),
        )
        count += 1
    return count


def replace_violations(conn: sqlite3.Connection, rows: list[dict], tenant_id: int) -> int:
    store_ids = sorted({r["store_id"] for r in rows})
    for store_id in store_ids:
        conn.execute(
            "DELETE FROM aliexpress_violation WHERE tenant_id = ? AND store_id = ?",
            (tenant_id, store_id),
        )

    sql = """
        INSERT INTO aliexpress_violation (
          id, tenant_id, store_id, store_name, type_code, type_label, order_no,
          description, fine_amount, currency, violated_at, appeal_status,
          appeal_result, confirmed, severity, owner
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    count = 0
    for row in rows:
        conn.execute(
            sql,
            (
                row["id"],
                tenant_id,
                row["store_id"],
                row.get("store_name") or "",
                row.get("type_code") or "",
                row.get("type_label") or "",
                row.get("order_no") or "",
                row.get("description") or "",
                float(row.get("fine_amount") or 0),
                row.get("currency") or "USD",
                row.get("violated_at") or "",
                row.get("appeal_status"),
                row.get("appeal_result"),
                int(row.get("confirmed") or 0),
                row.get("severity") or "medium",
                row.get("owner") or "",
            ),
        )
        count += 1
    return count


def _build_sales_last7_days(
    conn: sqlite3.Connection,
    *,
    tenant_id: int,
    store_id: str,
    sku: str,
    report_day: str,
) -> list[int]:
    end_day = date.fromisoformat(report_day)
    day_keys = [(end_day - timedelta(days=offset)).isoformat() for offset in range(6, -1, -1)]
    counts = {day: 0 for day in day_keys}
    rows = conn.execute(
        """
        SELECT report_day, SUM(quantity) AS qty
        FROM aliexpress_order
        WHERE tenant_id = ? AND store_id = ? AND sku = ?
          AND report_day >= ? AND report_day <= ?
        GROUP BY report_day
        """,
        (tenant_id, store_id, sku, day_keys[0], day_keys[-1]),
    ).fetchall()
    for report, qty in rows:
        day = str(report or "")
        if day in counts:
            counts[day] = int(qty or 0)
    return [counts[day] for day in day_keys]


def replace_products_for_day(
    conn: sqlite3.Connection,
    report_day: str,
    rows: list[dict],
    tenant_id: int,
) -> int:
    store_ids = sorted({r["store_id"] for r in rows})
    for store_id in store_ids:
        conn.execute(
            """
            DELETE FROM aliexpress_product
            WHERE tenant_id = ? AND report_day = ? AND store_id = ?
            """,
            (tenant_id, report_day, store_id),
        )

    sql = """
        INSERT INTO aliexpress_product (
          tenant_id, store_id, store_name, report_day, sku, name, category,
          selling_price, cost_price, platform_fee_rate, logistics_fee,
          official_stock, local_stock, days_without_sale, daily_sales,
          sales_last7_days, owner
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    count = 0
    for row in rows:
        sales_last7 = _build_sales_last7_days(
            conn,
            tenant_id=tenant_id,
            store_id=row["store_id"],
            sku=row.get("sku") or "",
            report_day=report_day,
        )
        conn.execute(
            sql,
            (
                tenant_id,
                row["store_id"],
                row.get("store_name") or "",
                report_day,
                row.get("sku") or "",
                row.get("name") or "",
                row.get("category") or "",
                float(row.get("selling_price") or 0),
                float(row.get("cost_price") or 0),
                float(row.get("platform_fee_rate") or 0),
                float(row.get("logistics_fee") or 0),
                int(row.get("official_stock") or 0),
                int(row.get("local_stock") or 0),
                int(row.get("days_without_sale") or 0),
                int(row.get("daily_sales") or 0),
                json.dumps(sales_last7, ensure_ascii=False),
                row.get("owner") or "",
            ),
        )
        count += 1
    return count


def replace_broadcasts(conn: sqlite3.Connection, rows: list[dict], tenant_id: int) -> int:
    if not rows:
        return 0
    store_ids = sorted({r["store_id"] for r in rows})
    for store_id in store_ids:
        conn.execute(
            "DELETE FROM aliexpress_hot_broadcast WHERE tenant_id = ? AND store_id = ?",
            (tenant_id, store_id),
        )

    sql = """
        INSERT INTO aliexpress_hot_broadcast (
          id, tenant_id, store_id, sku, product_name, daily_sales, message
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    count = 0
    for row in rows:
        conn.execute(
            sql,
            (
                row["id"],
                tenant_id,
                row["store_id"],
                row.get("sku") or "",
                row.get("product_name") or "",
                int(row.get("daily_sales") or 0),
                row.get("message") or "",
            ),
        )
        count += 1
    return count


def run_aliexpress_ingest(
    report_day: str | None = None,
    *,
    tenant_id: int = 1,
    scope: str = "all",
    store_id: str | None = None,
    store_name: str | None = None,
) -> dict:
    payload = crawl_aliexpress_operational(
        report_day,
        tenant_id=tenant_id,
        scope=scope,
        store_id=store_id,
        store_name=store_name,
    )
    conn = connect()
    try:
        init_schema(conn)
        seed_users(conn)
        upsert_shops(conn, payload["shops"], tenant_id)
        order_count = replace_orders_for_day(conn, payload["report_time"], payload["orders"], tenant_id)
        violation_count = replace_violations(conn, payload["violations"], tenant_id)
        product_count = replace_products_for_day(conn, payload["report_time"], payload["products"], tenant_id)
        broadcast_count = replace_broadcasts(conn, payload["broadcasts"], tenant_id)
        conn.commit()
        return {
            "tenant_id": tenant_id,
            "report_time": payload["report_time"],
            "shops": len(payload["shops"]),
            "rows": order_count,
            "orders": order_count,
            "violations": violation_count,
            "products": product_count,
            "broadcasts": broadcast_count,
        }
    finally:
        conn.close()
