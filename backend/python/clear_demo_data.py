#!/usr/bin/env python3
"""清除 SQLite 中所有 demo/mock 店铺与关联运营数据"""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "crosshub.db"

DEMO_PREDICATE = "shop_id LIKE 'demo_%' OR shop_id LIKE 'mock_%'"
DEMO_EXT_PREDICATE = "ext_code LIKE 'YT-T%'"


def purge(conn: sqlite3.Connection, dry_run: bool = False) -> dict[str, int]:
    stats: dict[str, int] = {}
    statements = [
        ("temu_sale", f"DELETE FROM temu_sale WHERE {DEMO_PREDICATE} OR {DEMO_EXT_PREDICATE}"),
        ("temu_hot_broadcast", f"DELETE FROM temu_hot_broadcast WHERE {DEMO_PREDICATE} OR source IN ('seed', 'overload')"),
        ("temu_restock_status", f"DELETE FROM temu_restock_status WHERE {DEMO_PREDICATE} OR sku LIKE 'YT-T%'"),
        ("user_shop_scope", f"DELETE FROM user_shop_scope WHERE {DEMO_PREDICATE}"),
        ("temu_shop", f"DELETE FROM temu_shop WHERE {DEMO_PREDICATE}"),
        ("platform_account", "DELETE FROM platform_account WHERE id LIKE 'demo_%' OR account LIKE '%@demo%' OR store_name LIKE '%Demo%'"),
        ("temu_crawl_job", "DELETE FROM temu_crawl_job WHERE mode = 'seed'"),
    ]

    for table, sql in statements:
        try:
            if dry_run:
                count_sql = sql.replace("DELETE FROM", "SELECT COUNT(*) FROM", 1)
                count = conn.execute(count_sql).fetchone()[0]
            else:
                cur = conn.execute(sql)
                count = cur.rowcount
            stats[table] = int(count or 0)
        except sqlite3.OperationalError:
            stats[table] = 0

    if not dry_run:
        conn.commit()
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="清除 demo/mock 数据")
    parser.add_argument("--db", default=str(DEFAULT_DB))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        raise SystemExit(f"数据库不存在: {db_path}")

    conn = sqlite3.connect(db_path)
    try:
        stats = purge(conn, dry_run=args.dry_run)
    finally:
        conn.close()

    action = "将删除" if args.dry_run else "已删除"
    print(f"{action} demo/mock 数据 ({db_path}):")
    for table, count in stats.items():
        print(f"  {table}: {count}")


if __name__ == "__main__":
    main()
