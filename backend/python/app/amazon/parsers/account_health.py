"""解析 Amazon Seller Central 页面指标（首页 + Account Health）。"""
from __future__ import annotations

import re
from typing import Any


METRIC_PATTERNS: list[tuple[str, str, re.Pattern[str]]] = [
    ("order_defect_rate", "订单缺陷率 ODR", re.compile(r"(?:order defect rate|订单缺陷率)[^\d%]*([\d.]+%)", re.I)),
    ("late_shipment_rate", "迟发率", re.compile(r"(?:late shipment rate|迟发率|延迟发货率)[^\d%]*([\d.]+%)", re.I)),
    ("pre_fulfillment_cancel_rate", "预配送取消率", re.compile(r"(?:pre-fulfillment cancel|取消率|预配送取消率)[^\d%]*([\d.]+%)", re.I)),
    ("valid_tracking_rate", "有效追踪率", re.compile(r"(?:valid tracking rate|有效追踪率)[^\d%]*([\d.]+%)", re.I)),
    ("on_time_delivery_rate", "准时送达率", re.compile(r"(?:on-time delivery rate|准时送达率)[^\d%]*([\d.]+%)", re.I)),
    ("invoice_defect_rate", "发票缺陷率", re.compile(r"(?:invoice defect rate|发票缺陷率)[^\d%]*([\d.]+%)", re.I)),
]

THRESHOLD_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("order_defect_rate", re.compile(r"order defect rate.*?target[^\d%]*(<[\d.]+%)", re.I | re.S)),
    ("late_shipment_rate", re.compile(r"late shipment rate.*?target[^\d%]*(<[\d.]+%)", re.I | re.S)),
    ("pre_fulfillment_cancel_rate", re.compile(r"pre-fulfillment cancel.*?target[^\d%]*(<[\d.]+%)", re.I | re.S)),
    ("valid_tracking_rate", re.compile(r"valid tracking rate.*?target[^\d%]*(>[\d.]+%)", re.I | re.S)),
    ("on_time_delivery_rate", re.compile(r"on-time delivery rate.*?target[^\d%]*(>[\d.]+%)", re.I | re.S)),
]

HOME_METRIC_RULES: list[tuple[str, str, re.Pattern[str], str]] = [
    (
        "account_health_status",
        "账户状况",
        re.compile(r"账户状况为\s*([^\n，,。.]+)"),
        "status",
    ),
]

SNAPSHOT_METRIC_RULES: list[tuple[str, str, re.Pattern[str], str]] = [
    (
        "sales_today",
        "今日销售额",
        re.compile(r"(?:销售额|Sales)[\s\S]{0,80}?US\$?\s*([\d,]+\.?\d*)", re.I),
        "money",
    ),
    (
        "open_orders",
        "未解决订单",
        re.compile(r"未解决的订单[\s\S]{0,80}?(\d+)"),
        "count",
    ),
    (
        "buyer_messages",
        "买家消息",
        re.compile(r"买家消息[\s\S]{0,40}?(\d+)"),
        "count",
    ),
    (
        "buy_box_percentage",
        "推荐报价百分比",
        re.compile(r"推荐报价百分比[\s\S]{0,40}?(\d+)%"),
        "percent",
    ),
    (
        "seller_feedback",
        "卖家反馈",
        re.compile(r"卖家反馈[\s\S]{0,40}?([\d.]+)"),
        "rating",
    ),
    (
        "payment_balance",
        "账户余额",
        re.compile(r"付款[\s\S]{0,80}?US\$?\s*([\d,]+\.?\d*)", re.I),
        "money",
    ),
    (
        "ipi_score",
        "库存绩效指标 IPI",
        re.compile(r"库存绩效指标[\s\S]{0,40}?(\d+)"),
        "count",
    ),
    (
        "ad_spend_today",
        "今日广告花费",
        re.compile(r"(?:广告(?:销售额|费用|花费|支出)|Ad spend|Spend)[\s\S]{0,80}?US\$?\s*([\d,]+\.?\d*)", re.I),
        "money",
    ),
]

HEALTH_STATUS_MAP = {
    "健康": "normal",
    "healthy": "normal",
    "良好": "normal",
    "good": "normal",
    "警告": "warning",
    "warning": "warning",
    "预警": "warning",
    "存在风险": "critical",
    "at risk": "critical",
    "critical": "critical",
    "不健康": "critical",
    "unhealthy": "critical",
}


def _status_for(metric_key: str, value_text: str) -> str:
    if metric_key == "account_health_status":
        lowered = (value_text or "").strip().lower()
        for token, status in HEALTH_STATUS_MAP.items():
            if token.lower() in lowered:
                return status
        return "normal"

    match = re.search(r"([\d.]+)", value_text or "")
    if not match:
        return "normal"
    value = float(match.group(1))
    if metric_key == "order_defect_rate":
        if value >= 1.0:
            return "critical"
        if value >= 0.8:
            return "warning"
        return "normal"
    if metric_key == "late_shipment_rate":
        if value >= 4.0:
            return "critical"
        if value >= 3.5:
            return "warning"
        return "normal"
    if metric_key == "pre_fulfillment_cancel_rate":
        if value >= 2.5:
            return "critical"
        if value >= 2.0:
            return "warning"
        return "normal"
    if metric_key in {"valid_tracking_rate", "on_time_delivery_rate"}:
        if value < 90:
            return "critical"
        if value < 95:
            return "warning"
        return "normal"
    if metric_key == "buy_box_percentage":
        if value < 90:
            return "warning"
        return "normal"
    if metric_key == "buyer_messages":
        if value > 0:
            return "warning"
        return "normal"
    if metric_key == "open_orders":
        if value >= 200:
            return "warning"
        return "normal"
    if metric_key == "ipi_score":
        if value < 400:
            return "critical"
        if value < 500:
            return "warning"
        return "normal"
    return "normal"


