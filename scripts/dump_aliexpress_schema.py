import sqlite3


def main() -> None:
    db_path = r"d:\NIUBI\SaaS-HZ_WEB_Demo\backend\data\crosshub.db"
    conn = sqlite3.connect(db_path)
    try:
        for name in [
            "aliexpress_crawl_job",
            "aliexpress_shop",
            "aliexpress_product",
            "aliexpress_order",
            "aliexpress_violation",
            "aliexpress_hot_broadcast",
            "aliexpress_hot_broadcast_read",
        ]:
            row = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone()
            print(f"--- {name}")
            print(row[0] if row and row[0] else "<missing>")
            print()
    finally:
        conn.close()


if __name__ == "__main__":
    main()

