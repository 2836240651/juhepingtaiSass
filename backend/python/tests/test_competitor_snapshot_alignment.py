import json
import os
import sqlite3
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from app.monitor_db import init_monitor_result_schema, init_monitor_schema
from app.monitor_worker_service import process_next_pending_job
from app.platforms.temu_monitor_adapter import TemuMonitorAdapter


class TemuSnapshotAlignmentTest(unittest.TestCase):
    def test_adapter_reads_ctf_page_card_file_and_returns_monitor_products(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_file = Path(tmpdir) / "raw_products.json"
            evidence_file.write_text(
                json.dumps(
                    [
                        {
                            "goods_id": "900000000000001",
                            "title": "Synthetic Stable Product",
                            "price_yen": 500,
                            "sold_num": 100,
                            "sold_text": "100",
                            "href": "https://www.temu.com/jp-zh-Hans/synthetic-stable-product-g-900000000000001.html",
                        },
                        {
                            "goods_id": "900000000000002",
                            "title": "Synthetic Newer Product",
                            "price_yen": 750,
                            "sold_num": 1200,
                            "sold_text": "1,200",
                            "href": "https://www.temu.com/jp-zh-Hans/synthetic-newer-product-g-900000000000002.html",
                        },
                    ]
                ),
                encoding="utf-8",
            )

            payload = TemuMonitorAdapter().crawl_target(
                tenant_id=1,
                target={
                    "id": "mt_synthetic",
                    "target_url": "https://www.temu.com/mall.html?mall_id=synthetic_mall",
                    "ctf_page_card_file": str(evidence_file),
                    "captured_at": "2026-07-07T00:00:00+00:00",
                },
                max_products=10,
            )

        self.assertEqual(payload["platform"], "temu")
        self.assertEqual(payload["snapshot_at"], "2026-07-07 00:00:00")
        self.assertEqual([item["product_id"] for item in payload["products"]], ["900000000000002", "900000000000001"])
        self.assertEqual(payload["products"][0]["product_name"], "Synthetic Newer Product")
        self.assertEqual(payload["products"][0]["price"], 750.0)
        self.assertEqual(payload["products"][0]["daily_sales"], 1200)
        self.assertEqual(payload["products"][0]["total_sales"], 1200)
        self.assertEqual(payload["products"][0]["url"], "https://www.temu.com/jp-zh-Hans/synthetic-newer-product-g-900000000000002.html")

    def test_adapter_requires_ctf_evidence_and_does_not_call_legacy_playwright_crawler(self):
        with patch("app.crawler.competitor_crawler.crawl_competitor_products") as legacy_crawler:
            with self.assertRaisesRegex(RuntimeError, "MONITOR_SOURCE_UNAVAILABLE"):
                TemuMonitorAdapter().crawl_target(
                    tenant_id=1,
                    target={
                        "id": "mt_missing_evidence",
                        "target_url": "https://www.temu.com/mall.html?mall_id=synthetic_mall",
                    },
                    max_products=10,
                )

        legacy_crawler.assert_not_called()

    def test_adapter_collects_evidence_from_http_collector_when_enabled(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_root = Path(tmpdir) / "evidence"
            with run_fake_collector(evidence_root) as collector:
                old_evidence_dir = os.environ.get("CROSSHUB_MONITOR_EVIDENCE_DIR")
                old_collector_url = os.environ.get("CROSSHUB_TEMU_COLLECTOR_URL")
                os.environ["CROSSHUB_MONITOR_EVIDENCE_DIR"] = str(evidence_root)
                os.environ["CROSSHUB_TEMU_COLLECTOR_URL"] = collector.url
                try:
                    payload = TemuMonitorAdapter().crawl_target(
                        tenant_id=1,
                        target={
                            "id": "mt_collector_bridge",
                            "target_url": "https://www.temu.com/mall.html?mall_id=synthetic_bridge",
                            "captured_at": "2026-07-07T00:00:00+00:00",
                        },
                        max_products=10,
                    )
                finally:
                    restore_env("CROSSHUB_MONITOR_EVIDENCE_DIR", old_evidence_dir)
                    restore_env("CROSSHUB_TEMU_COLLECTOR_URL", old_collector_url)

            raw_products = evidence_root / "mt_collector_bridge" / "raw_products.json"
            raw_products_exists = raw_products.exists()

        self.assertTrue(raw_products_exists)
        self.assertEqual(collector.received["target_id"], "mt_collector_bridge")
        self.assertEqual(collector.received["tenant_id"], 1)
        self.assertEqual(collector.received["capture_mode"], "browser")
        self.assertEqual(collector.received["store_url"], "https://www.temu.com/mall.html?mall_id=synthetic_bridge")
        self.assertEqual(payload["platform"], "temu")
        self.assertEqual(payload["products"][0]["product_id"], "910000000000002")
        self.assertEqual(payload["products"][0]["product_name"], "Collector Bridge Newer")

    def test_adapter_force_refresh_recollects_even_when_stale_evidence_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_root = Path(tmpdir) / "evidence"
            target_dir = evidence_root / "mt_force_refresh"
            target_dir.mkdir(parents=True)
            (target_dir / "raw_products.json").write_text(
                json.dumps(
                    [
                        {
                            "goods_id": "900000000000001",
                            "title": "Stale Local Evidence",
                            "price_yen": 100,
                            "sold_num": 1,
                            "href": "https://www.temu.com/stale-local-evidence-g-900000000000001.html",
                        }
                    ]
                ),
                encoding="utf-8",
            )

            old_evidence_dir = os.environ.get("CROSSHUB_MONITOR_EVIDENCE_DIR")
            os.environ["CROSSHUB_MONITOR_EVIDENCE_DIR"] = str(evidence_root)
            try:
                def fake_collect(*, tenant_id: int, target: dict, target_url: str):
                    self.assertEqual(tenant_id, 1)
                    self.assertEqual(target["id"], "mt_force_refresh")
                    self.assertEqual(target_url, "https://www.temu.com/mall.html?mall_id=synthetic_force")
                    (target_dir / "raw_products.json").write_text(
                        json.dumps(
                            [
                                {
                                    "goods_id": "900000000000999",
                                    "title": "Fresh Collector Evidence",
                                    "price_yen": 880,
                                    "sold_num": 66,
                                    "href": "https://www.temu.com/fresh-collector-evidence-g-900000000000999.html",
                                }
                            ]
                        ),
                        encoding="utf-8",
                    )
                    return {"status": "OK"}

                with patch(
                    "app.platforms.temu_monitor_adapter.collect_evidence_from_http_collector",
                    side_effect=fake_collect,
                ) as collect:
                    payload = TemuMonitorAdapter().crawl_target(
                        tenant_id=1,
                        target={
                            "id": "mt_force_refresh",
                            "target_url": "https://www.temu.com/mall.html?mall_id=synthetic_force",
                            "captured_at": "2026-07-08T00:00:00+00:00",
                            "force_refresh": True,
                        },
                        max_products=10,
                    )
            finally:
                restore_env("CROSSHUB_MONITOR_EVIDENCE_DIR", old_evidence_dir)

        self.assertEqual(collect.call_count, 1)
        self.assertEqual(payload["products"][0]["product_id"], "900000000000999")
        self.assertEqual(payload["products"][0]["product_name"], "Fresh Collector Evidence")

    def test_adapter_maps_http_collector_timeout_to_monitor_timeout(self):
        with run_slow_collector() as collector:
            old_collector_url = os.environ.get("CROSSHUB_TEMU_COLLECTOR_URL")
            old_timeout = os.environ.get("CROSSHUB_TEMU_COLLECTOR_TIMEOUT_MS")
            os.environ["CROSSHUB_TEMU_COLLECTOR_URL"] = collector.url
            os.environ["CROSSHUB_TEMU_COLLECTOR_TIMEOUT_MS"] = "1"
            try:
                with self.assertRaisesRegex(RuntimeError, "MONITOR_TIMEOUT"):
                    TemuMonitorAdapter().crawl_target(
                        tenant_id=1,
                        target={
                            "id": "mt_collector_timeout",
                            "target_url": "https://www.temu.com/mall.html?mall_id=synthetic_timeout",
                        },
                        max_products=10,
                    )
            finally:
                restore_env("CROSSHUB_TEMU_COLLECTOR_URL", old_collector_url)
                restore_env("CROSSHUB_TEMU_COLLECTOR_TIMEOUT_MS", old_timeout)

    def test_monitor_worker_persists_snapshot_from_ctf_evidence_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_root = Path(tmpdir) / "evidence"
            target_dir = evidence_root / "mt_synthetic"
            target_dir.mkdir(parents=True)
            (target_dir / "raw_products.json").write_text(
                json.dumps(
                    [
                        {
                            "goods_id": "900000000000010",
                            "title": "Synthetic Worker Baseline",
                            "price_yen": 300,
                            "sold_num": 50,
                            "href": "https://www.temu.com/jp-zh-Hans/synthetic-worker-baseline-g-900000000000010.html",
                        },
                        {
                            "goods_id": "900000000000011",
                            "title": "Synthetic Worker Outlier",
                            "price_yen": 900,
                            "sold_num": 5000,
                            "href": "https://www.temu.com/jp-zh-Hans/synthetic-worker-outlier-g-900000000000011.html",
                        },
                    ]
                ),
                encoding="utf-8",
            )
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
                    "mt_synthetic",
                    1,
                    "temu",
                    "shop",
                    "Synthetic Store",
                    "https://www.temu.com/mall.html?mall_id=synthetic_mall",
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
                    "mt_synthetic",
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
            old_evidence_dir = os.environ.get("CROSSHUB_MONITOR_EVIDENCE_DIR")
            os.environ["CROSSHUB_MONITOR_EVIDENCE_DIR"] = str(evidence_root)
            try:
                result = process_next_pending_job(
                    conn,
                    adapters={"temu": TemuMonitorAdapter()},
                    report_root=Path(tmpdir) / "reports",
                    worker_id="worker-snapshot",
                )
            finally:
                if old_evidence_dir is None:
                    os.environ.pop("CROSSHUB_MONITOR_EVIDENCE_DIR", None)
                else:
                    os.environ["CROSSHUB_MONITOR_EVIDENCE_DIR"] = old_evidence_dir

            self.assertEqual(result["status"], "success")
            self.assertEqual(result["product_count"], 2)
            snapshot = conn.execute(
                "SELECT product_count FROM monitor_snapshot WHERE id = ?",
                (result["snapshot_id"],),
            ).fetchone()
            self.assertEqual(snapshot["product_count"], 2)
            product_ids = [
                row["product_id"]
                for row in conn.execute(
                    "SELECT product_id FROM monitor_product_snapshot WHERE snapshot_id = ? ORDER BY product_id",
                    (result["snapshot_id"],),
                ).fetchall()
            ]
            self.assertEqual(product_ids, ["900000000000010", "900000000000011"])


class run_fake_collector:
    def __init__(self, evidence_root: Path):
        self.evidence_root = evidence_root
        self.received = {}

    def __enter__(self):
        owner = self

        class FakeCollectorHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                content_length = int(self.headers.get("Content-Length") or 0)
                request = json.loads(self.rfile.read(content_length).decode("utf-8"))
                owner.received = request
                target_dir = owner.evidence_root / request["target_id"]
                target_dir.mkdir(parents=True, exist_ok=True)
                (target_dir / "raw_products.json").write_text(
                    json.dumps(
                        [
                            {
                                "goods_id": "910000000000001",
                                "title": "Collector Bridge Baseline",
                                "price_yen": 500,
                                "sold_num": 20,
                                "href": "https://www.temu.com/collector-bridge-baseline-g-910000000000001.html",
                            },
                            {
                                "goods_id": "910000000000002",
                                "title": "Collector Bridge Newer",
                                "price_yen": 900,
                                "sold_num": 48,
                                "href": "https://www.temu.com/collector-bridge-newer-g-910000000000002.html",
                            },
                        ]
                    ),
                    encoding="utf-8",
                )
                self.write_json(
                    {
                        "status": "OK",
                        "target_id": request["target_id"],
                        "raw_products_file": str(target_dir / "raw_products.json"),
                        "product_count": 2,
                        "source_type": "AUTHORIZED_BROWSER_SESSION",
                    }
                )

            def write_json(self, payload):
                encoded = json.dumps(payload).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                try:
                    self.wfile.write(encoded)
                except (BrokenPipeError, ConnectionAbortedError):
                    pass

            def log_message(self, format, *args):
                return

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), FakeCollectorHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://{self.server.server_address[0]}:{self.server.server_address[1]}"
        return self

    def __exit__(self, exc_type, exc, tb):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)


class run_slow_collector:
    def __enter__(self):
        class SlowCollectorHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                time.sleep(0.2)
                encoded = b'{"status":"OK"}'
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                try:
                    self.wfile.write(encoded)
                except (BrokenPipeError, ConnectionAbortedError):
                    pass

            def log_message(self, format, *args):
                return

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), SlowCollectorHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://{self.server.server_address[0]}:{self.server.server_address[1]}"
        return self

    def __exit__(self, exc_type, exc, tb):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)


def restore_env(name: str, value: str | None) -> None:
    if value is None:
        os.environ.pop(name, None)
    else:
        os.environ[name] = value


if __name__ == "__main__":
    unittest.main()
