"""爬虫运行配置（可通过环境变量或 .env 覆盖）"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

PROFILE_DIR = Path(os.getenv("TEMU_PROFILE_DIR", str(ROOT / ".temu-browser-profile")))
TEMU_SELLER_HOME = os.getenv("TEMU_SELLER_HOME", "https://agentseller.temu.com/")
TEMU_SALES_API = os.getenv(
    "TEMU_SALES_API",
    "https://agentseller.temu.com/mms/venom/api/supplier/sales/management/listOverall",
)
TEMU_USER_INFO_API = os.getenv(
    "TEMU_USER_INFO_API",
    "https://agentseller.temu.com/api/seller/auth/userInfo",
)
MALL_STORAGE_KEY = os.getenv("TEMU_MALL_STORAGE_KEY", "agentseller-mall-info-id")

# 默认有头 + 本机 Chrome，降低 Temu 风控识别概率
HEADLESS = os.getenv("TEMU_HEADLESS", "0").strip().lower() in ("1", "true", "yes")
BROWSER_CHANNEL = os.getenv("TEMU_BROWSER_CHANNEL", "chrome").strip() or None

MIN_ACTION_DELAY_MS = int(os.getenv("TEMU_MIN_DELAY_MS", "800"))
MAX_ACTION_DELAY_MS = int(os.getenv("TEMU_MAX_DELAY_MS", "2200"))

STATUS_TO_CODE = {10: "100", 11: "200", 12: "300", 13: "400"}
