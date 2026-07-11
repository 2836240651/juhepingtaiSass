# Temu 平台 — 未实现功能清单

> 项目根目录：`SaaS-HZ_WEB_Demo`  
> 关联：`docs/temu-crawl/`、`03-PRD实施包.md` P1、`02-其余平台接口对齐清单.md`  
> 更新基准：2026-07-06

## 已实现基线（对照用）

| 能力 | Java / 前端 | 说明 |
|------|-------------|------|
| 账户绑定 | `platform-accounts` + `BindStoreDialog` Shop ID | `external_shop_id` 已入库 |
| 店铺列表 | `GET /api/temu/shops` + `fetchTemuStores` merge | 绑定店与爬虫 shop 合并 |
| 运营读数 | `GET /api/temu/operational` | 商品、亏损、滞销、备货预警、爆款 |
| 销售趋势 | `GET /api/temu/trend` | Boss 总览折线 |
| 一键爬取 | `POST/GET /api/temu/crawl` | 运营页「刷新数据」 |
| 运营总览 Temu 板块 | `operationsOverview` + 后端 operational | 绑定计数、亏损/备货问题项 |
| 价格亏损 / 滞销 | 前端 `PriceLossTable`、`SlowMovingPanel` | 数据来自 operational，算法前后端协作 |
| 备货建议量 | `RestockPlanner` 展示 | 建议量来自后端 `inventory_warnings` + 前端 `temuServerAlgo` |

以下均为 **后端模式** 下仍缺失或未做实的能力。

---

## 一、子模块未联调（仅 Local / Demo）

### 1. 竞店分析（Boss 专属 Tab）

| ID | 页面能力 | 当前实现 | 缺口 |
|----|----------|----------|------|
| TEMU-C01 | 竞争对手 CRUD | `temuCompetitorsLocal.js` | 无 `GET/POST/DELETE /api/temu/competitors` |
| TEMU-C02 | 每日爬取 / 分析 | `analyzeCompetitors` 生成 Demo 快照 | 无真实 Playwright 竞店爬虫 |
| TEMU-C03 | 快照历史 | `temuCompetitorSnapshotsLocal.js` | 无快照表与按日查询 API |
| TEMU-C04 | 监控报告 | `buildCompetitorMonitorReport` 本地计算 | 无 `GET /api/temu/competitors/{id}/reports` |
| TEMU-C05 | 后端模式门禁 | `CompetitorAnalysis` 有 `useBackendData` prop | **未传入**；后端登录仍走 Local |

**前端文件**：`temuCompetitors.js`、`CompetitorAnalysis.vue`、`utils/temuCompetitor.js`  
**建议 API 前缀**：`/api/temu/competitors`

---

### 2. 爆款通报

| ID | 页面能力 | 当前实现 | 缺口 |
|----|----------|----------|------|
| TEMU-H01 | 爆款识别列表 | 由 operational 商品计算 `isHot` | ✅ 读数已有 |
| TEMU-H02 | 一键全公司通报 | `appendHotBroadcast` → `localStorage` | 无通报持久化 API |
| TEMU-H03 | 通报历史 / 已读 | `crosshub_temu_hot_broadcasts` | 无多端同步、无员工已读回写 |
| TEMU-H04 | 初始种子 | `seedBroadcastsFromOverload` 写 localStorage | 后端模式不应依赖本地种子 |

**前端文件**：`HotProductBroadcast.vue`、`utils/temuHotBroadcast.js`  
**建议 API**：`GET/POST /api/temu/hot-broadcasts`，`POST .../{id}/read`

---

### 3. 备货跟进状态（运营总览 + 员工任务）

| ID | 页面能力 | 当前实现 | 缺口 |
|----|----------|----------|------|
| TEMU-R01 | SKU 备货状态（未备/备货中/已完成） | `temuRestockLocal.js` + 常量种子 | 无 Java 表与 API |
| TEMU-R02 | 运营总览「备货跟进」 | `getTemuRestockStatusMap()` **始终读 Local** | 后端模式仍混用 Demo 状态 |
| TEMU-R03 | 员工任务中心备货任务 | `employeeTasks.collectTemuTasks` 读总览 | 依赖 R01/R02 |
| TEMU-R04 | 页面内更新状态 | `updateTemuRestockStatus` **已实现但未挂 UI** | 无写接口、无操作入口 |
| TEMU-R05 | 备货参数配置 | `RESTOCK_CONFIG` 常量，卡片标「Demo」 | 无租户级配置 API |

**前端文件**：`temuRestockLocal.js`、`RestockPlanner.vue`、`constants/temuOps.js`  
**建议 API**：`GET/PUT /api/temu/restock-status`（按 `sku` + `shop_id`）

---

## 二、数据与算法未做实

| ID | 问题 | 现状 | 目标 |
|----|------|------|------|
| TEMU-D01 | **本地仓库存** | `mapReptileSaleToTemuProduct` 写死 `localStock: 0` | 对接仓库库存或 WMS；备货「本地缺 N」才有意义 |
| TEMU-D02 | **备货短fall 计算** | `restock.shortfall` 依赖 localStock | D01 完成后自动改善 |
| TEMU-D03 | **7 日销量序列** | 爬虫仅存 7 日总量，前端均分估算 | 爬虫落库每日销量或 API 返回真实序列 |
| TEMU-D04 | **滞销天数** | 无 Commander 明细时用 `join_site_time` 粗估 | 可选：后端返回 `days_without_sale` |
| TEMU-D05 | **历史报表日** | `operational?report_time=` 后端支持 | 前端无日期选择器，只能看最新一日 |
| TEMU-D06 | **platform_account ↔ shop** | 绑定时可填 Shop ID、可自动匹配 | `GET /shops` **未返回** `platform_account_id`（FR-P1-03） |

