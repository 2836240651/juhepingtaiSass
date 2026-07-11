# Amazon × 紫鸟 — PRD 实施包（开发清单）

> 实施前必读：[02-技术设计.md](./02-技术设计.md)、[01-需求与范围.md](./01-需求与范围.md)  
> 验收用例：[04-测试用例清单.md](./04-测试用例清单.md)  
> 回归：[05-回归基准.md](./05-回归基准.md)

## 里程碑总览

| 阶段 | 范围 | 工期估 | 状态 |
|------|------|--------|------|
| **AMZ-P0** | Agent + 紫鸟绑定 + 门禁 | 3～5 天 | 待实施 |
| **AMZ-P1** | Account Health 同步 + daily API | 5～7 天 | 待实施 |
| **AMZ-P2** | Boss insights + 运营总览 | 4～5 天 | 待实施 |
| **AMZ-P3** | 写操作 + 报表扩展 | 5～7 天 | 规划 |
| **AMZ-P4** | SP-API OAuth（可选并行） | 10～15 天 | 规划 |

---

## AMZ-P0：绑定与 Agent（开发清单）

### 后端 Java

| # | 任务 | 文件/位置 | 完成 |
|---|------|-----------|------|
| J-01 | DB 迁移：`integration_agent`、`platform_account` 扩展字段 | `config/migration/V*Amazon*.java` | ☐ |
| J-02 | `AgentController` register / heartbeat / tasks / complete | `controller/AgentController.java` | ☐ |
| J-03 | `AmazonZiniaoController` discover / candidates / bind | `controller/AmazonZiniaoController.java` | ☐ |
| J-04 | `AgentService` token 签发与校验 | `service/impl/AgentServiceImpl.java` | ☐ |
| J-05 | `PlatformAccountService` 写入 `external_shop_id` | 扩展 bind DTO | ☐ |
| J-06 | Security：Agent 路由 `X-Agent-Token` 过滤器 | `security/` | ☐ |

### Python Agent

| # | 任务 | 文件/位置 | 完成 |
|---|------|-----------|------|
| P-01 | `agent/main.py` 心跳 + 轮询循环 | `backend/python/agent/` | ☐ |
| P-02 | discover 任务：调 `ZiniaoClient.get_browser_list()` | `agent/handlers/discover.py` | ☐ |
| P-03 | `scripts/run_agent.py` 启动入口 | `backend/python/scripts/` | ☐ |
| P-04 | `ensure_webdriver_client` 普通模式检测（已有） | `app/ziniao/client.py` | ☑ |

### 前端 Vue

| # | 任务 | 文件/位置 | 完成 |
|---|------|-----------|------|
| F-01 | Vite 代理 `/api/amazon`、`/api/agent` | `vite.config.js` | ☐ |
| F-02 | `AccountBindingView`：「从紫鸟导入」对话框 | `views/boss/AccountBindingView.vue` | ☐ |
| F-03 | 绑定请求带 `external_shop_id`、`integration_mode` | `platformAccountsApi.js` | ☐ |
| F-04 | Agent 节点管理页（简易：名称 + 在线状态） | `views/boss/` 或设置子页 | ☐ |
| F-05 | Amazon 页：Agent 离线时展示操作指引 | `AmazonModuleView.vue` | ☐ |

### 运维 / 文档

| # | 任务 | 完成 |
|---|------|------|
| O-01 | `scripts/start-ziniao-webdriver.ps1` 一键启动紫鸟 WebDriver | ☐ |
| O-02 | `AGENTS.md` 补充 Agent + 紫鸟启动说明 | ☐ |

### P0 验收标准

- [ ] Boss 注册 Agent → 心跳 `ziniao_online=1`（WebDriver 运行时）
- [ ] discover 返回含 `YOTO美国账号` / `browserId=16505337258263`
- [ ] 绑定后 `platform_accounts` 行含 `external_shop_id`
- [ ] 后端模式 Amazon 页显示「待同步」非 Demo 刘洋种子数据

---

## AMZ-P1：日报 MVP（开发清单）

### 后端 Java

