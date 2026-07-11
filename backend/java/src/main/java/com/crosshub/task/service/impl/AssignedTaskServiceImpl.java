package com.crosshub.task.service.impl;

import com.crosshub.security.AuthContext;
import com.crosshub.task.service.AssignedTaskService;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;

@Service
public class AssignedTaskServiceImpl implements AssignedTaskService {
    private static final DateTimeFormatter DT = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
    private static final Set<String> VALID_STATUS = Set.of("待处理", "进行中", "已完成", "已取消");

    private final JdbcTemplate jdbc;
    private final AuthContext authContext;

    public AssignedTaskServiceImpl(JdbcTemplate jdbc, AuthContext authContext) {
        this.jdbc = jdbc;
        this.authContext = authContext;
    }

    @Override
    public List<Map<String, Object>> listTasks(String status, String platformKey, boolean activeOnly) {
        Long tenantId = requireTenant();
        String portal = authContext.portalRole();
        Long userId = authContext.userId();

        StringBuilder sql = new StringBuilder("SELECT * FROM assigned_task WHERE tenant_id = ?");
        List<Object> args = new ArrayList<>();
        args.add(tenantId);

        if ("employee".equalsIgnoreCase(portal)) {
            sql.append(" AND assignee_type = 'employee' AND assignee_id = ?");
            args.add(String.valueOf(userId));
        } else if ("warehouse".equalsIgnoreCase(portal)) {
            sql.append(" AND assignee_type = 'warehouse' AND assignee_id = ?");
            args.add(String.valueOf(userId));
        }

        if (status != null && !status.isBlank()) {
            sql.append(" AND status = ?");
            args.add(status.trim());
        }
        if (platformKey != null && !platformKey.isBlank()) {
            sql.append(" AND platform_key = ?");
            args.add(platformKey.trim().toLowerCase(Locale.ROOT));
        }
        if (activeOnly) {
            sql.append(" AND status NOT IN ('已完成', '已取消')");
        }

        sql.append(" ORDER BY assigned_at DESC");
        return jdbc.query(sql.toString(), (rs, rowNum) -> mapRow(rs), args.toArray());
    }

    @Override
    public Map<String, Object> getTask(String id) {
        Map<String, Object> task = findTask(requireTenant(), id);
        assertReadable(task);
        return task;
    }

