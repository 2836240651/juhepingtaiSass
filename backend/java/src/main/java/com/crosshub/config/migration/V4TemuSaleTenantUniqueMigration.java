package com.crosshub.config.migration;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.core.annotation.Order;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

@Component
@Order(3)
public class V4TemuSaleTenantUniqueMigration {
    private static final Logger log = LoggerFactory.getLogger(V4TemuSaleTenantUniqueMigration.class);

    private final JdbcTemplate jdbc;

    public V4TemuSaleTenantUniqueMigration(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    @EventListener(ApplicationReadyEvent.class)
    public void migrate() {
        String ddl = jdbc.query("""
                SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'temu_sale'
                """, rs -> rs.next() ? rs.getString(1) : null);
        if (ddl == null) {
            return;
        }
        if (ddl.contains("UNIQUE (tenant_id, report_time, shop_id, ext_code)")) {
            log.info("V4 temu_sale tenant unique already applied");
            return;
        }

        log.info("Rebuilding temu_sale with tenant-scoped unique constraint");
        jdbc.execute("""
                CREATE TABLE IF NOT EXISTS temu_sale_v4 (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  platform TEXT NOT NULL DEFAULT 'temu',
                  status TEXT NOT NULL DEFAULT '300',
                  report_time TEXT NOT NULL,
                  shop_name TEXT NOT NULL,
                  shop_id TEXT NOT NULL,
                  tenant_id INTEGER NOT NULL DEFAULT 1,
                  user_id INTEGER NOT NULL DEFAULT 1,
                  cost INTEGER NOT NULL DEFAULT 0,
                  category_name TEXT NOT NULL DEFAULT '',
                  img_url TEXT NOT NULL DEFAULT '',
                  title TEXT NOT NULL,
                  skc TEXT NOT NULL DEFAULT '',
                  spu TEXT NOT NULL DEFAULT '',
                  ext_code TEXT NOT NULL,
                  son_sku TEXT NOT NULL DEFAULT '',
                  son_price INTEGER NOT NULL DEFAULT 0,
                  son_today_sales INTEGER NOT NULL DEFAULT 0,
                  son_sales_seven_days INTEGER NOT NULL DEFAULT 0,
                  son_sales_thirty_days INTEGER NOT NULL DEFAULT 0,
                  join_site_time INTEGER NOT NULL DEFAULT 0,
                  warehouse_available_stock INTEGER NOT NULL DEFAULT 0,
                  nickname TEXT NOT NULL DEFAULT '',
                  username TEXT NOT NULL DEFAULT '',
                  enterprise TEXT NOT NULL DEFAULT '',
                  UNIQUE (tenant_id, report_time, shop_id, ext_code)
                )
                """);
        jdbc.execute("""
                INSERT OR IGNORE INTO temu_sale_v4 (
                  id, platform, status, report_time, shop_name, shop_id, tenant_id, user_id,
                  cost, category_name, img_url, title, skc, spu, ext_code, son_sku, son_price,
                  son_today_sales, son_sales_seven_days, son_sales_thirty_days, join_site_time,
                  warehouse_available_stock, nickname, username, enterprise
                )
                SELECT
                  id, platform, status, report_time, shop_name, shop_id, tenant_id, user_id,
                  cost, category_name, img_url, title, skc, spu, ext_code, son_sku, son_price,
                  son_today_sales, son_sales_seven_days, son_sales_thirty_days, join_site_time,
                  warehouse_available_stock, nickname, username, enterprise
                FROM temu_sale
                """);
        jdbc.execute("DROP TABLE temu_sale");
        jdbc.execute("ALTER TABLE temu_sale_v4 RENAME TO temu_sale");
        jdbc.execute("""
                CREATE INDEX IF NOT EXISTS idx_temu_sale_tenant_report
                ON temu_sale (tenant_id, report_time)
                """);
        log.info("V4 temu_sale tenant unique migration completed");
    }
}
