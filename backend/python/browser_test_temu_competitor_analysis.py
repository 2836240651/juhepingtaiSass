from __future__ import annotations

import os
from pathlib import Path
import requests
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


BASE_URL = os.environ.get("CROSSHUB_TEST_BASE_URL", "http://localhost:5173").rstrip("/")
ACCOUNT = os.environ.get("CROSSHUB_TEST_ACCOUNT", "HangZhouYiTuo")
# 注意：此仓库的测试/演示账号密码在当前环境里通常使用同值；如你真实密码不同，请覆盖环境变量。
PASSWORD = os.environ.get("CROSSHUB_TEST_PASSWORD", "HangZhouYiTuo")
SCREENSHOT = Path(os.environ.get("CROSSHUB_TEST_SCREENSHOT", "browser_test_temu_competitor_analysis.png"))


def backend_login_token() -> tuple[str, int]:
    base = BASE_URL
    res = requests.post(
        f"{base}/api/auth/login",
        json={"account": ACCOUNT, "password": PASSWORD, "portal_role": "boss"},
        timeout=20,
    )
    res.raise_for_status()
    payload = res.json()
    data = payload.get("data") or {}
    token = data.get("token")
    tenant_id = int(data.get("tenant_id") or 0)
    if not token:
        raise RuntimeError(f"登录未返回 token: {payload}")
    return token, tenant_id


def login_if_on_login_page(page) -> None:
    # 支持 label / placeholder 两类输入框
    has_login_btn = page.get_by_role("button", name="进入企业管理员").count() > 0
    if not has_login_btn:
        return
    account_input = page.get_by_label("账号")
    if account_input.count() == 0:
        account_input = page.get_by_placeholder("请输入账号")
    password_input = page.get_by_label("密码")
    if password_input.count() == 0:
        password_input = page.locator("input[type='password']")
    if account_input.count() > 0 and password_input.count() > 0:
        account_input.first.fill(ACCOUNT)
        password_input.first.fill(PASSWORD)
        page.get_by_role("button", name="进入企业管理员").click()
        page.wait_for_timeout(1500)


def click_competitor_tab(page) -> None:
    # 优先精确中文名称，再退化为正则包含“竞店”
    for locator in (
        page.get_by_role("tab", name="竞店分析"),
        page.get_by_role("tab", name="竞店"),
        page.get_by_role("tab", name="Temu竞品"),
        page.get_by_role("tab").filter(has_text="竞店"),
    ):
        if locator.count() > 0:
            locator.first.click()
            return

    # 打印可见 tab 文案，便于定位编码/文案变化问题
    tab_texts = page.get_by_role("tab").all_text_contents()
    # 兜底：尝试左侧菜单项/链接
    for locator in (
        page.get_by_role("menuitem").filter(has_text="竞店"),
        page.get_by_role("link").filter(has_text="竞店"),
        page.locator(".el-menu-item").filter(has_text="竞店"),
    ):
        if locator.count() > 0:
            locator.first.click()
            page.wait_for_timeout(1000)
            return
    current_url = page.url
    title = page.title()
    raise RuntimeError(f"找不到竞店分析入口，url={current_url}, title={title}, tabs={tab_texts}")


def click_run_analysis(page) -> None:
    for locator in (
        page.get_by_role("button", name="执行今日爬取分析"),
        page.get_by_role("button", name="今日爬取分析"),
        page.get_by_role("button").filter(has_text="爬取分析"),
    ):
        if locator.count() > 0:
            locator.first.click()
            return
    btn_texts = page.get_by_role("button").all_text_contents()
    raise RuntimeError(f"找不到执行按钮，可见 buttons={btn_texts}")


def print_safe(label: str, value) -> None:
    text = f"{label}{value!r}"
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("gbk", errors="replace").decode("gbk", errors="replace"))


def run_once() -> None:
    token, tenant_id = backend_login_token()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # 优先走后端真实会话，避免 UI 登录文案变化导致脚本失效
        page.goto(BASE_URL, wait_until="domcontentloaded")
        page.evaluate(
            """([token, tenantId]) => {
              localStorage.setItem('accessToken', token);
              localStorage.setItem('backend_linked', '1');
              if (tenantId) localStorage.setItem('backend_tenant_id', String(tenantId));
              localStorage.setItem('crosshub_logged_in', '1');
              localStorage.setItem('crosshub_role', 'boss');
            }""",
            [token, tenant_id],
        )

        # 直接进 Temu 运营页；若未登录，路由会跳登录页
        page.goto(f"{BASE_URL}/boss/temu", wait_until="domcontentloaded")
        login_if_on_login_page(page)

        # 等路由稳定
        page.wait_for_timeout(1500)

        # 切到“竞店分析”页签
        click_competitor_tab(page)
        page.wait_for_timeout(800)

        # 点“执行今日爬取分析”
        click_run_analysis(page)

        # 竞店分析的失败/成功都会在这里体现：通常是 warning 的 el-alert
        # 我们重点抓取“未抓到竞店商品”这个失败码对应的标题
        try:
            page.get_by_text("未抓到竞店商品", exact=False).first.wait_for(timeout=90_000)
            # 尽量抓 alert 文案
            alert_titles = page.locator(".el-alert__title").all_text_contents()
            alert_texts = page.locator(".el-alert__description").all_text_contents()
            print("UI_RESULT=ALERT")
            print_safe("alert_titles=", alert_titles[:3])
            print_safe("alert_texts=", alert_texts[:3])
        except PlaywrightTimeoutError:
            # 没看到失败提示，抓 summary-row 看看数字是否更新
            summary_row_text = page.locator(".summary-row").inner_text(timeout=5000)
            print("UI_RESULT=NO_ALERT")
            print_safe("summary_row_text=", summary_row_text)

        page.screenshot(path=str(SCREENSHOT), full_page=True)
        print(f"SCREENSHOT={SCREENSHOT.resolve()}")

        # 给你留几秒观察
        page.wait_for_timeout(5000)
        context.close()
        browser.close()


if __name__ == "__main__":
    run_once()

