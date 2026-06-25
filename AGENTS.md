# Agent Instructions

## Package Manager
- Frontend (`dev/vue-site`): **npm**
- Temu Python crawler (`backend/python`): **py** + Playwright（建议本机 Chrome）
- Temu Java API (`backend/java`): 便携 JDK/Maven → `scripts/setup-java.ps1`
- Optional Express demo (`script/api-server`): **npm**

## Commands

| Task | Command |
|------|---------|
| 安装 JDK 17 + Maven（便携） | `powershell -File scripts/setup-java.ps1` |
| 启用 Java 环境 | `. .\scripts\env-java.ps1` |
| Temu 首次登录（Playwright） | `py backend/python/login.py` |
| Temu 爬虫入库 | `py backend/python/crawl.py` |
| Temu 种子数据（无浏览器） | `py backend/python/crawl.py --seed` |
| Java Temu API | `mvn -f backend/java/pom.xml spring-boot:run` |
| Frontend dev | `cd dev/vue-site && npm run dev` |

## External References
| Need | File |
|------|------|
| Frontend entry & UI stack | `dev/vue-site/src/main.js` |
| Routes & role guard | `dev/vue-site/src/router/index.js` |
| Sidebar menus (boss/employee) | `dev/vue-site/src/layouts/PortalLayout.vue` |
| Platform taxonomy | `dev/vue-site/src/constants/platforms.js` |
| Employee menu scoping | `dev/vue-site/src/utils/scope.js` |
| Demo data & localStorage APIs | `dev/vue-site/src/api/*Local.js`, `dev/vue-site/src/api/platformAccounts.js` |
| Optional HTTP client | `dev/vue-site/src/api/http.js` |
| Vite proxy (`/api/temu`,`/api/auth` → `:8080`; `/api` → `:3000`) | `dev/vue-site/vite.config.js` |
| Temu Java API + Python 爬虫 | `backend/README.md` |
| Temu 前端 API 客户端 | `dev/vue-site/src/api/temuApi.js` |
| Express demo backend | `script/api-server/index.js` |

## Key Conventions
- Monorepo layout: Vue app in `dev/vue-site/`; demo Express in `script/api-server/`.
- Import alias: `@` → `dev/vue-site/src/`.
- Roles: `boss` (`/boss/*`) vs `employee` (`/employee/*`); guard in `router/index.js`.
- Boss sees all platform menus; employee menus come from `employeeModuleMenus()` based on `auth.employee.platforms`.
- Store visibility: `scopeStores()` filters by `assignedStoreIds` or platform list.
- **Demo-first data**: most platform ops use `*Local.js` + `localStorage`; `platformAccounts.js` orchestrates seed/ensure helpers.
- Platform module pattern: `views/<platform>/*ModuleView.vue` + `components/<platform>/` + `constants/<platform>*.js` + `utils/<platform>.js`.
- Domestic platforms (拼多多/抖音/视频号): shared `useDomesticModule` composable + `api/domesticPlatforms.js`.
- New platform: add boss + employee routes, `PortalLayout` boss menu, `employeeModuleMenus` def, view/components/constants, and `platformAccounts` fetch/seed.
- **Temu 运营**：Python 爬虫 → `backend/data/crosshub.db` → Java `:8080` → 前端 `temuApi.js`（见 `backend/README.md`）。
- Other demo APIs: Vite proxies `/api` to `localhost:3000` (Express; store-binding for `temu`/`aliexpress` labels only).
- UI: Element Plus; page shell via `PageHeader` + `PageScroll`.
- No ESLint/test runner configured—do not add tooling unless requested.

## Commit Attribution
AI commits MUST include:
```
Co-Authored-By: (the agent's name and attribution byline)
```
