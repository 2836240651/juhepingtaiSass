# 前后端 API 联调 — PRD 实施包

> 实施前必读：`01-未联调清单.md`  
> 验收用例：`04-测试用例.md`  
> 交叉：`docs/permissions/03-PRD实施包.md`（shop scope）、`docs/temu-crawl/03-PRD实施包.md`（爬取）

---

## 里程碑总览

| 阶段 | 范围 | 交付 | 状态 |
|------|------|------|------|
| **M0** | 契约与门禁 | snake_case、去掉静默 Demo 回退、总览按绑定计店 | 部分已做，需回归 |
| **M1** | Temu ID 统一 | 绑定账号 ↔ `shop_id` 映射；运营/总览/Temu 模块一致 | 待实施 |
| **M2** | 出库单闭环 | 平台推仓进 Java；去掉 orders 列表 local 合并 | 待实施 |
| **M3** | 任务与反馈 | `assigned_task` + `ops_feedback` API | 待实施 |
| **M4** | 非 Temu 运营 | 分平台 API 或明确「仅 Demo」开关 | 待规划 |

## 实施阶段（P0～P4）

| 阶段 | 对应 | 工期 | 目标 | 关键交付 |
|------|------|------|------|----------|
| **P0** | M0 | 1 天 | 已存在 Java API 100% 可走通；后端模式零 Demo 泄漏 | 契约表、门禁、`operationsOverview` |
| **P1** | M1 | 2–3 天 | Temu 绑定后运营总览/模块有数据或明确空态 | DB 映射 + `DataScopeService` |
| **P2** | M2 | 2–3 天 | 平台推仓出库单落库 | `WarehouseOrder` 扩展 + 前端 `platformShipRequests` |
| **P3** | M3 | 3–5 天 | 任务分配、反馈走后端 | 新表 + Controller |
| **P4** | M4 | 按平台 | AE/Amazon/国内等 | 各平台子 PRD |

**原则**：

1. `VITE_USE_TEMU_BACKEND=false` 时保持现有 Demo 行为不变。  
2. 后端模式失败 **throw**，禁止静默 `catch { fallback local }`。  
3. 新 API 请求体默认 snake_case（Record）；与现有 warehouse order Map 风格并存时须在契约中注明。

---

## P0：契约与门禁（不新增 Java）

### 功能需求

| ID | 需求 |
|----|------|
| FR-P0-01 | 账户绑定 bind/list/delete 在后端模式仅调 Java |
| FR-P0-02 | 员工/仓库站点/仓库人员 CRUD 在后端模式仅调 Java |
| FR-P0-03 | Record DTO 请求字段使用 snake_case（见清单第三节） |
| FR-P0-04 | 运营总览「绑定店铺」以 `platform_accounts` 计数，不依赖 Demo 商品 |
| FR-P0-05 | 后端模式不调用 `ensure*DemoData` / `ensureDemoStores` |
| FR-P0-06 | `loadOperationsOverview` 中 Temu 产品优先 `/api/temu/operational`（有绑定时） |

### 前端改动范围（实施时）

| 文件 | 改动要点 |
|------|----------|
| `src/api/backendSession.js` | `hasBackendSession(auth)` 单点判断 |
| `src/api/platformAccountsApi.js` | `toBindPayload` snake_case |
| `src/api/warehouseStaff.js` | `warehouse_ids` |
| `src/api/warehouseSites.js` | `sort_order`；去掉 fetch fallback |
| `src/api/employees.js` | 去掉 fetch fallback |
| `src/api/platformAccounts.js` | Demo 种子加 `!hasBackendSession` 门禁 |
| `src/api/operationsOverview.js` | Temu 后端 operational + `bound=stores.length` |
| `src/utils/platformMetrics.js` | 平台卡片以 `stores.length` 为准 |
| `src/main.js` | 已有 `isTemuBackendEnabled()` 门禁 Demo seed |

### 验收标准

- Boss 绑定 1 家 Temu → 运营总览「绑定店铺」= 1。  
- 故意发 camelCase `storeName` → 400「店铺名称不能为空」。  
- 断 Java 后绑定/员工列表 → 页面报错，不出现 Demo 王一鸣等数据。

---

## P1：Temu 店铺 ID 统一（M1）

### 功能需求

| ID | 需求 |
|----|------|
| FR-P1-01 | 账户绑定 Temu 时，可关联或自动解析 `temu_shop.shop_id` |
| FR-P1-02 | `user_shop_scope.shop_id` 与运营 API 使用同一主键 |
| FR-P1-03 | `/api/temu/shops` 返回项含 `platform_account_id`（可选） |
| FR-P1-04 | 运营总览 Temu 问题与绑定店铺可对应到同一负责人 |
| FR-P1-05 | 无爬虫数据时展示「已绑定，待同步」非「未绑定」 |

### 数据模型建议

```sql
-- 方案 A：platform_account 增加外部 ID
ALTER TABLE platform_account ADD COLUMN external_shop_id TEXT;
CREATE INDEX idx_pa_external_shop ON platform_account(tenant_id, platform, external_shop_id);

-- 方案 B：独立映射表
CREATE TABLE platform_shop_link (
  id TEXT PRIMARY KEY,
  tenant_id INTEGER NOT NULL,
  platform_account_id TEXT NOT NULL,
  external_shop_id TEXT NOT NULL,
  UNIQUE(tenant_id, platform_account_id),
  UNIQUE(tenant_id, platform, external_shop_id)
);
```

