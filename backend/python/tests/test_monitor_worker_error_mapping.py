import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from app.monitor_db import init_monitor_result_schema, init_monitor_schema
from app.monitor_worker_service import process_next_pending_job
from app.platforms.temu_monitor_adapter import TemuMonitorAdapter


class MonitorWorkerErrorMappingTest(unittest.TestCase):
    def test_no_products_preserves_monitor_error_code(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_root = Path(tmpdir) / "evidence"
            target_dir = evidence_root / "mt_empty"
            target_dir.mkdir(parents=True)
            (target_dir / "raw_products.json").write_text(json.dumps([]), encoding="utf-8")
            conn = build_conn("mt_empty", "https://www.temu.com/mall.html?mall_id=synthetic_mall")
            old_evidence_dir = os.environ.get("CROSSHUB_MONITOR_EVIDENCE_DIR")
            os.environ["CROSSHUB_MONITOR_EVIDENCE_DIR"] = str(evidence_root)
            try:
                with self.assertRaisesRegex(RuntimeError, "MONITOR_NO_PRODUCTS"):
                    process_next_pending_job(
                        conn,
                        adapters={"temu": TemuMonitorAdapter()},
                        report_root=Path(tmpdir) / "reports",
                    )
            finally:
                if old_evidence_dir is None:
                    os.environ.pop("CROSSHUB_MONITOR_EVIDENCE_DIR", None)
                else:
                    os.environ["CROSSHUB_MONITOR_EVIDENCE_DIR"] = old_evidence_dir

            job = conn.execute("SELECT status, error_code FROM monitor_job WHERE id = 'mj_synthetic'").fetchone()
            self.assertEqual(job["status"], "failed")
            self.assertEqual(job["error_code"], "MONITOR_NO_PRODUCTS")

    def test_invalid_url_preserves_monitor_error_code(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = build_conn("mt_invalid", "https://example.test/synthetic-store")

            with self.assertRaisesRegex(RuntimeError, "MONITOR_INVALID_URL"):
                process_next_pending_job(
                    conn,
                    adapters={"temu": TemuMonitorAdapter()},
                    report_root=Path(tmpdir) / "reports",
                )

            job = conn.execute("SELECT status, error_code FROM monitor_job WHERE id = 'mj_synthetic'").fetchone()
            self.assertEqual(job["status"], "failed")
            self.assertEqual(job["error_code"], "MONITOR_INVALID_URL")


def build_conn(target_id: str, target_url: str) -> sqlite3.Connection:
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
            target_id,
            1,
            "temu",
            "shop",
            "Synthetic Store",
            target_url,
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
            "mj_synthetic",
            1,
            target_id,
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
    return conn


if __name__ == "__main__":
    unittest.main()
