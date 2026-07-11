import sqlite3
import json

c = sqlite3.connect(r"d:\NIUBI\SaaS-HZ_WEB_Demo\backend\data\crosshub.db")
r = c.execute(
    "SELECT result_json FROM agent_task WHERE task_type='amazon_sync' AND status='success' ORDER BY finished_at DESC LIMIT 1"
).fetchone()
if r and r[0]:
    d = json.loads(r[0])
    prods = d.get("products") or []
    print("latest success products", len(prods))
    for p in prods[:3]:
        print(p)
else:
    print("no result json")

