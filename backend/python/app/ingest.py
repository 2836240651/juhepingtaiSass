"""将爬虫结果写入 SQLite（按租户+店铺+日期全量覆盖）"""
from __future__ import annotations

import sqlite3

from .crawler.temu_crawler import crawl_temu_sales
from .db import connect, init_schema, seed_users

COLUMNS = [
    "platform",
    "status",
    "report_time",
    "shop_name",
    "shop_id",
    "tenant_id",
    "user_id",
    "cost",
    "category_name",
    "img_url",
    "title",
    "skc",
    "spu",
    "ext_code",
    "son_sku",
    "son_price",
    "son_today_sales",
    "son_sales_seven_days",
    "son_sales_thirty_days",
    "join_site_time",
    "warehouse_available_stock",
    "nickname",
    "username",
    "enterprise",
]


def upsert_shops(conn: sqlite3.Connection, shops: list[dict], tenant_id: int) -> None:
    for shop in shops:
        conn.execute(
            """
            INSERT INTO temu_shop (shop_id, tenant_id, shop_name, is_upload)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(shop_id) DO UPDATE SET
              shop_name = excluded.shop_name,
              is_upload = excluded.is_upload,
              tenant_id = excluded.tenant_id
            """,
            (
                shop["shop_id"],
                tenant_id,
                shop["shop_name"],
                1 if shop.get("is_upload", True) else 0,
            ),
        )


def replace_sales_for_day(
    conn: sqlite3.Connection,
    report_time: str,
    rows: list[dict],
    tenant_id: int,
) -> int:
    shop_ids = sorted({r["shop_id"] for r in rows})
    for shop_id in shop_ids:
        conn.execute(
            """
            DELETE FROM temu_sale
            WHERE tenant_id = ? AND report_time = ? AND shop_id = ?
            """,
            (tenant_id, report_time, shop_id),
        )

    placeholders = ", ".join(["?"] * len(COLUMNS))
    update_columns = [
        col for col in COLUMNS
        if col not in ("tenant_id", "report_time", "shop_id", "ext_code")
    ]
    assignments = ", ".join([f"{col} = excluded.{col}" for col in update_columns])
    sql = f"""
        INSERT INTO temu_sale ({', '.join(COLUMNS)}) VALUES ({placeholders})
        ON CONFLICT(tenant_id, report_time, shop_id, ext_code)
        DO UPDATE SET {assignments}
    """

    seen_keys = set()
    for row in rows:
        values = [row.get(col, "") for col in COLUMNS]
        if not values[COLUMNS.index("tenant_id")]:
            values[COLUMNS.index("tenant_id")] = tenant_id
        conn.execute(sql, values)
        seen_keys.add((
            values[COLUMNS.index("tenant_id")],
            values[COLUMNS.index("report_time")],
            values[COLUMNS.index("shop_id")],
            values[COLUMNS.index("ext_code")],
        ))
    return len(seen_keys)


def run_ingest(
    report_day: str | None = None,
    *,
    use_seed: bool = False,
    tenant_id: int = 1,
) -> dict:
    payload = crawl_temu_sales(report_day, use_seed=use_seed, tenant_id=tenant_id)
    conn = connect()
    try:
        init_schema(conn)
        seed_users(conn)
        upsert_shops(conn, payload["shops"], tenant_id)
        count = replace_sales_for_day(conn, payload["report_time"], payload["rows"], tenant_id)
        conn.commit()
        return {
            "tenant_id": tenant_id,
            "report_time": payload["report_time"],
            "shops": len(payload["shops"]),
            "rows": count,
            "db": str(conn.execute("PRAGMA database_list").fetchone()[2]),
        }
    finally:
        conn.close()


if __name__ == "__main__":
    result = run_ingest(tenant_id=1)
    print(f"[Temu 爬虫] 入库完成: {result}")
