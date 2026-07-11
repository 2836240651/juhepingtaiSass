# 聚合平台 SaaS（CrossHub）

跨境电商 **多平台聚合运营** SaaS 系统：Boss / 运营 / 仓管三门户，多租户隔离，菜单与数据权限，Temu / AliExpress / Amazon 等平台运营与仓库协同。

**在线演示：** https://www.yoto.work/crosshub/

**仓库：** https://github.com/2836240651/juhepingtaiSass

---

## 功能概览

| 能力 | 说明 |
|------|------|
| **三门户** | Boss 管理端、运营员工端、仓库管理员端 |
| **多租户** | JWT 租户隔离（`tid`）、成员管理、功能开关 |
| **权限体系** | 菜单授权、平台/店铺/分仓数据范围 |
| **跨境平台** | Temu、AliExpress、Amazon、Walmart、1688 |
| **国内电商** | 拼多多、抖音、视频号 |
| **独立站** | Shopify / WordPress 演示模块 |
| **Temu 真爬取** | Playwright 爬数 → SQLite → Java API → 前端预警 |
| **AliExpress** | 订单/违规/热榜，Java + Python 爬虫联调 |
| **Amazon** | 紫鸟同步助手、运营数据、Agent 节点 |
| **仓库协同** | 分仓设置、出库单审批、仓管任务中心 |
| **任务分配** | Boss 向运营/仓管分配任务，反馈时间线同步 |

### 平台联调状态

| 平台 | 后端 API | 真实爬取/同步 | 说明 |
|------|----------|---------------|------|
| Temu | ✅ Java | ✅ Python Playwright | 完整闭环 |
| AliExpress | ✅ Java | ✅ Python | 订单、违规、热榜 |
| Amazon | ✅ Java | ⚙️ Agent + 紫鸟 | 同步助手节点 |
| 仓库/租户/账户 | ✅ Java | — | 生产可用 |
| Walmart / 1688 / DTC / 国内 | 前端 Demo | 模拟刷新 | localStorage 演示层 |
| 任务分配 | 前端 Demo | — | 待 Java 持久化 |

---

## 技术栈

| 模块 | 路径 | 技术 |
|------|------|------|
| 前端 | `dev/vue-site/` | Vue 3 + Vite + Element Plus + Pinia |
| Java API | `backend/java/` | Spring Boot + JPA + SQLite + JWT |
| Python 爬虫/Agent | `backend/python/` | Playwright、竞店监控、平台适配器 |
| Express Demo | `script/api-server/` | Node.js Express（健康检查桩） |
| 数据 | `backend/data/crosshub.db` | 四栈共用 SQLite |

---

## 项目结构

```
juhepingtaiSass/
├── dev/vue-site/              # Vue 前端（Boss / 员工 / 仓管）
├── backend/
│   ├── java/                  # Spring Boot 多平台 API
│   │   └── src/.../crosshub/  # auth / tenant / temu / amazon / aliexpress / warehouse / agent / monitor
│   ├── python/                # 爬虫、Agent、竞店快照
│   └── data/                  # crosshub.db（本地，不入库）
├── script/api-server/         # Express 演示接口
├── deploy/                    # Docker、Nginx 反代
├── docs/                      # 各模块 PRD、联调手册
└── scripts/                   # 本地启动、部署、回归脚本
```

---

## 快速开始

### 环境要求

- **Node.js** 18+（推荐 22+，见 `dev/vue-site/package.json` engines）
- **Python** 3.10+（爬虫 / Agent）
- **JDK 17 + Maven**（可用便携脚本安装，不改系统环境）

### 1. 安装 JDK / Maven（本机未装时）

```powershell
cd D:\NIUBI\SaaS-HZ_WEB_Demo
powershell -ExecutionPolicy Bypass -File scripts\setup-java.ps1
. .\scripts\env-java.ps1
```

### 2. 一键本地启动

```powershell
powershell -File scripts\start-local.ps1
```

或分别启动：

| 服务 | 端口 | 命令 |
|------|------|------|
| Java API | `18080` | `powershell -File scripts\run-java-api.ps1` |
| Express | `3000` | `cd script\api-server; npm install; npm start` |
| Vue dev | `5173` | `cd dev\vue-site; npm install; npm run dev` |

访问：http://localhost:5173

### 3. 后端联调开关

`dev/vue-site/.env`（参考 `.env.example`）：

```env
VITE_USE_TEMU_BACKEND=true
```

开启后 Boss 登录走 Java API（认证、租户、仓库、账户绑定、Temu/AliExpress/Amazon 等）；默认 `false` 时为纯前端 Demo（localStorage）。

### 4. 演示账号

| 角色 | 账号 | 密码 |
|------|------|------|
| Boss | `admin@crosshub.cn` | `12345678` |
| 运营 | `wangyiming@yituo-outdoor.com` | `Emp@Demo123` |
| 运营 | `liting@yituo-outdoor.com` | `Emp@Demo456` |