| # | 任务 | 完成 |
|---|------|------|
| J-10 | 迁移 `amazon_sync_job`、`amazon_account_metric` | ☐ |
| J-11 | `AmazonSyncService` trigger / poll / complete | ☐ |
| J-12 | `AmazonController` POST sync、GET sync/{id}、GET daily | ☐ |
| J-13 | `AmazonOperationalService` 读 daily 聚合 | ☐ |
| J-14 | `AppErrorCode`：`AMAZON_AGENT_OFFLINE`、`AMAZON_ZINIAO_*` | ☐ |

### Python

| # | 任务 | 完成 |
|---|------|------|
| P-10 | `amazon/report_crawler.py` Account Health 页面导航 | ☐ |
| P-11 | `parsers/account_health.py` 输出 metric 列表 | ☐ |
| P-12 | sync 任务 handler：startBrowser → CDP → 解析 → POST complete | ☐ |
| P-13 | 失败截图存 `backend/data/amazon-captures/` | ☐ |

### 前端

| # | 任务 | 完成 |
|---|------|------|
| F-10 | 新建 `amazonApi.js`（sync 轮询、daily） | ☐ |
| F-11 | `amazon.js` 后端模式走 Api | ☐ |
| F-12 | `AmazonModuleView` 刷新按钮 → POST sync | ☐ |
| F-13 | `AmazonAccountHealthPanel` 展示 API 数据 | ☐ |
| F-14 | `platformOperationalMode.js` 条件纳入 amazon | ☐ |

### P1 验收标准

- [ ] 刷新后 `amazon_sync_job`：pending → running → success
- [ ] `GET /api/amazon/daily` 含 ≥1 条 `account_metrics`
- [ ] UI 账户状况 Tab 非 Demo `demo_amazon_1`
- [ ] Agent 离线时刷新返回明确错误，**无** Local 回退

---

## AMZ-P2：Boss + 运营总览（开发清单）

| # | 任务 | 完成 |
|---|------|------|
| J-20 | `amazon_product_snapshot`、`amazon_outbound_order` 表 | ☐ |
| J-21 | `GET /api/amazon/insights`、POST sync scope=insights | ☐ |
| P-20 | Business Report CSV 下载解析 | ☐ |
| F-20 | Boss Tab 产品/出库接 API | ☐ |
| F-21 | `operationsOverview.js` `buildAmazonSection` 接 daily | ☐ |
| F-22 | `platformMetrics.js` Amazon 待办计数来自 API | ☐ |

### P2 验收标准

- [ ] Boss 产品 TOP 来自同步数据或空态
- [ ] 运营总览 Amazon 卡片数字与 daily API 一致
- [ ] 员工 liuyang 仅见 Amazon scope 店铺

---

## AMZ-P3 / P4（ backlog ）

| # | 任务 | 优先级 |
|---|------|--------|
| B-01 | 买家消息 / Review / Case 爬取 + PATCH 回写 | P3 |
| B-02 | SP-API OAuth 在紫鸟窗口 + refresh_token 存储 | P4 |
| B-03 | 虎步 RPA API 对接标准财务报表 | 可选 |
| B-04 | 多 Agent 节点负载分配 | 可选 |

---

## API 契约摘要（P1）

### POST `/api/amazon/sync`

请求：

```json
{
  "platform_account_id": "uuid",
  "scope": "account_health"
}
```

响应 202：

```json
{
  "code": 0,
  "data": {
    "job_id": "uuid",
    "status": "pending"
  }
}
```

响应 409：同店同 scope 进行中。  
响应 503：`AMAZON_AGENT_OFFLINE`。

### GET `/api/amazon/sync/{jobId}`

```json
{
  "code": 0,
  "data": {
    "job_id": "uuid",
    "status": "success",
    "scope": "account_health",
    "result_summary": { "metrics_count": 12 }
  }
}
```

---

## 实施顺序建议

```
P0: J-01 → J-02/J-03 → P-01/P-02 → F-01/F-02 → 联调 discover+bind
P1: J-10/J-11 → P-10/P-12 → F-10/F-12 → 联调 sync+daily
P2: J-20 → P-20 → F-20/F-21 → 总览回归
```

**原则**（与 `docs/api-integration/03-PRD实施包.md` 一致）：

1. `VITE_USE_TEMU_BACKEND=false` 保持 Demo 不变  
2. 后端模式失败 **throw**，禁止静默 Local 回退  
3. 新 Record DTO 请求/响应 **snake_case**