---

## 三、体验与空态

| ID | 需求 | 现状 |
|----|------|------|
| TEMU-U01 | 已绑定、无爬虫数据时展示「已绑定，待同步」（FR-P1-05） | ✅ `TemuModuleView` 空态提示 |
| TEMU-U02 | 绑定店与爬虫店未匹配时的引导 | ✅ 未填 Shop ID 警告条 |
| TEMU-U03 | 爬取依赖未登录 Temu 时的引导 | `formatCrawlError` 有文案，无运营页固定说明区 |
| TEMU-U04 | 员工仅分配「平台」未分配「店铺」时的 Temu 可见性 | 后端 `platforms含temu` 时可见全部爬虫店；与绑定店 scope 策略需产品确认 |

---

## 四、跨模块未覆盖（Temu 特有）

| ID | 能力 | 其他平台 | Temu |
|----|------|----------|------|
| TEMU-X01 | 今日订单列表 | AE/WM/国内等有 | **无** Temu 订单 Tab |
| TEMU-X02 | 平台订单推仓库 | `from-platform` 已支持 | Temu 运营页 **未接入** `PlatformShipPushDialog` |
| TEMU-X03 | 运营问题推任务 | 任务 API 已有 | 自动从 operational 生成的 issue 任务与分配任务并存，无统一关闭回路 |

> X01/X02 是否为 Temu 产品范围需确认；若要做，复用 `platformShipRequests` + 新建 Temu 订单读 API。

---

## 五、爬取与运维扩展（文档非目标，列为待规划）

| ID | 能力 | 说明 |
|----|------|------|
| TEMU-O01 | 定时自动爬取 | `temu-crawl` 明确非目标 |
| TEMU-O02 | 多店铺并行爬 | 非目标 |
| TEMU-O03 | 爬取任务列表 / 历史 | 仅 `GET /crawl/{jobId}`，无 Boss 任务看板 |
| TEMU-O04 | 生产 seed 关闭后的空租户冷启动 | `allow-seed: false` 时需 login + 真实爬取 |

---

## 六、汇总表（按优先级）

| 优先级 | ID 范围 | 说明 | 工期粗估 |
|--------|---------|------|----------|
| **P0** | TEMU-R01～R04、TEMU-D06 | 备货跟进后端化；shops 返回 `platform_account_id`；总览去 Local | ✅ 2026-07-06 |
| **P1** | TEMU-H01～H04 | 爆款通报持久化 | ✅ 2026-07-06 |
| **P1** | TEMU-U01～U02 | 空态与绑定引导 | 0.5～1 天 |
| **P2** | TEMU-C01～C05 | 竞店分析全链路（含爬虫） | 5～8 天 |
| **P2** | TEMU-D01～D02 | 本地仓库存对接 | 依赖仓库模块 |
| **P3** | TEMU-D05、TEMU-O03 | 历史报表日、爬取任务看板 | 1～2 天 |
| **待定** | TEMU-X01～X03 | 订单/推仓/任务闭环 | 视产品范围 |

---

## 七、建议新增 Java 端点一览

| 方法 | 路径 | 用途 |
|------|------|------|
| GET | `/api/temu/shops` | 响应增加 `platform_account_id`、`bound_store_name` |
| GET/PUT | `/api/temu/restock-status` | 备货跟进状态 |
| GET/POST | `/api/temu/hot-broadcasts` | 爆款通报 |
| POST | `/api/temu/hot-broadcasts/{id}/read` | 已读标记 |
| GET/POST/DELETE | `/api/temu/competitors` | 竞店 URL 管理 |
| POST | `/api/temu/competitors/{id}/crawl` | 触发竞店爬取 |
| GET | `/api/temu/competitors/{id}/snapshots` | 快照与报告 |
| GET | `/api/temu/crawl/jobs` | （可选）爬取任务历史 |

---

## 八、前端改动索引（实施时）

| 文件 | 未做实要点 |
|------|------------|
| `temuCompetitors.js` | 增加 `hasBackendSession` → `temuCompetitorsApi.js` |
| `temuRestockLocal.js` | 后端模式改为 API；`RestockPlanner` 增加状态更新 UI |
| `temuHotBroadcast.js` | 后端模式读写 API |
| `operationsOverview.js` | `restockStatus` 走后端，去掉 Local 种子 |
| `mapReptileSaleToTemuProduct.js` | 接入 `localStock`（仓库） |
| `TemuModuleView.vue` | 传 `useBackendData` 给竞店；历史日期；空态文案 |
| `CompetitorAnalysis.vue` | 后端模式禁用 Demo 分析或接真实 crawl |

---

## 九、审查结论

**Temu 核心运营链（绑定 → 爬取 → operational → 亏损/滞销/备货建议/趋势）已可用；竞店分析、爆款通报、备货跟进状态、本地仓库存、历史报表与若干体验空态仍停留在 localStorage / Demo，后端模式未完全去本地化。**
