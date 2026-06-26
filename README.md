# CrossHub SaaS Web Demo

跨境电商多平台运营 SaaS 演示系统：Boss / 员工双门户、多租户、菜单与数据权限、Temu 实时运营数据。

**在线演示：** https://www.yoto.work/crosshub/

## 技术栈

| 模块 | 路径 | 技术 |
|------|------|------|
| 前端 | `dev/vue-site/` | Vue 3 + Vite + Element Plus + Pinia |
| Java API（Temu / 认证 / 租户） | `backend/java/` | Spring Boot + JPA + SQLite + JWT |
| Express Demo API | `script/api-server/` | Node.js Express |
| Python 爬虫 | `backend/python/` | Playwright（脚本，非常驻服务） |

## 项目结构

```
SaaS-HZ_WEB_Demo/
├── dev/vue-site/          # Vue 前端
├── backend/java/          # Spring Boot Temu & 租户 API
├── backend/python/        # Temu 爬数入库
├── backend/data/          # 共用 SQLite（crosshub.db）
├── script/api-server/     # Express 演示接口
├── deploy/                # Docker 与 Nginx 反代配置
└── scripts/               # 本地启动、部署脚本
```

## 核心能力

- **多租户**：租户隔离、成员管理、功能开关（`Tenant` / `TenantFeature`）
- **权限体系**：Boss / 员工门户、菜单授权（`SysMenu` / `UserMenuGrant`）、平台与店铺数据范围（`UserPlatformScope` / `UserShopScope`）
- **Temu 运营**：Python Playwright 爬数 → SQLite → Java API 预警与趋势 → 前端 Temu 模块
- **双 API 代理**：`/api/temu`、`/api/auth` → Java；其余 `/api` → Express

## 本地开发

### 前置

- Node.js 18+
- Python 3.10+（爬虫）
- JDK 17 + Maven（可用 `scripts/setup-java.ps1` 便携安装到 `tools/`）

### 一键启动

```powershell
cd D:\NIUBI\SaaS-HZ_WEB_Demo
powershell -File scripts\start-local.ps1
```

分别启动：

| 服务 | 端口 | 命令 |
|------|------|------|
| Java API | `18080` | `powershell -File scripts\run-java-api.ps1` |
| Express | `3000` | `cd script\api-server; npm start` |
| Vue dev | `5173` | `cd dev\vue-site; npm run dev` |

Vite 代理：`/api/temu`、`/api/auth` → `18080`；其余 `/api` → `3000`。

### 演示账号

| 角色 | 账号 | 密码 |
|------|------|------|
| Boss | `admin@crosshub.cn` | `12345678` |
| 员工 | `wangyiming@yituo-outdoor.com` | `Emp@Demo123` |
| 员工 | `liting@yituo-outdoor.com` | `Emp@Demo456` |

### Temu 爬虫（可选）

详见 [`backend/README.md`](backend/README.md)。简要步骤：

```powershell
cd backend/python
py -m pip install -r requirements.txt
py -m playwright install chrome
py login.py    # 首次手动登录 Temu
py crawl.py    # 爬取入库
```

## 生产部署

线上使用 Docker 运行双后端（仅绑定 `127.0.0.1`），Nginx 反代静态前端与 API。

| 服务 | 端口 | 说明 |
|------|------|------|
| Java API | `18080` | Temu、认证、租户 |
| Express | `18081` | 演示接口 |
| 静态前端 | Nginx | `/crosshub/` |

部署前设置 SSH 环境变量（勿写入仓库）：

```powershell
$env:CROSSHUB_SSH_HOST = "your-server"
$env:CROSSHUB_SSH_USER = "root"
$env:CROSSHUB_SSH_PASSWORD = "your-password"
powershell -File scripts\deploy-server.ps1
```

仅更新前端静态资源：

```powershell
node scripts\deploy-web-only.js
```

构建生产前端（子路径 `/crosshub/`）：

```powershell
cd dev\vue-site
$env:VITE_BASE_PATH="/crosshub/"
npm run build
```

## API 概览

### 认证（Java `:18080`）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/login` | 登录，返回 JWT、菜单、数据范围 |
| GET | `/api/auth/me` | 当前用户与会话信息 |

### Temu（Java）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/temu/shops` | 店铺列表（受数据范围过滤） |
| GET | `/api/temu/operational` | 商品与四类预警 |
| GET | `/api/temu/trend` | 销量趋势 |

### 租户成员（Java）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/tenant/members` | 成员列表 |
| POST | `/api/tenant/members` | 新增成员 |
| PUT | `/api/tenant/members/{id}` | 更新成员权限 |

## 许可证

内部演示项目，仅供学习与评估使用。
