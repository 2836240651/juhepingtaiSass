#!/usr/bin/env python3
"""Synthetic smoke test for the monitor snapshot worker path."""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import tempfile
from pathlib import Path
from typing import Any

from app.db import init_schema, seed_users
from app.monitor_db import init_monitor_result_schema, init_monitor_schema
from monitor_worker import process_one_job


TARGET_ID = "mt_synthetic_smoke"
JOB_ID = "mj_synthetic_smoke"


def run_synthetic_smoke(work_dir: Path | None = None) -> dict[str, Any]:
    if work_dir is None:
        with tempfile.TemporaryDirectory() as tmpdir:
            return _run_synthetic_smoke(Path(tmpdir))
    return _run_synthetic_smoke(work_dir)


def _run_synthetic_smoke(work_dir: Path) -> dict[str, Any]:
    work_dir.mkdir(parents=True, exist_ok=True)
    db_path = work_dir / "crosshub-smoke.db"
    evidence_root = work_dir / "evidence"
    report_root = work_dir / "reports"
    target_evidence_dir = evidence_root / TARGET_ID
    target_evidence_dir.mkdir(parents=True, exist_ok=True)
    (target_evidence_dir / "raw_products.json").write_text(
        json.dumps(synthetic_page_cards(), ensure_ascii=False),
        encoding="utf-8",
    )

    old_db_path = os.environ.get("CROSSHUB_DB_PATH")
    old_evidence_dir = os.environ.get("CROSSHUB_MONITOR_EVIDENCE_DIR")
    os.environ["CROSSHUB_DB_PATH"] = str(db_path)
    os.environ["CROSSHUB_MONITOR_EVIDENCE_DIR"] = str(evidence_root)
    try:
        prepare_smoke_db(db_path)
        worker_result = process_one_job(worker_id="smoke-worker", report_root=report_root)
        return collect_smoke_result(db_path, worker_result or {})
    finally:
        restore_env("CROSSHUB_DB_PATH", old_db_path)
        restore_env("CROSSHUB_MONITOR_EVIDENCE_DIR", old_evidence_dir)


def synthetic_page_cards() -> list[dict[str, Any]]:
    return [
        {
            "goods_id": "1001",
            "title": "Synthetic Smoke Baseline",
            "price_yen": 500,
            "sold_num": 20,
            "sold_text": "20",
            "href": "https://www.temu.com/jp-zh-Hans/synthetic-smoke-baseline-g-1001.html",
        },
        {
            "goods_id": "1002",
            "title": "Synthetic Smoke Stable",
            "price_yen": 650,
            "sold_num": 25,
            "sold_text": "25",
            "href": "https://www.temu.com/jp-zh-Hans/synthetic-smoke-stable-g-1002.html",
        },
        {
            "goods_id": "1003",
            "title": "Synthetic Smoke Rising",
            "price_yen": 900,
            "sold_num": 30,
            "sold_text": "30",
            "href": "https://www.temu.com/jp-zh-Hans/synthetic-smoke-rising-g-1003.html",
        },
        {
            "goods_id": "1004",
            "title": "Synthetic Smoke Outlier",
            "price_yen": 1200,
            "sold_num": 5000,
            "sold_text": "5,000",
            "href": "https://www.temu.com/jp-zh-Hans/synthetic-smoke-outlier-g-1004.html",
        },
    ]


def prepare_smoke_db(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        init_schema(conn)
        seed_users(conn)
        init_monitor_schema(conn)
        init_monitor_result_schema(conn)
        now = "2026-07-07 09:00:00"
        conn.execute(
            """
            INSERT INTO monitor_target (
              id, tenant_id, platform, target_type, label, target_url, host, status,
              crawl_strategy, freshness_minutes, latest_snapshot_id, latest_snapshot_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?)
            """,
            (
                TARGET_ID,
                1,
                "temu",
                "shop",
                "Synthetic Smoke Store",
                "https://www.temu.com/mall.html?mall_id=synthetic_smoke",
                "www.temu.com",
                "active",
                "store_listing",
                1440,
                now,
                now,
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
                JOB_ID,
                1,
                TARGET_ID,
                None,
                "temu",
                "manual",
                "pending",
                1,
                "2026-07-07 09:01:00",
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                1,
                "synthetic smoke",
            ),
        )
        conn.commit()
    finally:
        conn.close()


def collect_smoke_result(db_path: Path, worker_result: dict[str, Any]) -> dict[str, Any]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        job = conn.execute("SELECT status, snapshot_id FROM monitor_job WHERE id = ?", (JOB_ID,)).fetchone()
        target = conn.execute("SELECT latest_snapshot_id FROM monitor_target WHERE id = ?", (TARGET_ID,)).fetchone()
        snapshot = conn.execute(
            """
            SELECT id, product_count, recent_launch_count, sales_outlier_count, report_md_path, report_xlsx_path
            FROM monitor_snapshot
            WHERE target_id = ?
            LIMIT 1
            """,
            (TARGET_ID,),
        ).fetchone()
        signal_types = [
            row["signal_type"]
            for row in conn.execute(
                "SELECT DISTINCT signal_type FROM monitor_signal WHERE target_id = ? ORDER BY signal_type",
                (TARGET_ID,),
            ).fetchall()
        ]
    finally:
        conn.close()

    report_md = Path(snapshot["report_md_path"]) if snapshot else Path("")
    report_xlsx = Path(snapshot["report_xlsx_path"]) if snapshot else Path("")
    return {
        "status": "ok" if job and job["status"] == "success" else "failed",
        "job_id": JOB_ID,
        "job_status": job["status"] if job else "",
        "snapshot_id": snapshot["id"] if snapshot else "",
        "target_latest_snapshot_id": target["latest_snapshot_id"] if target else "",
        "product_count": int(snapshot["product_count"] if snapshot else 0),
        "recent_launch_count": int(snapshot["recent_launch_count"] if snapshot else 0),
        "sales_outlier_count": int(snapshot["sales_outlier_count"] if snapshot else 0),
        "signal_types": signal_types,
        "report_md_exists": report_md.exists(),
        "report_xlsx_exists": report_xlsx.exists(),
        "worker_result": worker_result,
    }


def restore_env(name: str, old_value: str | None) -> None:
    if old_value is None:
        os.environ.pop(name, None)
    else:
        os.environ[name] = old_value


def main() -> None:
    parser = argparse.ArgumentParser(description="Run synthetic monitor snapshot smoke test")
    parser.add_argument("--work-dir", type=Path, help="Directory for synthetic DB, evidence, and reports")
    args = parser.parse_args()
    print(json.dumps(run_synthetic_smoke(args.work_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