def _format_value(value_type: str, raw: str) -> str:
    text = (raw or "").strip()
    if value_type == "percent":
        return f"{text}%"
    if value_type == "money":
        match = re.search(r"([\d,]+\.?\d*)", text)
        if match:
            amount = float(match.group(1).replace(",", ""))
            return f"US${amount:,.2f}"
        return f"US${text}" if not text.startswith("US$") else text
    if value_type == "rating":
        return f"{text} 星"
    if value_type == "status":
        return text
    return text


def _append_metric(
    metrics: list[dict[str, Any]],
    seen: set[str],
    *,
    metric_key: str,
    label: str,
    value_text: str,
    threshold: str = "",
    note: str = "",
) -> None:
    if not value_text or metric_key in seen:
        return
    metrics.append(
        {
            "metric_key": metric_key,
            "metric_label": label,
            "value_text": value_text,
            "threshold_text": threshold,
            "status": _status_for(metric_key, value_text),
            "trend": "stable",
            "note_text": note,
        }
    )
    seen.add(metric_key)


def _extract_global_snapshot_block(text: str) -> str:
    body = text or ""
    match = re.search(
        r"全局快照\s*(.*?)(?=商品绩效|建议|卖家新闻|卖家体验|隐藏式|$)",
        body,
        re.S,
    )
    if match:
        return match.group(1)
    match = re.search(
        r"Global snapshot\s*(.*?)(?=Product performance|Recommendations|Seller news|$)",
        body,
        re.S | re.I,
    )
    return match.group(1) if match else ""


def parse_seller_home_text(text: str) -> list[dict[str, Any]]:
    body = text or ""
    snapshot = _extract_global_snapshot_block(body)
    metrics: list[dict[str, Any]] = []
    seen: set[str] = set()

    for metric_key, label, pattern, value_type in HOME_METRIC_RULES:
        match = pattern.search(body)
        if not match:
            continue
        value_text = _format_value(value_type, match.group(1))
        _append_metric(metrics, seen, metric_key=metric_key, label=label, value_text=value_text)

    if snapshot:
        for metric_key, label, pattern, value_type in SNAPSHOT_METRIC_RULES:
            match = pattern.search(snapshot)
            if not match:
                continue
            value_text = _format_value(value_type, match.group(1))
            _append_metric(metrics, seen, metric_key=metric_key, label=label, value_text=value_text)

    return metrics


def parse_account_health_text(text: str) -> list[dict[str, Any]]:
    body = text or ""
    metrics: list[dict[str, Any]] = []
    seen: set[str] = set()

    for metric_key, label, pattern in METRIC_PATTERNS:
        match = pattern.search(body)
        if not match:
            continue
        value_text = match.group(1).strip()
        threshold = ""
        for key, threshold_pattern in THRESHOLD_PATTERNS:
            if key != metric_key:
                continue
            threshold_match = threshold_pattern.search(body)
            if threshold_match:
                threshold = threshold_match.group(1).strip()
                break
        _append_metric(
            metrics,
            seen,
            metric_key=metric_key,
            label=label,
            value_text=value_text,
            threshold=threshold,
        )

    return metrics


def parse_seller_central_text(text: str) -> list[dict[str, Any]]:
    """合并首页快照 + Account Health 详情页指标。"""
    metrics: list[dict[str, Any]] = []
    seen: set[str] = set()

    for item in parse_seller_home_text(text):
        key = item["metric_key"]
        if key not in seen:
            metrics.append(item)
            seen.add(key)

    for item in parse_account_health_text(text):
        key = item["metric_key"]
        if key not in seen:
            metrics.append(item)
            seen.add(key)

    if metrics:
        return metrics

    # 兜底：页面含卖家后台特征时，至少返回账户状况占位
    body = text or ""
    if "seller central" in body.lower() or "卖家平台" in body or "全局快照" in body:
        health_match = re.search(r"账户状况为\s*([^\n，,。.]+)", body)
        if health_match:
            value = health_match.group(1).strip()
            return [
                {
                    "metric_key": "account_health_status",
                    "metric_label": "账户状况",
                    "value_text": value,
                    "threshold_text": "",
                    "status": _status_for("account_health_status", value),
                    "trend": "stable",
                    "note_text": "来自卖家平台首页",
                }
            ]

    fallback_values = re.findall(r"([\d.]+%)", body)
    if fallback_values:
        return [
            {
                "metric_key": "account_health_snapshot",
                "metric_label": "账户状况快照",
                "value_text": fallback_values[0],
                "threshold_text": "",
                "status": "normal",
                "trend": "stable",
                "note_text": "未能完整解析指标，已保存页面快照值",
            }
        ]
    return []
