# 权限体系 — PRD 实施包

> 实施前必读：`01-未对齐清单.md`、`02-技术债清单.md`  
> 验收用例：`04-回归测试用例.md`

---

## 里程碑总览

| 阶段 | 范围 | 交付 | 状态 |
|------|------|------|------|
| **M1** | 文档与对齐基线 | `docs/permissions/*` 四件套 | **完成** |
| **M2** | 租户功能开关（菜单模板） | Java API + Boss「功能开关」页 | 待实施 |
| **M3** | 双模式一致性 | Demo 菜单单源 + 路由守卫统一 | 待实施 |
| **M4** | 数据权限扩展（可选） | 统一 shop 主键 + 第二平台 scope | 待实施 |

## 实施阶段（P0～P3）

| 阶段 | 对应 | 工期 | 目标 | 关键文件 |
|------|------|------|------|----------|
| **P0** | M3 | 1–2 天 | 双模式菜单一致；`canAccessRoute` 统一 `menuCode` | `menuAuth.js`、`constants/menusSnapshot.js` |
| **P1** | M2 | 2–3 天 | 租户功能开关 `GET/PUT /api/tenant/features` | `TenantFeatureController`、Boss 设置页 |
| **P2** | M4 | 3–5 天 | shop_id 统一；warehouse grant 校验；platform-accounts 过滤 | `MemberScopeServiceImpl`、`DataScopeServiceImpl` |
| **P3** | 扩展 | 3–5 天（可选） | preset 套餐；`sys_menu` backfill；注册选套餐 | `TenantRegistrationServiceImpl`、迁移脚本 |

**原则**：M2–M4 默认不改变 `VITE_USE_TEMU_BACKEND=false` 的 Demo 开箱行为，除非 P0/M3 明确要求 Demo 守卫与后端语义对齐。

---

## M2：租户功能开关

### 功能需求

| ID | 需求 |
|----|------|
| FR-M2-01 | Boss 可查看本租户已开通的 `tenant_feature` 列表（含 label） |
| FR-M2-02 | Boss 可批量启停平台模块类 feature（如 `boss.platform.temu`） |
| FR-M2-03 | 关闭 feature 后，登录返回的 `menus` 不含对应 code |
| FR-M2-04 | 核心 admin 项不可关闭（白名单：`boss.settings`、`boss.employees`、`boss.accounts` 等） |
| FR-M2-05 | 员工门户菜单同步受 tenant feature 过滤（已有 `MenuServiceImpl` 逻辑，需保证 feature 关闭后员工 platform 菜单也消失） |

### API 契约

#### GET `/api/tenant/features`

**权限**：Boss JWT（`portal_role=boss` 或 `role=admin`）

**响应 200**：

```json
{
  "code": 0,
  "data": [
    {
      "feature_code": "boss.platform.temu",
      "enabled": true,
      "label": "Temu 运营",
      "portal": "boss",
      "platform": "temu"
    }
  ]
}
```

实现建议：join `sys_menu` 取 `label` / `portal` / `platform`，left join `tenant_feature`。

#### PUT `/api/tenant/features`

**权限**：Boss JWT

**请求体**：

```json
{
  "features": [
    { "feature_code": "boss.platform.temu", "enabled": false },
    { "feature_code": "employee.platform.temu", "enabled": false }
  ]
}
```

**规则**：

- 同一逻辑功能 Boss/Employee 成对关闭（或 Service 层根据 platform 级联）
- 白名单 code 拒绝关闭 → 400
- 仅更新本租户 `tenant_id`（JWT `tid`）

**响应 200**：

```json
{
  "code": 0,
  "message": "已更新 2 项功能开关",
  "data": { "updated": 2 }
}
```

#### POST `/api/auth/register` 扩展（可选）

**请求体增加**：

```json
{
  "company_name": "示例公司",
  "account": "boss@example.com",
  "password": "12345678",
  "feature_preset": "standard"
}
```

| preset | 说明 |
|--------|------|
| `standard` | 当前行为：全部 `sys_menu.code` enabled |
| `temu_only` | 仅 Temu + 核心 admin + 仓库相关 |
| `minimal` | 仅 dashboard、设置、运营绑定 |

### 前端改动

| 文件 | 改动 |
|------|------|
| 新建 `views/boss/TenantFeaturesView.vue` | 功能开关表格 + 保存 |
| `router/index.js` | 路由 `/boss/features`，`menuCode: 'boss.features'`（需 `sys_menu` 种子） |
| `api/tenantFeatures.js` | GET/PUT 封装 |

### M2 验收标准

- [ ] Boss 关闭 `boss.platform.walmart` 后，侧栏无 Walmart，直链 `/boss/walmart` 不可访问
- [ ] 员工已开通 Walmart 平台 scope，但 tenant 关闭 feature 后，员工菜单无 Walmart
- [ ] `GET /api/auth/session` 刷新后 menus 与开关一致
- [ ] 白名单项 PUT disabled → 400

---

## M3：双模式菜单一致

### 功能需求

