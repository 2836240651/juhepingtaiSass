"""Parser regression checks for Amazon daily sync."""
from __future__ import annotations

from pathlib import Path

from app.amazon.parsers.account_health import parse_seller_home_text
from app.amazon.parsers.seller_pages import parse_reviews_from_text

ROOT = Path(__file__).resolve().parents[1]
HOME_SAMPLE = ROOT / "data" / "amazon-probe-home.txt"

FEEDBACK_SAMPLE = """
反馈管理器
最新反馈
日期	评级	订单编号	评论	操作
2026/07/07	5	113-7966774-9300250	good
2026/06/29	1	113-9587851-5301049	Ordered empty envelope
2026/06/25	5	112-2744115-9981016	Arrived fine
"""


def test_home_buyer_messages_from_snapshot() -> None:
    if not HOME_SAMPLE.exists():
        return
    text = HOME_SAMPLE.read_text(encoding="utf-8")
    metrics = {item["metric_key"]: item["value_text"] for item in parse_seller_home_text(text)}
    assert metrics.get("buyer_messages") == "0", metrics.get("buyer_messages")
    assert metrics.get("open_orders") == "237", metrics.get("open_orders")


def test_reviews_parser_finds_one_star() -> None:
    rows = parse_reviews_from_text(FEEDBACK_SAMPLE)
    assert len(rows) == 1
    assert rows[0]["order_no"] == "113-9587851-5301049"
    assert rows[0]["rating"] == 1


if __name__ == "__main__":
    test_home_buyer_messages_from_snapshot()
    test_reviews_parser_finds_one_star()
    print("ok")
