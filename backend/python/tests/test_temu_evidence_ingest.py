import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from app.monitor_db import init_monitor_result_schema, init_monitor_schema
from app.external_snapshot.competitor_snapshot.providers.temu import TemuProvider
from app.monitor_worker_service import process_next_pending_job
from app.platforms.temu_monitor_adapter import TemuMonitorAdapter
from app.platforms.temu_evidence import extract_raw_products, ingest_evidence_file


class TemuEvidenceIngestTest(unittest.TestCase):
    def test_provider_capabilities_declare_har_and_payload_evidence(self):
        supported = TemuProvider().capabilities()["supported_evidence"]

        self.assertIn("evidence.raw_payload_json", supported)
        self.assertIn("evidence.har", supported)

    def test_extracts_raw_products_from_nested_api_payload(self):
        payload = {
            "result": {
                "store": {"mallId": "synthetic_mall"},
                "items": [
                    {
                        "goodsId": "900000000000101",
                        "goodsName": "Synthetic Payload Jig",
                        "priceInfo": {"price": "1299"},
                        "soldQuantity": "1,200",
                        "linkUrl": "https://www.temu.com/synthetic-payload-jig-g-900000000000101.html",
                    }
                ],
            }
        }

        products = extract_raw_products(payload)

        self.assertEqual(
            products,
            [
                {
                    "goods_id": "900000000000101",
                    "title": "Synthetic Payload Jig",
                    "price_yen": 1299.0,
                    "sold_num": 1200,
                    "sold_text": "1,200",
                    "href": "https://www.temu.com/synthetic-payload-jig-g-900000000000101.html",
                }
            ],
        )

    def test_ingests_har_response_into_raw_products_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_dir = Path(tmpdir) / "mt_synthetic_har"
            evidence_dir.mkdir()
            har_file = evidence_dir / "capture.har"
            har_file.write_text(
                json.dumps(
                    {
                        "log": {
                            "entries": [
                                {
                                    "request": {"url": "https://www.temu.com/api/mall/items"},
                                    "response": {
                                        "content": {
                                            "mimeType": "application/json",
                                            "text": json.dumps(
                                                {
                                                    "goodsList": [
                                                        {
                                                            "goods_id": "900000000000201",
                                                            "title": "Synthetic HAR Rod",
                                                            "price": {"amount": 880},
                                                            "sales": {"value": 88, "raw_text": "88"},
                                                            "url": "https://www.temu.com/synthetic-har-rod-g-900000000000201.html",
                                                        }
                                                    ]
                                                }
                                            ),
                                        }
                                    },
                                }
                            ]
                        }
                    }
                ),
                encoding="utf-8",
            )

            raw_file = ingest_evidence_file(har_file, evidence_dir / "raw_products.json")
            loaded = json.loads(raw_file.read_text(encoding="utf-8"))

        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]["goods_id"], "900000000000201")
        self.assertEqual(loaded[0]["title"], "Synthetic HAR Rod")
        self.assertEqual(loaded[0]["price_yen"], 880.0)
        self.assertEqual(loaded[0]["sold_num"], 88)

    def test_ingests_payload_with_utf8_bom(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            source_file = Path(tmpdir) / "payload.json"
            source_file.write_text(
                json.dumps(
                    {
                        "items": [
                            {
                                "goodsId": "900000000000202",
                                "goodsName": "Synthetic BOM Payload",
                                "priceInfo": {"price": 420},
                                "soldQuantity": 12,
                                "linkUrl": "https://www.temu.com/synthetic-bom-payload-g-900000000000202.html",
                            }
                        ]
                    }
                ),
                encoding="utf-8-sig",
            )

            raw_file = ingest_evidence_file(source_file, Path(tmpdir) / "raw_products.json")
            loaded = json.loads(raw_file.read_text(encoding="utf-8"))

        self.assertEqual(loaded[0]["goods_id"], "900000000000202")

    def test_monitor_worker_converts_har_evidence_before_snapshot(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_root = Path(tmpdir) / "evidence"
            target_dir = evidence_root / "mt_synthetic_har"
            target_dir.mkdir(parents=True)
            (target_dir / "network.har").write_text(
                json.dumps(
                    {
                        "log": {
                            "entries": [
                                {
                                    "request": {"url": "https://www.temu.com/api/mall/items"},
                                    "response": {
                                        "content": {
                                            "mimeType": "application/json",
                                            "text": json.dumps(
                                                {
                                                    "items": [
                                                        {
                                                            "goodsId": "900000000000301",
                                                            "goodsName": "Synthetic Worker HAR Lure",
                                                            "priceInfo": {"price": 760},
                                                            "soldQuantity": 66,
                                                            "linkUrl": "https://www.temu.com/synthetic-worker-har-lure-g-900000000000301.html",
                                                        }
                                                    ]
                                                }
                                            ),
                                        }
                                    },
                                }
                            ]
                        }
                    }
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
                    "mt_synthetic_har",
                    1,
                    "temu",
                    "shop",
                    "Synthetic HAR Store",
                    "https://www.temu.com/mall.html?mall_id=synthetic_har",
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
                    "mj_synthetic_har",
                    1,
                    "mt_synthetic_har",
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
                    worker_id="worker-har",
                )
            finally:
                if old_evidence_dir is None:
                    os.environ.pop("CROSSHUB_MONITOR_EVIDENCE_DIR", None)
                else:
                    os.environ["CROSSHUB_MONITOR_EVIDENCE_DIR"] = old_evidence_dir

            self.assertEqual(result["status"], "success")
            self.assertEqual(result["product_count"], 1)
            self.assertTrue((target_dir / "raw_products.json").exists())
            product = conn.execute(
                "SELECT product_id, product_name, price, daily_sales FROM monitor_product_snapshot WHERE snapshot_id = ?",
                (result["snapshot_id"],),
            ).fetchone()
            self.assertEqual(dict(product), {
                "product_id": "900000000000301",
                "product_name": "Synthetic Worker HAR Lure",
                "price": 760.0,
                "daily_sales": 66,
            })

    def test_cli_runner_imports_payload_for_target(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            source_file = Path(tmpdir) / "payload.json"
            evidence_root = Path(tmpdir) / "evidence"
            source_file.write_text(
                json.dumps(
                    {
                        "items": [
                            {
                                "goodsId": "900000000000401",
                                "goodsName": "Synthetic CLI Import",
                                "priceInfo": {"price": 990},
                                "soldQuantity": 77,
                                "linkUrl": "https://www.temu.com/synthetic-cli-import-g-900000000000401.html",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            from temu_evidence_ingest import run_import

            result = run_import(
                source_file=source_file,
                target_id="mt_cli_import",
                evidence_root=evidence_root,
            )
            raw_file = evidence_root / "mt_cli_import" / "raw_products.json"
            loaded = json.loads(raw_file.read_text(encoding="utf-8"))

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["product_count"], 1)
        self.assertEqual(loaded[0]["goods_id"], "900000000000401")


if __name__ == "__main__":
    unittest.main()
