package com.crosshub.config.migration;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.core.annotation.Order;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

@Component
@Order(2)
public class V3TemuCrawlJobMigration {
    private static final Logger log = LoggerFactory.getLogger(V3TemuCrawlJobMigration.class);

    private final JdbcTemplate jdbc;

    public V3TemuCrawlJobMigration(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    @EventListener(ApplicationReadyEvent.class)
    public void migrate() {
        jdbc.execute("""
                CREATE TABLE IF NOT EXISTS temu_crawl_job (
                  id TEXT PRIMARY KEY,
                  tenant_id INTEGER NOT NULL,
                  triggered_by INTEGER NOT NULL,
                  status TEXT NOT NULL,
                  mode TEXT NOT NULL DEFAULT 'live',
                  report_time TEXT,
                  shops_count INTEGER,
                  rows_count INTEGER,
                  error_message TEXT,
                  started_at TEXT,
                  finished_at TEXT,
                  created_at TEXT NOT NULL
                )
                """);
        jdbc.execute("""
                CREATE INDEX IF NOT EXISTS idx_temu_crawl_job_tenant_status
                ON temu_crawl_job (tenant_id, status)
                """);
        int orphans = jdbc.update("""
                UPDATE temu_crawl_job
                SET status = 'failed',
                    error_message = '服务重启中断',
                    finished_at = datetime('now', 'localtime')
                WHERE status IN ('pending', 'running')
                """);
        if (orphans > 0) {
            log.warn("Marked {} orphan temu crawl jobs as failed", orphans);
        }
        log.info("V3 temu crawl job migration completed");
    }
}
