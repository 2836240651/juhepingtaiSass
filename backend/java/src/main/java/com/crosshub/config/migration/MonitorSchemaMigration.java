package com.crosshub.config.migration;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

@Component
public class MonitorSchemaMigration {
    private static final Logger log = LoggerFactory.getLogger(MonitorSchemaMigration.class);

    private final JdbcTemplate jdbc;

    public MonitorSchemaMigration(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    @EventListener(ApplicationReadyEvent.class)
    public void migrate() {
        jdbc.execute("""
                CREATE TABLE IF NOT EXISTS monitor_target (
                  id TEXT PRIMARY KEY,
                  tenant_id INTEGER NOT NULL,
                  platform TEXT NOT NULL,
                  target_type TEXT NOT NULL,
                  label TEXT NOT NULL,
                  target_url TEXT NOT NULL,
                  host TEXT NOT NULL DEFAULT '',
                  status TEXT NOT NULL DEFAULT 'active',
                  crawl_strategy TEXT NOT NULL DEFAULT '',
                  freshness_minutes INTEGER NOT NULL DEFAULT 1440,
                  latest_snapshot_id TEXT,
                  latest_snapshot_at TEXT,
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL
                )
                """);
        jdbc.execute("""
                CREATE INDEX IF NOT EXISTS idx_monitor_target_tenant_platform_status
                ON monitor_target (tenant_id, platform, status)
                """);
        jdbc.execute("""
                CREATE TABLE IF NOT EXISTS monitor_schedule (
                  id TEXT PRIMARY KEY,
                  tenant_id INTEGER NOT NULL,
                  target_id TEXT NOT NULL,
                  enabled INTEGER NOT NULL DEFAULT 1,
                  schedule_type TEXT NOT NULL DEFAULT 'interval',
                  cron_expr TEXT NOT NULL DEFAULT '',
                  interval_minutes INTEGER NOT NULL DEFAULT 1440,
                  next_run_at TEXT,
                  last_run_at TEXT,
                  max_products INTEGER NOT NULL DEFAULT 100,
                  retry_limit INTEGER NOT NULL DEFAULT 1,
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL
                )
                """);
        jdbc.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_monitor_schedule_target
                ON monitor_schedule (tenant_id, target_id)
                """);
        jdbc.execute("""
                CREATE TABLE IF NOT EXISTS monitor_job (
                  id TEXT PRIMARY KEY,
                  tenant_id INTEGER NOT NULL,
                  target_id TEXT NOT NULL,
                  schedule_id TEXT,
                  platform TEXT NOT NULL,
                  trigger_type TEXT NOT NULL,
                  force INTEGER NOT NULL DEFAULT 0,
                  status TEXT NOT NULL,
                  attempt_no INTEGER NOT NULL DEFAULT 1,
                  queued_at TEXT NOT NULL,
                  started_at TEXT,
                  finished_at TEXT,
                  worker_id TEXT,
                  error_code TEXT,
                  error_message TEXT,
                  error_detail TEXT,
                  snapshot_id TEXT,
                  created_by INTEGER,
                  reason TEXT NOT NULL DEFAULT ''
                )
                """);
        jdbc.execute("""
                CREATE INDEX IF NOT EXISTS idx_monitor_job_status_queued
                ON monitor_job (tenant_id, status, queued_at DESC)
                """);
        jdbc.execute("""
                CREATE INDEX IF NOT EXISTS idx_monitor_job_target_created
                ON monitor_job (tenant_id, target_id, queued_at DESC)
                """);
        jdbc.execute("""
                CREATE TABLE IF NOT EXISTS monitor_snapshot (
                  id TEXT PRIMARY KEY,
                  tenant_id INTEGER NOT NULL,
                  target_id TEXT NOT NULL,
                  platform TEXT NOT NULL,
                  snapshot_at TEXT NOT NULL,
                  product_count INTEGER NOT NULL DEFAULT 0,
                  recent_launch_count INTEGER NOT NULL DEFAULT 0,
                  sales_outlier_count INTEGER NOT NULL DEFAULT 0,
                  report_md_path TEXT NOT NULL DEFAULT '',
                  report_xlsx_path TEXT NOT NULL DEFAULT '',
                  created_at TEXT NOT NULL
                )
                """);
        jdbc.execute("""
                CREATE INDEX IF NOT EXISTS idx_monitor_snapshot_target_time
                ON monitor_snapshot (tenant_id, target_id, snapshot_at DESC)
                """);
        jdbc.execute("""
                CREATE TABLE IF NOT EXISTS monitor_product_snapshot (
                  id TEXT PRIMARY KEY,
                  tenant_id INTEGER NOT NULL,
                  snapshot_id TEXT NOT NULL,
                  target_id TEXT NOT NULL,
                  product_id TEXT NOT NULL,
                  product_name TEXT NOT NULL,
                  category TEXT NOT NULL DEFAULT '',
                  price REAL NOT NULL DEFAULT 0,
                  daily_sales INTEGER NOT NULL DEFAULT 0,
                  total_sales INTEGER NOT NULL DEFAULT 0,
                  listed_at TEXT NOT NULL DEFAULT '',
                  url TEXT NOT NULL DEFAULT '',
                  created_at TEXT NOT NULL
                )
                """);
        jdbc.execute("""
                CREATE TABLE IF NOT EXISTS monitor_signal (
                  id TEXT PRIMARY KEY,
                  tenant_id INTEGER NOT NULL,
                  snapshot_id TEXT NOT NULL,
                  target_id TEXT NOT NULL,
                  product_id TEXT NOT NULL,
                  signal_type TEXT NOT NULL,
                  signal_score REAL NOT NULL DEFAULT 0,
                  signal_value TEXT NOT NULL DEFAULT '',
                  created_at TEXT NOT NULL
                )
                """);
        jdbc.execute("""
                CREATE INDEX IF NOT EXISTS idx_monitor_signal_snapshot_type
                ON monitor_signal (tenant_id, snapshot_id, signal_type)
                """);
        log.info("Monitor schema migration completed");
    }
}
