import sqlite3
import unittest

from app.db import SCHEMA
from app.ingest import replace_sales_for_day


def sale_row(ext_code, status, title):
    return {
        "platform": "temu",
        "status": status,
        "report_time": "2026-07-06",
        "shop_name": "Shop A",
        "shop_id": "mall-123",
        "tenant_id": 5,
        "user_id": 1,
        "title": title,
        "ext_code": ext_code,
        "son_sales_thirty_days": 1,
    }


class ReplaceSalesForDayTests(unittest.TestCase):
    def test_duplicate_ext_code_rows_update_instead_of_failing(self):
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.executescript(SCHEMA)

        count = replace_sales_for_day(
            conn,
            "2026-07-06",
            [
                sale_row("sku-1", "100", "first"),
                sale_row("sku-1", "300", "updated"),
            ],
            tenant_id=5,
        )

        rows = conn.execute(
            "SELECT ext_code, status, title FROM temu_sale WHERE tenant_id = 5"
        ).fetchall()
        self.assertEqual(count, 1)
        self.assertEqual(len(rows), 1)
        self.assertEqual(dict(rows[0]), {"ext_code": "sku-1", "status": "300", "title": "updated"})


if __name__ == "__main__":
    unittest.main()
