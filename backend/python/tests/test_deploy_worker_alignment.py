import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


class DeployWorkerAlignmentTest(unittest.TestCase):
    def test_deploy_artifacts_define_python_worker(self):
        dockerfile = ROOT / "deploy" / "Dockerfile.python-worker"
        compose = (ROOT / "deploy" / "docker-compose.yml").read_text(encoding="utf-8")
        deploy_script = (ROOT / "scripts" / "deploy-server.js").read_text(encoding="utf-8")

        self.assertTrue(dockerfile.exists())
        self.assertIn("crosshub-python-worker", compose)
        self.assertIn("CROSSHUB_DB_PATH: /data/crosshub.db", compose)
        self.assertIn("CROSSHUB_MONITOR_EVIDENCE_DIR: /evidence", compose)
        self.assertIn("Dockerfile.python-worker", deploy_script)
        self.assertIn("python-src", deploy_script)
        self.assertIn("docker build -f Dockerfile.python-worker -t crosshub-python-worker:latest python-src", deploy_script)

    def test_deploy_script_verifies_python_worker_after_start(self):
        deploy_script = (ROOT / "scripts" / "deploy-server.js").read_text(encoding="utf-8")

        self.assertIn("mkdir -p ${REMOTE_ROOT}/data ${REMOTE_ROOT}/evidence ${REMOTE_ROOT}/reports", deploy_script)
        self.assertIn("docker inspect -f '{{.State.Running}}' crosshub-python-worker", deploy_script)
        self.assertIn("test \"$(docker inspect -f '{{.State.Running}}' crosshub-python-worker)\" = \"true\"", deploy_script)
        self.assertIn("docker exec crosshub-python-worker python smoke_monitor_snapshot.py --work-dir /tmp/monitor-smoke", deploy_script)

    def test_deploy_script_can_run_remote_monitor_api_smoke(self):
        deploy_script = (ROOT / "scripts" / "deploy-server.js").read_text(encoding="utf-8")

        self.assertIn("monitor-api-smoke.js", deploy_script)
        self.assertIn("${REMOTE_ROOT}/scripts/monitor-api-smoke.js", deploy_script)
        self.assertIn("if [ -f ${REMOTE_ROOT}/.monitor-smoke.env ]; then", deploy_script)
        self.assertIn(". ${REMOTE_ROOT}/.monitor-smoke.env", deploy_script)
        self.assertIn("docker run --rm --network host", deploy_script)
        self.assertIn("node:20-alpine", deploy_script)
        self.assertIn("node /scripts/monitor-api-smoke.js --base-url http://127.0.0.1:18080", deploy_script)
        self.assertNotIn("  node scripts/monitor-api-smoke.js --base-url http://127.0.0.1:18080", deploy_script)
        self.assertIn("--evidence-root ${REMOTE_ROOT}/evidence", deploy_script)
        self.assertIn("--db-path ${REMOTE_ROOT}/data/crosshub.db", deploy_script)
        self.assertIn("--no-local-worker", deploy_script)

    def test_monitor_smoke_env_template_is_safe_and_private_env_is_ignored(self):
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        template_path = ROOT / "deploy" / "monitor-smoke.env.example"

        self.assertIn(".monitor-smoke.env", gitignore)
        self.assertTrue(template_path.exists())
        template = template_path.read_text(encoding="utf-8")
        self.assertIn("CROSSHUB_MONITOR_API_TOKEN=", template)
        self.assertIn("CROSSHUB_MONITOR_LOGIN_ACCOUNT=", template)
        self.assertIn("CROSSHUB_MONITOR_LOGIN_PASSWORD=", template)
        self.assertNotIn("12345678", template)
        self.assertNotIn("Bearer ", template)
        self.assertNotRegex(template, r"mall_id=\d{6,}")

    def test_deploy_script_runs_preflight_before_building(self):
        deploy_script = (ROOT / "scripts" / "deploy-server.js").read_text(encoding="utf-8")

        self.assertIn("node scripts/deploy-preflight.js", deploy_script)
        self.assertLess(
            deploy_script.index("node scripts/deploy-preflight.js"),
            deploy_script.index("==> build Java JAR"),
        )
        self.assertLess(
            deploy_script.index("node scripts/deploy-preflight.js"),
            deploy_script.index("require('ssh2')"),
        )
        self.assertNotIn("Set CROSSHUB_SSH_HOST and CROSSHUB_SSH_PASSWORD before deploying.", deploy_script)

    def test_production_runbook_records_required_evidence(self):
        checklist = (ROOT / "docs" / "competitor-snapshot-integration" / "01-对齐清单.md").read_text(encoding="utf-8")
        runbook_path = ROOT / "docs" / "competitor-snapshot-integration" / "02-生产联调运行手册.md"
        runbook = runbook_path.read_text(encoding="utf-8")

        self.assertTrue(runbook_path.exists())
        self.assertIn("02-生产联调运行手册.md", checklist)
        self.assertIn("## 7. 通过标准", runbook)
        self.assertIn("## 8. 失败定位", runbook)
        self.assertIn("## 10. 实机记录模板", runbook)
        self.assertIn("crosshub-python-worker", runbook)
        self.assertIn("node:20-alpine", runbook)
        self.assertIn("deploy_preflight_ok", runbook)
        self.assertIn("status=ok", runbook)
        self.assertIn("product_count > 0", runbook)
        self.assertIn("不引入 Playwright 兜底", runbook)
        self.assertNotRegex(runbook, r"[A-Z]:\\")
        self.assertNotRegex(runbook, r"mall_id=\d{6,}")
        self.assertNotRegex(runbook, r"CROSSHUB_(?:SSH_PASSWORD|MONITOR_API_TOKEN|MONITOR_LOGIN_PASSWORD)=.+")

    def test_competitor_snapshot_integration_docs_have_index(self):
        index_path = ROOT / "docs" / "competitor-snapshot-integration" / "README.md"

        self.assertTrue(index_path.exists())
        index = index_path.read_text(encoding="utf-8")
        self.assertIn("01-对齐清单.md", index)
        self.assertIn("02-生产联调运行手册.md", index)
        self.assertIn("crosshub-python-worker", index)
        self.assertIn("/api/monitor/*", index)
        self.assertIn("boards/ctf-website", index)
        self.assertIn("不恢复 Playwright", index)
        self.assertIn("CROSSHUB_SSH_HOST", index)
        self.assertIn("CROSSHUB_REMOTE_MONITOR_SMOKE_ENV_READY=true", index)
        self.assertNotRegex(index, r"[A-Z]:\\")
        self.assertNotRegex(index, r"mall_id=\d{6,}")
        self.assertNotRegex(index, r"CROSSHUB_(?:SSH_PASSWORD|MONITOR_API_TOKEN|MONITOR_LOGIN_PASSWORD)=.+")


if __name__ == "__main__":
    unittest.main()
