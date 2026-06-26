"""SQLite 数据库：与 Java 后端共用 backend/data/crosshub.db"""
from __future__ import annotations

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "crosshub.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS tenant (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  code TEXT NOT NULL UNIQUE,
  status TEXT NOT NULL DEFAULT 'active'
);

CREATE TABLE IF NOT EXISTS app_user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tenant_id INTEGER,
  username TEXT NOT NULL UNIQUE,
  password TEXT NOT NULL,
  nickname TEXT NOT NULL DEFAULT '',
  enterprise TEXT NOT NULL DEFAULT '',
  job_title TEXT NOT NULL DEFAULT '',
  role TEXT NOT NULL DEFAULT 'user',
  phone TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'active',
  created_at TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS sys_menu (
  code TEXT PRIMARY KEY,
  parent_code TEXT,
  portal TEXT NOT NULL,
  platform TEXT,
  path TEXT NOT NULL,
  label TEXT NOT NULL,
  menu_type TEXT NOT NULL,
  sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS tenant_feature (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tenant_id INTEGER NOT NULL,
  feature_code TEXT NOT NULL,
  enabled INTEGER NOT NULL DEFAULT 1,
  UNIQUE (tenant_id, feature_code)
);

CREATE TABLE IF NOT EXISTS user_platform_scope (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tenant_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  platform TEXT NOT NULL,
  UNIQUE (tenant_id, user_id, platform)
);

CREATE TABLE IF NOT EXISTS user_shop_scope (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tenant_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  platform TEXT NOT NULL,
  shop_id TEXT NOT NULL,
  UNIQUE (tenant_id, user_id, platform, shop_id)
);

CREATE TABLE IF NOT EXISTS user_menu_grant (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tenant_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  menu_code TEXT NOT NULL,
  UNIQUE (tenant_id, user_id, menu_code)
);

CREATE TABLE IF NOT EXISTS temu_shop (
  shop_id TEXT PRIMARY KEY,
  tenant_id INTEGER NOT NULL DEFAULT 1,
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
  tenant_id INTEGER NOT NULL DEFAULT 1,
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
    conn.execute("""
        INSERT OR IGNORE INTO tenant (id, name, code, status)
        VALUES (1, '泰州亿拓户外用品有限公司', 'yituo-outdoor', 'active')
    """)
    users = [
        ("admin@crosshub.cn", "12345678", "管理员", "泰州亿拓户外用品有限公司", "admin"),
        ("wangyiming@yituo-outdoor.com", "Emp@Demo123", "王一鸣", "泰州亿拓户外用品有限公司", "user"),
        ("liting@yituo-outdoor.com", "Emp@Demo456", "李婷", "泰州亿拓户外用品有限公司", "user"),
    ]
    for username, password, nickname, enterprise, role in users:
        conn.execute(
            """
            INSERT OR IGNORE INTO app_user (username, password, nickname, enterprise, role, tenant_id, job_title)
            VALUES (?, ?, ?, ?, ?, 1, ?)
            """,
            (username, password, nickname, enterprise, role, nickname),
        )
    conn.commit()
