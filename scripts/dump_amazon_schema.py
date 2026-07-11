import sqlite3
from pathlib import Path

db = Path(__file__).resolve().parents[1] / "backend/data/crosshub.db"
c = sqlite3.connect(db)
for name in [
    "amazon_sync_job",
    "integration_agent",
    "agent_task",
    "amazon_product_snapshot",
    "amazon_account_metric",
    "amazon_operational_item",
]:
    row = c.execute("SELECT sql FROM sqlite_master WHERE name=?", (name,)).fetchone()
    print("---", name)
    print(row[0] if row else "MISSING")