| ID | 需求 |
|----|------|
| FR-M3-01 | Demo 侧栏菜单与 `sys_menu` 种子结构一致（code/path/label/parent_code） |
| FR-M3-02 | `canAccessRoute` 在 Demo 模式也依据 `menuCode`，不再 Boss/Warehouse 一律放行 |
| FR-M3-03 | 员工 Demo 菜单由 `employee.platforms` + `menuCodes` 计算，规则与 `MenuServiceImpl.allowEmployeeMenu` 文档对齐 |

### 实现要点

1. **菜单快照**  
   - 新建 `dev/vue-site/src/constants/menusSnapshot.js`（或构建脚本从 DB 导出）  
   - 内容与 `TenantSchemaMigration.seedMenus` 一致  
   - `fallbackSidebarMenus` 改为基于快照 + 与后端相同的过滤规则（简化版 tenant_feature 全开）

2. **`menuAuth.js`**  
   - `resolveSidebarMenus`：Demo 时用快照过滤，而非硬编码数组  
   - `canAccessRoute`：统一 `flattenMenuPaths(resolveSidebarMenus(auth))` 是否含目标 path，或对 `menuCode` 做 `hasMenuCode` 等价计算

3. **`router/index.js`**  
   - 确认所有需保护路由均有 `meta.menuCode`（已基本覆盖）

### M3 验收标准

- [ ] Demo 与 Backend Boss 侧栏条目 `code` 集合一致（feature 全开时）  
- [ ] Demo 员工 wang（Temu）无 Amazon 菜单，直链 `/employee/amazon` 被拦  
- [ ] `npm run build` 通过  

---

## M4：数据权限扩展（可选）

### 功能需求

| ID | 需求 |
|----|------|
| FR-M4-01 | `user_shop_scope` 支持存 `platform_account.id`，Service 层按平台解析为 Temu `shop_id` 或各平台主键 |
| FR-M4-02 | `GET /api/platform-accounts` 员工端按 platform + shop scope 过滤 |
| FR-M4-03 | `POST /api/warehouse/orders` 校验员工具备 `employee.warehouse` menu grant |
| FR-M4-04 | 运营绑定写 scope 时，Temu 店铺写 `temu_shop.shop_id`，其他平台写 `platform_account.id` |

### 数据模型草案

```text
user_shop_scope (
  tenant_id, user_id, platform, shop_id  -- shop_id 语义由 platform 解释
)
```

`MemberScopeServiceImpl` 保存时：

- `platform=temu` → 校验 shop_id ∈ `temu_shop`  
- 其他 → 校验 shop_id ∈ `platform_account`  

### M4 验收标准

- [ ] 员工 A 仅分配 Temu 店铺 1，operational/crawl 不能访问店铺 2  
- [ ] 无 `employee.warehouse` grant 的员工 POST 出库单 → 403  
- [ ] `GET /api/platform-accounts?platform=amazon` 员工仅见 scope 内店铺  

---

## P3：菜单模板产品化（可选）

### 功能需求

| ID | 需求 |
|----|------|
| FR-P3-01 | 注册支持 `feature_preset`（`standard` / `temu_only` / `minimal`） |
| FR-P3-02 | `sys_menu` 新增 code 时，迁移 backfill 全租户 `tenant_feature`（默认 disabled） |
| FR-P3-03 | 可选：从模板租户 `copy_from_template_tenant_id` 复制 feature 集 |

### P3 验收标准

- [ ] `temu_only` 注册后 Boss 侧栏无 Walmart/Amazon 模块
- [ ] 迁移新增 menu 后，老租户 PUT features 可手动开启新项
- [ ] backfill 不覆盖已有 enabled 状态

---

## 改动文件清单（汇总）

### M2（Java）

- 新建 `controller/TenantFeatureController.java`
- 新建 `service/TenantFeatureService.java` + `impl`
- 修改 `WebConfig.java`（若需放行路径）
- 修改 `TenantSchemaMigration.java`（新增 `boss.features` 菜单种子，可选）

### M2（Vue）

- 新建 `api/tenantFeatures.js`、`views/boss/TenantFeaturesView.vue`
- 修改 `router/index.js`、`PortalLayout.vue`（设置子菜单）

### M3（Vue）

- 新建 `constants/menusSnapshot.js`
- 修改 `utils/menuAuth.js`
- 可选：脚本 `scripts/export-sys-menu.js`

### M4（Java + Vue）

- `MemberScopeServiceImpl.java`、`DataScopeServiceImpl.java`
- `PlatformAccountServiceImpl.java`（列表过滤）
- `WarehouseOrderServiceImpl.java`（grant 校验）
- `scope.js`、`EmployeeBindingView.vue`（ID 语义统一）

---

## 非目标

- 按钮级 / action 级 RBAC  
- 子租户继承父租户 `tenant_feature`  
- 非 Temu 平台真后端（见 `docs/开发顺序.md` Phase 3）  
- 本 PRD 不包含自动化测试实现（用例见 `04-回归测试用例.md`）

---

## 运维说明

- 修改 `sys_menu` 种子后：执行迁移 + M2 backfill `tenant_feature`（TD-PERM-07）  
- 功能开关变更后：建议前端 `auth.refreshSession()` 或提示用户重新登录  

---

## 相关文档

- 未对齐项：`01-未对齐清单.md`  
- 技术债：`02-技术债清单.md`  
- 测试：`04-回归测试用例.md`