    @Override
    public Map<String, Object> createTask(Map<String, Object> payload) {
        requireBossPortal();
        Long tenantId = requireTenant();
        String title = text(payload.get("title"), "");
        if (title.isBlank()) {
            throw badRequest("请填写任务标题");
        }
        String assigneeType = text(payload.get("assigneeType"), "employee");
        String assigneeId = text(payload.get("assigneeId"), text(payload.get("employeeId"), ""));
        if (assigneeId.isBlank()) {
            throw badRequest("请选择负责人");
        }
        String now = nowText();
        String id = "assign_" + System.currentTimeMillis() + "_" + Integer.toHexString((int) (Math.random() * 0x10000));

        jdbc.update("""
                INSERT INTO assigned_task (
                  id, tenant_id, assignee_type, assignee_id, assignee_name, title, description,
                  platform_key, category, priority, status, progress, due_text, warehouse_name,
                  assigned_by, assigned_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                id,
                tenantId,
                assigneeType,
                assigneeId,
                text(payload.get("assignee"), text(payload.get("assigneeName"), "")),
                title,
                text(payload.get("description"), ""),
                text(payload.get("platformKey"), "temu").toLowerCase(Locale.ROOT),
                text(payload.get("category"), assigneeType.equals("warehouse") ? "出库" : "运营"),
                text(payload.get("priority"), "medium"),
                "待处理",
                0,
                text(payload.get("due"), text(payload.get("dueText"), "今天 18:00")),
                text(payload.get("warehouseName"), ""),
                text(payload.get("assignedBy"), resolveBossName()),
                now,
                now
        );
        return findTask(tenantId, id);
    }

    @Override
    public Map<String, Object> updateTask(String id, Map<String, Object> payload) {
        requireBossPortal();
        Long tenantId = requireTenant();
        Map<String, Object> existing = findTask(tenantId, id);
        jdbc.update("""
                UPDATE assigned_task SET
                  title = ?, description = ?, platform_key = ?, category = ?, priority = ?,
                  due_text = ?, warehouse_name = ?, updated_at = ?
                WHERE tenant_id = ? AND id = ?
                """,
                text(payload.get("title"), text(existing.get("title"), "")),
                text(payload.get("description"), text(existing.get("description"), "")),
                text(payload.get("platformKey"), text(existing.get("platformKey"), "temu")),
                text(payload.get("category"), text(existing.get("category"), "")),
                text(payload.get("priority"), text(existing.get("priority"), "medium")),
                text(payload.get("due"), text(existing.get("due"), "")),
                text(payload.get("warehouseName"), text(existing.get("warehouseName"), "")),
                nowText(),
                tenantId,
                id
        );
        return findTask(tenantId, id);
    }

    @Override
    public Map<String, Object> updateTaskStatus(String id, String status, Map<String, Object> extra) {
        Long tenantId = requireTenant();
        Map<String, Object> existing = findTask(tenantId, id);
        assertWritable(existing);
        String normalized = normalizeStatus(status);
        jdbc.update("""
                UPDATE assigned_task SET
                  status = ?, progress = ?, last_outcome = ?, last_feedback = ?,
                  last_feedback_at = ?, last_feedback_by = ?, updated_at = ?
                WHERE tenant_id = ? AND id = ?
                """,
                normalized,
                extra != null && extra.get("progress") instanceof Number n ? n.intValue() : existing.get("progress"),
                text(extra == null ? null : extra.get("lastOutcome"), text(existing.get("lastOutcome"), "")),
                text(extra == null ? null : extra.get("lastFeedback"), text(existing.get("lastFeedback"), "")),
                text(extra == null ? null : extra.get("lastFeedbackAt"), text(existing.get("lastFeedbackAt"), "")),
                text(extra == null ? null : extra.get("lastFeedbackBy"), text(existing.get("lastFeedbackBy"), "")),
                nowText(),
                tenantId,
                id
        );
        return findTask(tenantId, id);
    }

    @Override
    public void deleteTask(String id) {
        requireBossPortal();
        Long tenantId = requireTenant();
        findTask(tenantId, id);
        jdbc.update("DELETE FROM assigned_task WHERE tenant_id = ? AND id = ?", tenantId, id);
    }

    private Map<String, Object> findTask(Long tenantId, String id) {
        List<Map<String, Object>> rows = jdbc.query(
                "SELECT * FROM assigned_task WHERE tenant_id = ? AND id = ? LIMIT 1",
                (rs, rowNum) -> mapRow(rs),
                tenantId,
                id
        );
        if (rows.isEmpty()) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "任务不存在");
        }
        return rows.get(0);
    }

    private Map<String, Object> mapRow(java.sql.ResultSet rs) throws java.sql.SQLException {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("id", rs.getString("id"));
        row.put("assigneeType", rs.getString("assignee_type"));
        row.put("assigneeId", rs.getString("assignee_id"));
        row.put("employeeId", rs.getString("assignee_id"));
        row.put("assignee", rs.getString("assignee_name"));
        row.put("title", rs.getString("title"));
        row.put("description", rs.getString("description"));
        row.put("platformKey", rs.getString("platform_key"));
        row.put("category", rs.getString("category"));
        row.put("priority", rs.getString("priority"));
        row.put("status", rs.getString("status"));
        row.put("progress", rs.getInt("progress"));
        row.put("due", rs.getString("due_text"));
        row.put("warehouseName", rs.getString("warehouse_name"));
        row.put("assignedBy", rs.getString("assigned_by"));
        row.put("assignedAt", rs.getString("assigned_at"));
        row.put("updatedAt", rs.getString("updated_at"));
        row.put("lastOutcome", rs.getString("last_outcome"));
        row.put("lastFeedback", rs.getString("last_feedback"));
        row.put("lastFeedbackAt", rs.getString("last_feedback_at"));
        row.put("lastFeedbackBy", rs.getString("last_feedback_by"));
        return row;
    }

    private void assertReadable(Map<String, Object> task) {
        String portal = authContext.portalRole();
        if ("boss".equalsIgnoreCase(portal) || authContext.isAdmin()) {
            return;
        }
        String owner = String.valueOf(task.get("assigneeId"));
        if (!String.valueOf(authContext.userId()).equals(owner)) {
            throw new ResponseStatusException(HttpStatus.FORBIDDEN, "无权查看该任务");
        }
    }

    private void assertWritable(Map<String, Object> task) {
        String portal = authContext.portalRole();
        if ("boss".equalsIgnoreCase(portal) || authContext.isAdmin()) {
            return;
        }
        assertReadable(task);
    }

    private void requireBossPortal() {
        if (!authContext.isBossPortal() && !authContext.isAdmin()) {
            throw new ResponseStatusException(HttpStatus.FORBIDDEN, "仅企业管理员可管理任务");
        }
    }

    private Long requireTenant() {
        Long tenantId = authContext.tenantId();
        if (tenantId == null) {
            throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "未登录");
        }
        return tenantId;
    }

    private String resolveBossName() {
        Long userId = authContext.userId();
        if (userId == null) return "企业管理员";
        return jdbc.query(
                "SELECT nickname FROM app_user WHERE id = ? LIMIT 1",
                rs -> rs.next() ? rs.getString(1) : "企业管理员",
                userId
        );
    }

    private String normalizeStatus(String status) {
        if (status == null || status.isBlank()) return "待处理";
        return VALID_STATUS.contains(status) ? status : "待处理";
    }

    private String nowText() {
        return LocalDateTime.now().format(DT);
    }

    private String text(Object value, String fallback) {
        if (value == null) return fallback;
        return String.valueOf(value).trim();
    }

    private ResponseStatusException badRequest(String message) {
        return new ResponseStatusException(HttpStatus.BAD_REQUEST, message);
    }
}
