package com.crosshub.config.migration;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.core.annotation.Order;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

@Component
@Order(1)
public class V2TenantConstraintsMigration {
    private static final Logger log = LoggerFactory.getLogger(V2TenantConstraintsMigration.class);

    private final JdbcTemplate jdbc;

    public V2TenantConstraintsMigration(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    @EventListener(ApplicationReadyEvent.class)
    public void migrate() {
        createPlatformAccountTable();
        ensureTenantScopedUserIndex();
        ensureTenantScopedShopIndex();
        log.info("V2 tenant constraints migration completed");
    }

    private void createPlatformAccountTable() {
        jdbc.execute("""
                CREATE TABLE IF NOT EXISTS platform_account (
                  id TEXT PRIMARY KEY,
                  tenant_id INTEGER NOT NULL,
                  platform TEXT NOT NULL,
                  store_name TEXT NOT NULL,
                  account TEXT NOT NULL,
                  password TEXT NOT NULL DEFAULT '',
                  company_name TEXT NOT NULL DEFAULT '',
                  bound_at TEXT NOT NULL DEFAULT '',
                  UNIQUE (tenant_id, platform, store_name)
                )
                """);
        jdbc.execute("""
                CREATE INDEX IF NOT EXISTS idx_platform_account_tenant
                ON platform_account (tenant_id)
                """);
    }

    private void ensureTenantScopedUserIndex() {
        if (!indexExists("idx_app_user_tenant_username")) {
            jdbc.execute("""
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_app_user_tenant_username
                    ON app_user (tenant_id, lower(username))
                    """);
        }
    }

    private void ensureTenantScopedShopIndex() {
        if (!indexExists("idx_temu_shop_tenant_shop")) {
            jdbc.execute("""
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_temu_shop_tenant_shop
                    ON temu_shop (tenant_id, shop_id)
                    """);
        }
    }

    private boolean indexExists(String name) {
        Integer count = jdbc.queryForObject(
                "SELECT COUNT(*) FROM sqlite_master WHERE type = 'index' AND name = ?",
                Integer.class,
                name
        );
        return count != null && count > 0;
    }
}