仓管账号由 Boss 在 **设置 → 仓库人员** 中创建。

---

## Temu 爬虫（可选）

```powershell
cd backend\python
py -m pip install -r requirements.txt
py -m playwright install chrome
copy .env.example .env

# 首次登录（按租户隔离浏览器 Profile）
py login.py --tenant-id 1

# 爬取入库
py crawl.py --tenant-id 1
# 或无浏览器种子数据
powershell -File ..\..\scripts\crawl-tenant.ps1 -TenantId 1 -Seed
```

前端 Temu 模块点击 **刷新数据** → `POST /api/temu/crawl` → Java 调 Python → 轮询任务状态 → 重载运营数据。

---

## API 代理

Vite 开发代理（`dev/vue-site/vite.config.js`）：

| 前缀 | 目标 | 说明 |
|------|------|------|
| `/api/temu` | Java `:18080` | Temu 运营、爬取 |
| `/api/auth` | Java `:18080` | 登录、注册、会话 |
| `/api/warehouse` | Java `:18080` | 分仓、出库单、仓管 |
| `/api/tenant` | Java `:18080` | 租户成员、权限 |
| `/api/platform-accounts` | Java `:18080` | 店铺绑定 |
| `/api/aliexpress` | Java `:18080` | AliExpress |
| `/api/amazon` | Java `:18080` | Amazon |
| `/api/agent` | Java `:18080` | 同步助手节点 |
| `/api/monitor` | Java `:18080` | 竞店监控 |
| `/api/tasks`、`/api/ops-feedback` | Java `:18080` | 任务与反馈 |
| 其余 `/api/*` | Express `:3000` | 健康检查桩 |

---

## 核心 API 一览

### 认证

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 注册并创建租户 |
| POST | `/api/auth/login` | 登录，返回 JWT、菜单、数据范围 |
| GET | `/api/auth/session` | 当前会话（续期校验） |

### 店铺绑定

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/platform-accounts` | 租户内店铺（可选 `?platform=`） |
| POST | `/api/platform-accounts/bind` | 绑定/更新店铺 |
| DELETE | `/api/platform-accounts/{id}` | 解除绑定 |

### Temu

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/temu/operational` | 商品与四类预警 |
| GET | `/api/temu/trend` | 销量趋势 |
| POST | `/api/temu/crawl` | 触发异步爬取 |
| GET | `/api/temu/crawl/{jobId}` | 爬取任务状态 |

### 仓库

| 方法 | 路径 | 说明 |
|------|------|------|
| GET/POST | `/api/warehouse/sites` | 分仓设置 |
| GET/POST | `/api/warehouse/orders` | 出库单（提交→审批→发货） |
| GET/POST | `/api/warehouse/members` | 仓管人员与分仓范围 |

更多接口见 `docs/` 目录下各平台 PRD 与联调手册。

---

## 生产部署

线上 Docker 运行双后端（绑定 `127.0.0.1`），Nginx 反代静态前端与 API。

| 服务 | 端口 | 说明 |
|------|------|------|
| Java API | `18080` | 认证、租户、多平台 |
| Express | `18081` | 演示接口 |
| 静态前端 | Nginx | `/crosshub/` |

```powershell
# 设置 SSH 环境变量（勿写入仓库）后执行
$env:CROSSHUB_SSH_HOST = "your-server"
$env:CROSSHUB_SSH_USER = "root"
$env:CROSSHUB_SSH_PASSWORD = "your-password"
powershell -File scripts\deploy-server.ps1
```

构建生产前端（子路径 `/crosshub/`）：

```powershell
cd dev\vue-site
$env:VITE_BASE_PATH="/crosshub/"
npm run build
```

**Java 后端变更后须重启：**

```powershell
powershell -File scripts\restart-java-api.ps1
```

---

## 文档索引

| 主题 | 路径 |
|------|------|
| 全局开发顺序 | `docs/开发顺序.md` |
| Temu 爬取 | `docs/temu-crawl/` |
| AliExpress / Amazon 联调 | `docs/api-integration/`、`docs/amazon-integration/` |
| 竞店监控 | `docs/competitor-monitor/` |
| 权限对齐 | `docs/permissions/` |
| Java 包结构 | `backend/java/PACKAGES.md` |

---

## 多租户约定

- **Java**：JWT 携带 `tid`；`/api/auth/register` 创建租户
- **Python**：`--tenant-id` / `TENANT_ID`；Profile 目录 `.temu-browser-profile/tenant-{id}`
- **Vue**：`src/utils/tenantStorage.js` 按 `crosshub:t{id}:` 隔离 localStorage
- **开发 JWT 密钥**：见 `backend/java/src/main/resources/application.yml`（生产务必更换）

---

## 许可证

内部演示 / 学习评估项目。生产使用前请更换密钥、禁用 Demo 账号，并审查 `docs/permissions/` 中的权限对齐清单。
