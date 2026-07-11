"""CrossHub Agent：轮询 Java 任务并在本机执行紫鸟 WebDriver 操作。"""
from __future__ import annotations

import os
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env", override=False)

JAVA_API_URL = os.getenv("JAVA_API_URL", "http://localhost:18080").rstrip("/")
AGENT_TOKEN = os.getenv("AGENT_TOKEN", "").strip()
POLL_INTERVAL_SECONDS = int(os.getenv("AGENT_POLL_INTERVAL_SECONDS", "10"))
HEARTBEAT_INTERVAL_SECONDS = int(os.getenv("AGENT_HEARTBEAT_INTERVAL_SECONDS", "30"))
AGENT_HEALTH_PORT = int(os.getenv("AGENT_HEALTH_PORT", "18765"))
ZINIAO_SOCKET_PORT = int(os.getenv("ZINIAO_SOCKET_PORT", "16851"))