### API 变更建议

| 方法 | 路径 | 说明 |
|------|------|------|
| PUT | `/api/platform-accounts/bind` | 响应增加 `external_shop_id`；绑定时可选填 |
| GET | `/api/temu/shops` | 每项增加 `platform_account_id`、`account` 匹配提示 |
| GET | `/api/platform-accounts` | 每项增加 `external_shop_id` |

### 前端改动范围（实施时）

| 文件 | 改动要点 |
|------|----------|
| `BindStoreDialog.vue` | 可选「Temu Shop ID」或绑后自动匹配 |
| `temuApi.js` | `fetchTemuStores` 与绑定店铺 merge |
| `operationsOverview.js` | 用 `external_shop_id` 过滤 operational |
| `scope.js` | 员工 scope 统一 ID 域 |

---

## P2：平台推仓（M2）

### 功能需求

| ID | 需求 |
|----|------|
| FR-P2-01 | 各平台「推仓库发货」创建的后端出库单写入 `warehouse_order` |
| FR-P2-02 | 出库单记录 `source_platform`、`source_store_name`、`source_order_ref` |
| FR-P2-03 | `fetchWarehouseOrders` 后端模式不再 merge localStorage |
| FR-P2-04 | 平台运营页可读出库反馈状态（审批/发货） |

### API 建议

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/warehouse/orders/from-platform` | 由平台订单一键生成出库单 |
| GET | `/api/warehouse/orders` | 已有；增加 `fromPlatformOrder` 字段 |

### 前端改动范围

| 文件 | 改动要点 |
|------|----------|
| `platformShipRequests.js` | 调 Java 替代 `platformShipRequestsLocal` |
| `warehouseOrders.js` | 删除 local 合并逻辑 |
| `platformOrderWarehouseSync.js` | 退役或仅 Demo |

---

## P3：任务与反馈（M3）

### 功能需求

| ID | 需求 |
|----|------|
| FR-P3-01 | Boss 分配任务持久化到 DB，员工/仓库可见自己的任务 |
| FR-P3-02 | 任务反馈写入 DB，Boss 任务详情与运营总览日报可读 |
| FR-P3-03 | 取消/完成/逾期状态机与现有 `assignedTasksLocal` 语义一致 |
| FR-P3-04 | 与 `employeeTasks.js` 运营问题生成任务可并存或逐步迁移 |

### API 草案

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/tasks` | 列表（Boss 全量；员工/仓库 scoped） |
| GET | `/api/tasks/{id}` | 详情含 feedbacks |
| POST | `/api/tasks` | Boss 分配 |
| PATCH | `/api/tasks/{id}` | 更新状态/内容 |
| DELETE | `/api/tasks/{id}` | Boss 删除 |
| POST | `/api/tasks/{id}/feedbacks` | 提交反馈 |
| GET | `/api/ops-feedback/today` | 运营总览日报用 |

### 表结构草案

- `assigned_task`：id, tenant_id, title, assignee_id, assignee_type, platform, store_id, status, due_at, payload_json, …  
- `ops_feedback`：id, task_id, tenant_id, author_id, outcome, content, created_at, …

### 前端改动范围

| 文件 | 改动要点 |
|------|----------|
| `assignedTasks.js` | `hasBackendSession` 分支调 API |
| `opsFeedback.js` | 同上 |
| `employeeTasks.js` | 后端模式跳过 `OPERATION_TASKS` 硬编码（已部分做） |

---

## P4：非 Temu 平台运营（M4，可选）

**策略二选一**：

1. **继续 Demo**：后端模式下各平台运营页显示「该平台运营数据接口开发中」，仅展示绑定店铺列表。  
2. **分平台 Java API**：每平台 `orders` / `issues` 表 + 爬虫或导入；工作量大，按业务优先级排期。

| 平台 | 前端入口 | 建议 |
|------|----------|------|
| AliExpress | `aliexpress.js` | P4-AE |
| Walmart | `walmart.js` | P4-WM |
| Amazon | `amazon.js` | P4-AMZ |
| 国内三平台 | `domesticPlatforms.js` | P4-DOM |
| 1688 | `alibaba1688.js` | P4-1688 |
| 独立站 | `dtc.js` | P4-DTC |
| Temu 竞品 | `temuCompetitors.js` | P4-TEMU-COMP |

---

## 双模式行为矩阵（验收依据）

| 能力 | Backend | Demo (`VITE_USE_TEMU_BACKEND=false`) |
|------|---------|----------------------------------------|
| 登录 | Java | localStorage |
| 账户绑定 | Java DB | localStorage + Demo 店 |
| 运营总览店铺数 | 绑定表 | Demo 种子 + 绑定 |
| Temu 商品数据 | `/api/temu/operational` | `TEMU_PRODUCTS_RAW` |
| 任务分配 | P3 后 Java | localStorage |
| 出库单 | Java（P2 后含推仓） | localStorage |

---

## 实施顺序（推荐）

```
P0 契约回归（1d）
  → P1 Temu ID（2–3d）
  → P2 推仓（2–3d）
  → P3 任务反馈（3–5d）
  → P4 按平台排期
```

每阶段合并前执行 `04-测试用例.md` 对应章节，并与 `permissions/04` 做 Temu scope 交叉回归。
