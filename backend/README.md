# CrossHub Temu 后端（项目内独立）

Python 负责 **爬数 + 入库**，Java 负责 **读 API + 预警算法 + JWT 认证**。  
共用 SQLite：`backend/data/crosshub.db`。

## 架构

```
py login.py          ← 首次手动登录 Temu（持久化 Cookie）
py crawl.py          ← Playwright 调卖家后台 API 爬数
    ↓ 写入 SQLite
backend/data/crosshub.db
    ↓ JPA 读取
Java API (:8080)
    ↓
Vue TemuModuleView
```

---

## 0. 安装 JDK / Maven（本机未装时）

```powershell
cd d:\NIUBI\SaaS-HZ_WEB_Demo
powershell -ExecutionPolicy Bypass -File scripts\setup-java.ps1
. .\scripts\env-java.ps1
```

JDK 与 Maven 会安装到 `tools/jdk-17`、`tools/maven`（便携，不改系统环境）。

---

## 1. Python 环境与 Playwright

```powershell
cd backend/python
py -m pip install -r requirements.txt
py -m playwright install chrome
```

复制配置：`copy .env.example .env`

### 首次登录 Temu（必做）

```powershell
py login.py
```

- 默认 **有头模式** + **本机 Chrome**（`TEMU_BROWSER_CHANNEL=chrome`）
- 登录态保存在 `backend/python/.temu-browser-profile`（勿删）
- 登录后需在后台 **选好店铺**，终端里应能看到 `agentseller-mall-info-id`

### 爬取入库

```powershell
py crawl.py
```

| 参数 | 说明 |
|------|------|
| `--date 2026-06-25` | 指定上报日期 |
| `--seed` | 不打开浏览器，用 demo 种子数据 |

### 反检测要点（Temu 易识别自动化）

| 措施 | 说明 |
|------|------|
| 持久化 Profile | 复用真实登录 Cookie，避免每次新环境 |
| 有头 + 本机 Chrome | `TEMU_HEADLESS=0`，优先 `channel=chrome` |
| 去 webdriver 特征 | `--disable-blink-features=AutomationControlled` + init script |
| 浏览器内发 API | `page.request.post`，不用裸 httpx |
| 随机间隔 | 默认 0.8–2.2s  между请求 |

爬取逻辑对齐 Commander Agent：  
`agentseller.temu.com/mms/venom/api/supplier/sales/management/listOverall`

---

## 2. Java API

```powershell
. ..\..\scripts\env-java.ps1
mvn -f backend/java/pom.xml spring-boot:run
```

或：`powershell -File scripts\run-java-api.ps1`

### 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/login` | 登录，返回 JWT |
| GET | `/api/temu/shops` | 店铺列表 |
| GET | `/api/temu/operational?shop_id=` | 商品 + 四类预警 |
| GET | `/api/temu/trend?days=7` | 销量趋势 |

### 演示账号（`app_user`，爬虫初始化时写入）

| 角色 | 账号 | 密码 |
|------|------|------|
| Boss | `admin@crosshub.cn` | `12345678` |
| 员工 | `wangyiming@yituo-outdoor.com` | `Emp@Demo123` |
| 员工 | `liting@yituo-outdoor.com` | `Emp@Demo456` |

---

## 3. 前端

```powershell
cd dev/vue-site
npm run dev
```

Boss 登录后进入 **Temu 运营**，应显示「后端实时数据」。
