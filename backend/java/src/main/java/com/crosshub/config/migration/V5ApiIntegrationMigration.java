package com.crosshub.config.migration;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.core.annotation.Order;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

@Component
@Order(5)
public class V5ApiIntegrationMigration {
    private static final Logger log = LoggerFactory.getLogger(V5ApiIntegrationMigration.class);

    private final JdbcTemplate jdbc;

    public V5ApiIntegrationMigration(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    @EventListener(ApplicationReadyEvent.class)
    public void migrate() {
        addColumnIfMissing("platform_account", "external_shop_id", "TEXT NOT NULL DEFAULT ''");
        addColumnIfMissing("warehouse_order", "source_order_ref", "TEXT NOT NULL DEFAULT ''");
        addColumnIfMissing("warehouse_order", "from_platform_order", "INTEGER NOT NULL DEFAULT 0");
        createAssignedTaskTable();
        createOpsFeedbackTable();
        jdbc.execute("""
                CREATE INDEX IF NOT EXISTS idx_platform_account_external_shop
                ON platform_account (tenant_id, platform, external_shop_id)
                """);
        log.info("V5 API integration migration completed");
    }

    private void createAssignedTaskTable() {
        jdbc.execute("""
                CREATE TABLE IF NOT EXISTS assigned_task (
                  id TEXT PRIMARY KEY,
                  tenant_id INTEGER NOT NULL,
                  assignee_type TEXT NOT NULL DEFAULT 'employee',
                  assignee_id TEXT NOT NULL,
                  assignee_name TEXT NOT NULL DEFAULT '',
                  title TEXT NOT NULL,
                  description TEXT NOT NULL DEFAULT '',
                  platform_key TEXT NOT NULL DEFAULT 'temu',
                  category TEXT NOT NULL DEFAULT '',
                  priority TEXT NOT NULL DEFAULT 'medium',
                  status TEXT NOT NULL DEFAULT '待处理',
                  progress INTEGER NOT NULL DEFAULT 0,
                  due_text TEXT NOT NULL DEFAULT '',
                  warehouse_name TEXT NOT NULL DEFAULT '',
                  assigned_by TEXT NOT NULL DEFAULT '',
                  assigned_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL,
                  last_outcome TEXT NOT NULL DEFAULT '',
                  last_feedback TEXT NOT NULL DEFAULT '',
                  last_feedback_at TEXT NOT NULL DEFAULT '',
                  last_feedback_by TEXT NOT NULL DEFAULT ''
                )
                """);
        jdbc.execute("""
                CREATE INDEX IF NOT EXISTS idx_assigned_task_tenant
                ON assigned_task (tenant_id, assigned_at DESC)
                """);
        jdbc.execute("""
                CREATE INDEX IF NOT EXISTS idx_assigned_task_assignee
                ON assigned_task (tenant_id, assignee_type, assignee_id)
                """);
    }

    private void createOpsFeedbackTable() {
        jdbc.execute("""
                CREATE TABLE IF NOT EXISTS ops_feedback (
                  id TEXT PRIMARY KEY,
                  tenant_id INTEGER NOT NULL,
                  task_id TEXT NOT NULL,
                  employee_id TEXT NOT NULL DEFAULT '',
                  employee_name TEXT NOT NULL DEFAULT '',
                  employee_role TEXT NOT NULL DEFAULT '',
                  platform TEXT NOT NULL DEFAULT '',
                  platform_key TEXT NOT NULL DEFAULT '',
                  task_title TEXT NOT NULL DEFAULT '',
                  category TEXT NOT NULL DEFAULT '',
                  outcome TEXT NOT NULL DEFAULT 'in_progress',
                  outcome_label TEXT NOT NULL DEFAULT '',
                  feedback TEXT NOT NULL DEFAULT '',
                  store_name TEXT NOT NULL DEFAULT '',
                  feedback_date TEXT NOT NULL,
                  submitted_at TEXT NOT NULL
                )
                """);
        jdbc.execute("""
                CREATE INDEX IF NOT EXISTS idx_ops_feedback_tenant_date
                ON ops_feedback (tenant_id, feedback_date DESC)
                """);
        jdbc.execute("""
                CREATE INDEX IF NOT EXISTS idx_ops_feedback_task
                ON ops_feedback (tenant_id, task_id)
                """);
    }

    private void addColumnIfMissing(String table, String column, String definition) {
        Integer count = jdbc.queryForObject(
                "SELECT COUNT(*) FROM pragma_table_info(?) WHERE name = ?",
                Integer.class,
                table,
                column
        );
        if (count == null || count == 0) {
            jdbc.execute("ALTER TABLE " + table + " ADD COLUMN " + column + " " + definition);
        }
    }
}
