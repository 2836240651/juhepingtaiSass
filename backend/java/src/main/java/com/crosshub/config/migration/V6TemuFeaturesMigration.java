package com.crosshub.config.migration;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.core.annotation.Order;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

@Component
@Order(6)
public class V6TemuFeaturesMigration {
    private static final Logger log = LoggerFactory.getLogger(V6TemuFeaturesMigration.class);

    private final JdbcTemplate jdbc;

    public V6TemuFeaturesMigration(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    @EventListener(ApplicationReadyEvent.class)
    public void migrate() {
        jdbc.execute("""
                CREATE TABLE IF NOT EXISTS temu_restock_status (
                  id TEXT PRIMARY KEY,
                  tenant_id INTEGER NOT NULL,
                  shop_id TEXT NOT NULL DEFAULT '',
                  sku TEXT NOT NULL,
                  status TEXT NOT NULL DEFAULT 'pending',
                  note TEXT NOT NULL DEFAULT '',
                  updated_at TEXT NOT NULL,
                  updated_by TEXT NOT NULL DEFAULT ''
                )
                """);
        jdbc.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_temu_restock_tenant_shop_sku
                ON temu_restock_status (tenant_id, shop_id, sku)
                """);
        jdbc.execute("""
                CREATE INDEX IF NOT EXISTS idx_temu_restock_tenant
                ON temu_restock_status (tenant_id, updated_at DESC)
                """);
        log.info("V6 Temu features migration completed");
    }
}
