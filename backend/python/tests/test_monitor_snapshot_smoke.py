import tempfile
import unittest
from pathlib import Path

from smoke_monitor_snapshot import run_synthetic_smoke


class MonitorSnapshotSmokeTest(unittest.TestCase):
    def test_synthetic_smoke_runs_monitor_job_from_evidence_to_signals(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_synthetic_smoke(Path(tmpdir))

        self.assertEqual(result["job_status"], "success")
        self.assertEqual(result["product_count"], 4)
        self.assertGreaterEqual(result["recent_launch_count"], 1)
        self.assertGreaterEqual(result["sales_outlier_count"], 1)
        self.assertEqual(result["target_latest_snapshot_id"], result["snapshot_id"])
        self.assertEqual(result["signal_types"], ["recent_launch", "sales_outlier"])
        self.assertTrue(result["report_md_exists"])
        self.assertTrue(result["report_xlsx_exists"])


if __name__ == "__main__":
    unittest.main()
