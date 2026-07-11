import sqlite3
import tempfile
import unittest
from pathlib import Path

from app.monitor_db import init_monitor_schema, init_monitor_result_schema
from app.monitor_worker_service import process_next_pending_job


class FakeTemuAdapter:
    def crawl_target(self, *, tenant_id, target, max_products):
        return {
            "platform": "temu",
            "snapshot_at": "2026-07-07 10:00:00",
            "products": [
                {
                    "product_id": "p-100",
                    "product_name": "Fishing Lure Set",
                    "category": "Sports",
                    "price": 12.5,
                    "daily_sales": 45,
                    "total_sales": 120,
                    "listed_at": "2026-07-07",
                    "url": "https://www.temu.com/goods.html?goods_id=100",
                },
                {
                    "product_id": "p-101",
                    "product_name": "Camping Light",
                    "category": "Outdoors",
                    "price": 8.9,
                    "daily_sales": 6,
                    "total_sales": 30,
                    "listed_at": "2026-06-20",
                    "url": "https://www.temu.com/goods.html?goods_id=101",
                },
            ],
        }


class MonitorWorkerServiceTest(unittest.TestCase):
    def test_process_next_pending_job_persists_snapshot_signals_and_reports(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            report_root = Path(tmpdir) / "reports"
            conn = sqlite3.connect(":memory:")
            conn.row_factory = sqlite3.Row
            init_monitor_schema(conn)
            init_monitor_result_schema(conn)

            conn.execute(
                """
                INSERT INTO monitor_target (
                  id, tenant_id, platform, target_type, label, target_url, host, status,
                  crawl_strategy, freshness_minutes, latest_snapshot_id, latest_snapshot_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?)
                """,
                (
                    "mt_001",
                    1,
                    "temu",
                    "shop",
                    "JIGGING PRO",
                    "https://www.temu.com/mall.html?mall_id=1",
                    "www.temu.com",
                    "active",
                    "store_listing",
                    1440,
                    "2026-07-07 09:00:00",
                    "2026-07-07 09:00:00",
                ),
            )
            conn.execute(
                """
                INSERT INTO monitor_job (
                  id, tenant_id, target_id, schedule_id, platform, trigger_type, status, attempt_no,
                  queued_at, started_at, finished_at, worker_id, error_code, error_message, error_detail,
                  snapshot_id, created_by, reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "mj_001",
                    1,
                    "mt_001",
                    None,
                    "temu",
                    "manual",
                    "pending",
                    1,
                    "2026-07-07 09:59:00",
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    9,
                    "manual refresh",
                ),
            )
            conn.commit()

            result = process_next_pending_job(
                conn,
                adapters={"temu": FakeTemuAdapter()},
                report_root=report_root,
                worker_id="worker-1",
            )

            self.assertEqual(result["job_id"], "mj_001")
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["product_count"], 2)
            self.assertEqual(result["recent_launch_count"], 1)
            self.assertEqual(result["sales_outlier_count"], 1)
            self.assertTrue(Path(result["report_xlsx_path"]).exists())
            self.assertTrue(Path(result["report_md_path"]).exists())

            job = conn.execute(
                "SELECT status, snapshot_id, worker_id FROM monitor_job WHERE id = ?",
                ("mj_001",),
            ).fetchone()
            self.assertEqual(dict(job), {"status": "success", "snapshot_id": result["snapshot_id"], "worker_id": "worker-1"})

            target = conn.execute(
                "SELECT latest_snapshot_id, latest_snapshot_at FROM monitor_target WHERE id = ?",
                ("mt_001",),
            ).fetchone()
            self.assertEqual(target["latest_snapshot_id"], result["snapshot_id"])
            self.assertEqual(target["latest_snapshot_at"], "2026-07-07 10:00:00")

            snapshot = conn.execute(
                """
                SELECT product_count, recent_launch_count, sales_outlier_count, report_md_path, report_xlsx_path
                FROM monitor_snapshot WHERE id = ?
                """,
                (result["snapshot_id"],),
            ).fetchone()
            self.assertEqual(snapshot["product_count"], 2)
            self.assertEqual(snapshot["recent_launch_count"], 1)
            self.assertEqual(snapshot["sales_outlier_count"], 1)
            self.assertTrue(snapshot["report_md_path"].endswith(".md"))
            self.assertTrue(snapshot["report_xlsx_path"].endswith(".xlsx"))

            signals = conn.execute(
                """
                SELECT signal_type, product_id
                FROM monitor_signal
                WHERE snapshot_id = ?
                ORDER BY signal_type, product_id
                """,
                (result["snapshot_id"],),
            ).fetchall()
            self.assertEqual(
                [(row["signal_type"], row["product_id"]) for row in signals],
                [("recent_launch", "p-100"), ("sales_outlier", "p-100")],
            )


if __name__ == "__main__":
    unittest.main()
