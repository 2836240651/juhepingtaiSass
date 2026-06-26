package com.crosshub.temu.config;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

import java.util.Arrays;
import java.util.List;
import java.util.Locale;

@Component
public class TenantSchemaMigration {
    private static final Logger log = LoggerFactory.getLogger(TenantSchemaMigration.class);

    private final JdbcTemplate jdbc;

    public TenantSchemaMigration(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    @EventListener(ApplicationReadyEvent.class)
    public void migrate() {
        createTables();
        addColumnIfMissing("app_user", "tenant_id", "INTEGER");
        addColumnIfMissing("app_user", "job_title", "TEXT NOT NULL DEFAULT ''");
        addColumnIfMissing("app_user", "phone", "TEXT NOT NULL DEFAULT ''");
        addColumnIfMissing("app_user", "status", "TEXT NOT NULL DEFAULT 'active'");
        addColumnIfMissing("app_user", "created_at", "TEXT NOT NULL DEFAULT ''");
        addColumnIfMissing("temu_shop", "tenant_id", "INTEGER NOT NULL DEFAULT 1");
        addColumnIfMissing("temu_sale", "tenant_id", "INTEGER NOT NULL DEFAULT 1");
        seedTenant();
        backfillTenantIds();
        seedMenus();
        seedTenantFeatures();
        seedUserScopes();
        log.info("Tenant schema migration completed");
    }

    private void createTables() {
        jdbc.execute("""
                CREATE TABLE IF NOT EXISTS tenant (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  code TEXT NOT NULL UNIQUE,
                  status TEXT NOT NULL DEFAULT 'active'
                )
                """);
        jdbc.execute("""
                CREATE TABLE IF NOT EXISTS sys_menu (
                  code TEXT PRIMARY KEY,
                  parent_code TEXT,
                  portal TEXT NOT NULL,
                  platform TEXT,
                  path TEXT NOT NULL,
                  label TEXT NOT NULL,
                  menu_type TEXT NOT NULL,
                  sort_order INTEGER NOT NULL DEFAULT 0
                )
                """);
        jdbc.execute("""
                CREATE TABLE IF NOT EXISTS tenant_feature (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  tenant_id INTEGER NOT NULL,
                  feature_code TEXT NOT NULL,
                  enabled INTEGER NOT NULL DEFAULT 1,
                  UNIQUE (tenant_id, feature_code)
                )
                """);
        jdbc.execute("""
                CREATE TABLE IF NOT EXISTS user_platform_scope (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  tenant_id INTEGER NOT NULL,
                  user_id INTEGER NOT NULL,
                  platform TEXT NOT NULL,
                  UNIQUE (tenant_id, user_id, platform)
                )
                """);
        jdbc.execute("""
                CREATE TABLE IF NOT EXISTS user_shop_scope (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  tenant_id INTEGER NOT NULL,
                  user_id INTEGER NOT NULL,
                  platform TEXT NOT NULL,
                  shop_id TEXT NOT NULL,
                  UNIQUE (tenant_id, user_id, platform, shop_id)
                )
                """);
        jdbc.execute("""
                CREATE TABLE IF NOT EXISTS user_menu_grant (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  tenant_id INTEGER NOT NULL,
                  user_id INTEGER NOT NULL,
                  menu_code TEXT NOT NULL,
                  UNIQUE (tenant_id, user_id, menu_code)
                )
                """);
    }

    private void addColumnIfMissing(String table, String column, String ddl) {
        List<String> cols = jdbc.query(
                "PRAGMA table_info(" + table + ")",
                (rs, rowNum) -> rs.getString("name").toLowerCase(Locale.ROOT)
        );
        if (cols.stream().noneMatch(c -> c.equals(column.toLowerCase(Locale.ROOT)))) {
            jdbc.execute("ALTER TABLE " + table + " ADD COLUMN " + column + " " + ddl);
            log.info("Added column {}.{}", table, column);
        }
    }

    private void seedTenant() {
        jdbc.update("""
                INSERT OR IGNORE INTO tenant (id, name, code, status)
                VALUES (1, '泰州亿拓户外用品有限公司', 'yituo-outdoor', 'active')
                """);
    }

    private void backfillTenantIds() {
        jdbc.update("UPDATE app_user SET tenant_id = 1 WHERE tenant_id IS NULL");
        jdbc.update("UPDATE temu_shop SET tenant_id = 1 WHERE tenant_id IS NULL");
        jdbc.update("UPDATE temu_sale SET tenant_id = 1 WHERE tenant_id IS NULL");
        jdbc.update("""
                UPDATE app_user SET job_title = nickname
                WHERE (job_title IS NULL OR job_title = '')
                  AND role = 'user'
                """);
        jdbc.update("""
                UPDATE app_user SET job_title = '企业管理员'
                WHERE (job_title IS NULL OR job_title = '') AND role = 'admin'
                """);
        jdbc.update("""
                UPDATE app_user SET enterprise = (SELECT name FROM tenant WHERE id = app_user.tenant_id)
                WHERE tenant_id IS NOT NULL
                """);
        jdbc.update("""
                UPDATE app_user SET status = 'active'
                WHERE status IS NULL OR status = ''
                """);
        jdbc.update("""
                UPDATE app_user SET created_at = datetime('now', 'localtime')
                WHERE (created_at IS NULL OR created_at = '') AND role = 'user'
                """);
    }

    private void seedMenus() {
        List<Object[]> rows = Arrays.asList(
                menu("boss.employees", null, "boss", null, "/boss/employees", "员工绑定", "admin", 10),
                menu("boss.dashboard", null, "boss", null, "/boss/dashboard", "运营总览", "admin", 20),
                menu("boss.tasks", null, "boss", null, "/boss/tasks", "任务分配", "admin", 30),
                menu("boss.platform.temu", null, "boss", "temu", "/boss/temu", "Temu 运营", "module", 40),
                menu("boss.platform.aliexpress", null, "boss", "aliexpress", "/boss/aliexpress", "AliExpress 运营", "module", 50),
                menu("boss.platform.amazon", null, "boss", "amazon", "/boss/amazon", "Amazon 运营", "module", 60),
                menu("boss.platform.walmart", null, "boss", "walmart", "/boss/walmart", "Walmart 运营", "module", 70),
                menu("boss.platform.pdd", null, "boss", "pdd", "/boss/pdd", "拼多多运营", "module", 80),
                menu("boss.platform.douyin", null, "boss", "douyin", "/boss/douyin", "抖音运营", "module", 90),
                menu("boss.platform.channels", null, "boss", "channels", "/boss/channels", "视频号运营", "module", 100),
                menu("boss.platform.1688", null, "boss", "1688", "/boss/1688", "1688 运营", "module", 110),
                menu("boss.platform.dtc", null, "boss", "dtc", "/boss/dtc", "独立站运营", "module", 120),
                menu("boss.accounts", null, "boss", null, "/boss/accounts", "账户绑定", "admin", 130),

                menu("employee.dashboard", null, "employee", null, "/employee/dashboard", "我的工作台", "base", 10),
                menu("employee.tasks", null, "employee", null, "/employee/tasks", "任务中心", "base", 90),
                menu("employee.ai", null, "employee", null, "/employee/ai", "AI 办公", "base", 100),
                menu("employee.platform.temu", null, "employee", "temu", "/employee/temu", "Temu 运营", "module", 20),
                menu("employee.platform.aliexpress", null, "employee", "aliexpress", "/employee/aliexpress", "AliExpress 运营", "module", 30),
                menu("employee.platform.amazon", null, "employee", "amazon", "/employee/amazon", "Amazon 运营", "module", 40),
                menu("employee.platform.walmart", null, "employee", "walmart", "/employee/walmart", "Walmart 运营", "module", 50),
                menu("employee.platform.pdd", null, "employee", "pdd", "/employee/pdd", "拼多多运营", "module", 60),
                menu("employee.platform.douyin", null, "employee", "douyin", "/employee/douyin", "抖音运营", "module", 70),
                menu("employee.platform.channels", null, "employee", "channels", "/employee/channels", "视频号运营", "module", 80),
                menu("employee.platform.1688", null, "employee", "1688", "/employee/1688", "1688 运营", "module", 85),
                menu("employee.platform.dtc", null, "employee", "dtc", "/employee/dtc", "独立站运营", "module", 88)
        );
        for (Object[] row : rows) {
            jdbc.update("""
                    INSERT OR REPLACE INTO sys_menu
                    (code, parent_code, portal, platform, path, label, menu_type, sort_order)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, row);
        }
    }

    private Object[] menu(String code, String parent, String portal, String platform,
                          String path, String label, String type, int sort) {
        return new Object[]{code, parent, portal, platform, path, label, type, sort};
    }

    private void seedTenantFeatures() {
        List<String> codes = jdbc.query("SELECT code FROM sys_menu", (rs, i) -> rs.getString(1));
        for (String code : codes) {
            jdbc.update("""
                    INSERT OR IGNORE INTO tenant_feature (tenant_id, feature_code, enabled)
                    VALUES (1, ?, 1)
                    """, code);
        }
    }

    private void seedUserScopes() {
        seedPlatformScope("wangyiming@yituo-outdoor.com", "temu");
        seedPlatformScope("liting@yituo-outdoor.com", "temu");
        seedShopScopesForUser("wangyiming@yituo-outdoor.com", "temu", 2);
    }

    private void seedShopScopesForUser(String username, String platform, int limit) {
        Long userId = jdbc.query("""
                SELECT id FROM app_user WHERE lower(username) = lower(?) LIMIT 1
                """, rs -> rs.next() ? rs.getLong(1) : null, username);
        if (userId == null || limit <= 0) return;

        List<String> shopIds = jdbc.query(
                "SELECT shop_id FROM temu_shop WHERE tenant_id = 1 ORDER BY shop_id LIMIT ?",
                (rs, rowNum) -> rs.getString(1),
                limit
        );
        for (String shopId : shopIds) {
            jdbc.update("""
                    INSERT OR IGNORE INTO user_shop_scope (tenant_id, user_id, platform, shop_id)
                    VALUES (1, ?, ?, ?)
                    """, userId, platform, shopId);
        }
    }

    private void seedPlatformScope(String username, String platform) {
        Long userId = jdbc.query("""
                SELECT id FROM app_user WHERE lower(username) = lower(?) LIMIT 1
                """, rs -> rs.next() ? rs.getLong(1) : null, username);
        if (userId == null) return;
        jdbc.update("""
                INSERT OR IGNORE INTO user_platform_scope (tenant_id, user_id, platform)
                VALUES (1, ?, ?)
                """, userId, platform);
    }
}
