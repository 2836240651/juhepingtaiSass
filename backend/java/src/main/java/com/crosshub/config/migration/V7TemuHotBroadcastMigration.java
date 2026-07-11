package com.crosshub.config.migration;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.core.annotation.Order;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

@Component
@Order(7)
public class V7TemuHotBroadcastMigration {
    private static final Logger log = LoggerFactory.getLogger(V7TemuHotBroadcastMigration.class);

    private final JdbcTemplate jdbc;

    public V7TemuHotBroadcastMigration(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    @EventListener(ApplicationReadyEvent.class)
    public void migrate() {
        jdbc.execute("""
                CREATE TABLE IF NOT EXISTS temu_hot_broadcast (
                  id TEXT PRIMARY KEY,
                  tenant_id INTEGER NOT NULL,
                  shop_id TEXT NOT NULL DEFAULT '',
                  sku TEXT NOT NULL,
                  product_name TEXT NOT NULL,
                  daily_sales INTEGER NOT NULL DEFAULT 0,
                  avg7_day_daily REAL NOT NULL DEFAULT 0,
                  surge_ratio REAL NOT NULL DEFAULT 0,
                  operator_name TEXT NOT NULL DEFAULT '',
                  source TEXT NOT NULL DEFAULT 'manual',
                  broadcast_at TEXT NOT NULL,
                  created_at TEXT NOT NULL
                )
                """);
        jdbc.execute("""
                CREATE INDEX IF NOT EXISTS idx_temu_hot_broadcast_tenant
                ON temu_hot_broadcast (tenant_id, broadcast_at DESC)
                """);
        jdbc.execute("""
                CREATE TABLE IF NOT EXISTS temu_hot_broadcast_read (
                  id TEXT PRIMARY KEY,
                  tenant_id INTEGER NOT NULL,
                  broadcast_id TEXT NOT NULL,
                  reader_id TEXT NOT NULL DEFAULT '',
                  reader_name TEXT NOT NULL,
                  read_at TEXT NOT NULL
                )
                """);
        jdbc.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_temu_hot_broadcast_read_unique
                ON temu_hot_broadcast_read (tenant_id, broadcast_id, reader_name)
                """);
        log.info("V7 Temu hot broadcast migration completed");
    }
}
