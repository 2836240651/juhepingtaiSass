"""SQLite 数据库：与 Java 后端共用 backend/data/crosshub.db"""
from __future__ import annotations

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "crosshub.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS app_user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE,
  password TEXT NOT NULL,
  nickname TEXT NOT NULL DEFAULT '',
  enterprise TEXT NOT NULL DEFAULT '',
  role TEXT NOT NULL DEFAULT 'user'
);

CREATE TABLE IF NOT EXISTS temu_shop (
  shop_id TEXT PRIMARY KEY,
  shop_name TEXT NOT NULL,
  is_upload INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS temu_sale (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  platform TEXT NOT NULL DEFAULT 'temu',
  status TEXT NOT NULL DEFAULT '300',
  report_time TEXT NOT NULL,
  shop_name TEXT NOT NULL,
  shop_id TEXT NOT NULL,
  user_id INTEGER NOT NULL DEFAULT 1,
  cost INTEGER NOT NULL DEFAULT 0,
  category_name TEXT NOT NULL DEFAULT '',
  img_url TEXT NOT NULL DEFAULT '',
  title TEXT NOT NULL,
  skc TEXT NOT NULL DEFAULT '',
  spu TEXT NOT NULL DEFAULT '',
  ext_code TEXT NOT NULL,
  son_sku TEXT NOT NULL DEFAULT '',
  son_price INTEGER NOT NULL DEFAULT 0,
  son_today_sales INTEGER NOT NULL DEFAULT 0,
  son_sales_seven_days INTEGER NOT NULL DEFAULT 0,
  son_sales_thirty_days INTEGER NOT NULL DEFAULT 0,
  join_site_time INTEGER NOT NULL DEFAULT 0,
  warehouse_available_stock INTEGER NOT NULL DEFAULT 0,
  nickname TEXT NOT NULL DEFAULT '',
  username TEXT NOT NULL DEFAULT '',
  enterprise TEXT NOT NULL DEFAULT '',
  UNIQUE (report_time, shop_id, ext_code)
);
"""


def connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def seed_users(conn: sqlite3.Connection) -> None:
    users = [
        ("admin@crosshub.cn", "12345678", "管理员", "泰州亿拓户外用品有限公司", "admin"),
        ("wangyiming@yituo-outdoor.com", "Emp@Demo123", "王一鸣", "泰州亿拓户外用品有限公司", "user"),
        ("liting@yituo-outdoor.com", "Emp@Demo456", "李婷", "泰州亿拓户外用品有限公司", "user"),
    ]
    for username, password, nickname, enterprise, role in users:
        conn.execute(
            """
            INSERT OR IGNORE INTO app_user (username, password, nickname, enterprise, role)
            VALUES (?, ?, ?, ?, ?)
            """,
            (username, password, nickname, enterprise, role),
        )
    conn.commit()
