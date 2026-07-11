import json
import sqlite3


def main() -> None:
    db_path = r"d:\NIUBI\SaaS-HZ_WEB_Demo\backend\data\crosshub.db"
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table'
              AND (
                name LIKE 'aliexpress%'
                OR name LIKE 'ae_%'
                OR name LIKE 'ali%'
              )
            ORDER BY 1
            """
        ).fetchall()
        print(json.dumps([r[0] for r in rows], ensure_ascii=False, indent=2))
    finally:
        conn.close()


if __name__ == "__main__":
    main()

