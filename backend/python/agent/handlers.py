"""Agent 任务处理器。"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from typing import Any

from agent.java_client import AgentApiClient
from app.amazon.report_crawler import AmazonLoginRequiredError, crawl_amazon
from app.ziniao.client import ZiniaoClient, ZiniaoConfig

CRAWL_TIMEOUT_SECONDS = 900
CRAWL_TIMEOUT_MINUTES = CRAWL_TIMEOUT_SECONDS // 60


def handle_ziniao_discover(client: AgentApiClient, task: dict[str, Any]) -> None:
    task_id = str(task.get("task_id") or task.get("id") or "")
    if not task_id:
        return

    ziniao = ZiniaoClient(ZiniaoConfig.from_env())
    try:
        ziniao.ensure_webdriver_client(wait_seconds=20)
        stores = ziniao.get_browser_list()
        client.complete_task(task_id, status="success", result={"stores": stores})
    except Exception as exc:
        client.complete_task(
            task_id,
            status="failed",
            error_code="ZINIAO_DISCOVER_FAILED",
            error_message=str(exc),
        )


def handle_amazon_sync(client: AgentApiClient, task: dict[str, Any]) -> None:
    task_id = str(task.get("task_id") or task.get("id") or "")
    if not task_id:
        return

    payload = task.get("payload") or {}
    scope = str(payload.get("scope") or "account_health")
    browser_id = str(payload.get("browser_id") or "")
    browser_oauth = str(payload.get("browser_oauth") or "")
    store_name = str(payload.get("store_name") or "")

    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                crawl_amazon,
                scope=scope,
                browser_id=browser_id,
                browser_oauth=browser_oauth,
                store_name=store_name,
            )
            result = future.result(timeout=CRAWL_TIMEOUT_SECONDS)
        client.complete_task_with_retry(task_id, status="success", result=result)
    except FutureTimeoutError:
        client.complete_task_with_retry(
            task_id,
            status="failed",
            error_code="AMAZON_SYNC_TIMEOUT",
            error_message=f"Amazon 爬取超时（超过 {CRAWL_TIMEOUT_MINUTES} 分钟），请稍后重试",
        )
    except AmazonLoginRequiredError as exc:
        client.complete_task_with_retry(
            task_id,
            status="failed",
            error_code="AMAZON_LOGIN_REQUIRED",
            error_message=str(exc),
        )
    except Exception as exc:
        message = str(exc)
        error_code = "AMAZON_SYNC_FAILED"
        if "未登录" in message or "login" in message.lower() or "sign in" in message.lower():
            error_code = "AMAZON_LOGIN_REQUIRED"
        client.complete_task_with_retry(
            task_id,
            status="failed",
            error_code=error_code,
            error_message=message,
        )


def dispatch_task(client: AgentApiClient, task: dict[str, Any]) -> None:
    task_type = str(task.get("task_type") or "")
    if task_type in {"ziniao_discover", "amazon_ziniao_discover"}:
        handle_ziniao_discover(client, task)
        return
    if task_type == "amazon_sync":
        handle_amazon_sync(client, task)
        return
    task_id = str(task.get("task_id") or "")
    if task_id:
        client.complete_task(
            task_id,
            status="failed",
            error_code="UNSUPPORTED_TASK",
            error_message=f"未支持的任务类型: {task_type}",
        )
