import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from app import db
from monitor_worker import run_worker_loop


class MonitorWorkerRuntimeTest(unittest.TestCase):
    def test_run_worker_loop_repeats_until_idle_limit(self):
        calls = []
        sleeps = []

        def process_once():
            calls.append(len(calls))
            if len(calls) == 1:
                return {"status": "success", "job_id": "job_synthetic"}
            return None

        results = run_worker_loop(
            process_once=process_once,
            sleep_fn=lambda seconds: sleeps.append(seconds),
            interval_seconds=0.25,
            max_idle_cycles=1,
        )

        self.assertEqual(len(calls), 2)
        self.assertEqual(results, [{"status": "success", "job_id": "job_synthetic"}, {"status": "idle"}])
        self.assertEqual(sleeps, [0.25])

    def test_db_connect_uses_crosshub_db_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_db = Path(tmpdir) / "custom" / "crosshub.db"
            old_value = os.environ.get("CROSSHUB_DB_PATH")
            os.environ["CROSSHUB_DB_PATH"] = str(custom_db)
            try:
                conn = db.connect()
                try:
                    conn.execute("CREATE TABLE proof (id INTEGER PRIMARY KEY)")
                    conn.commit()
                finally:
                    conn.close()
            finally:
                if old_value is None:
                    os.environ.pop("CROSSHUB_DB_PATH", None)
                else:
                    os.environ["CROSSHUB_DB_PATH"] = old_value

            self.assertTrue(custom_db.exists())
            check = sqlite3.connect(custom_db)
            try:
                row = check.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'proof'"
                ).fetchone()
            finally:
                check.close()
            self.assertIsNotNone(row)

    def test_local_restart_script_sets_worker_db_and_evidence_env(self):
        root = Path(__file__).resolve().parents[3]
        restart_script = (root / "scripts" / "restart-java-vue.ps1").read_text(encoding="utf-8")
        launcher_utils = (root / "scripts" / "_launcher-utils.ps1").read_text(encoding="utf-8")

        self.assertIn("$env:CROSSHUB_DB_PATH='$Root\\backend\\data\\crosshub.db'", restart_script)
        self.assertIn("$env:CROSSHUB_MONITOR_EVIDENCE_DIR='$Root\\backend\\python\\exports\\ctf-website'", restart_script)
        self.assertIn("$env:CROSSHUB_TEMU_COLLECTOR_URL='http://127.0.0.1:18082'", restart_script)
        self.assertIn("temu_collector_service.py", restart_script)
        self.assertIn('collector = "crosshub-collector.ps1"', launcher_utils)


if __name__ == "__main__":
    unittest.main()
