# Java 后端包结构（多平台）

根包由 `com.crosshub.temu` 调整为 **`com.crosshub`**，按业务域拆分：

```
com.crosshub/
├── CrosshubApplication.java      # 启动类（原 CrosshubTemuApplication）
├── common/                       # ApiResult、AppErrorCode、DemoDataFilter、全局异常
├── config/                       # WebConfig、CrawlerProperties
│   └── migration/                # SQLite 启动迁移 V2…
├── security/                     # JWT、AuthContext、拦截器
├── auth/                         # 登录注册、AppUser
├── tenant/                       # 租户、成员、菜单、数据范围
├── platform/                     # 跨平台店铺绑定 platform_account
├── warehouse/                    # 分仓、出库单、仓管
├── task/                         # Boss 任务分配、运营反馈
├── temu/                         # Temu 运营、爬虫、热榜、备货
├── amazon/                       # Amazon 紫鸟同步（待补齐源码）
├── aliexpress/                   # AliExpress 爬虫（待补齐源码）
├── agent/                        # 本地同步助手节点（待补齐源码）
└── monitor/                      # 竞店快照（待补齐源码）
```

## 各平台子包约定

每个平台模块统一分层：

| 子包 | 职责 |
|------|------|
| `controller` | REST 路由，`/api/<platform>/**` |
| `service` / `service.impl` | 业务逻辑 |
| `entity` / `repository` | JPA 持久化 |
| `dto` | 请求/响应 record |
| `mapper` | Entity ↔ JSON（可选） |

## 共享模块

| 模块 | 说明 |
|------|------|
| `platform` | `PlatformAccount` 全平台店铺主数据 |
| `tenant` | `DataScopeService` 租户/员工数据范围 |
| `security` | Boss/员工 JWT；Agent 用 `X-Agent-Token` |
| `config` | 爬虫路径、异步线程池、DB 迁移 |

## 迁移脚本

| 脚本 | 用途 |
|------|------|
| `scripts/restore-from-tree.py` | 从 git dangling tree 恢复 `com.crosshub.temu` 源码 |
| `scripts/restructure-packages.py` | 拆分到 `com.crosshub.*`（先移到 `_legacy_temu_pkg` 再清理，避免误删 `temu` 模块） |
| `scripts/fix-packages-from-path.py` | 按目录修正 `package` 声明与 import |

## 新增平台 Checklist

1. 在 `com.crosshub.<platform>/` 下按上表建 controller/service/entity
2. `AppErrorCode` 增加平台错误码
3. `WebConfig` 注册 JWT 拦截路径 `/api/<platform>/**`
4. `dev/vue-site/vite.config.js` 代理到 `:18080`
5. 如需 DB 变更，在 `config/migration/` 增加 `V*.java`

## 当前状态（2026-07-10）

- ✅ 已从 git dangling tree 恢复 **112** 个基础类并完成分包，`mvn compile` 通过
- ⚠️ **Amazon / Agent / AliExpress / Monitor** 及迁移 V9–V19 曾在未提交工作区，分包误操作后丢失，需按 `docs/amazon-integration/` 等文档在新包路径下重建
