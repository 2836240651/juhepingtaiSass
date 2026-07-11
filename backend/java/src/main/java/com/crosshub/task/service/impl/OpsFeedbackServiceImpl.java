package com.crosshub.task.service.impl;

import com.crosshub.security.AuthContext;
import com.crosshub.task.service.AssignedTaskService;
import com.crosshub.task.service.OpsFeedbackService;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

@Service
public class OpsFeedbackServiceImpl implements OpsFeedbackService {
    private static final DateTimeFormatter DT = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
    private static final Map<String, String> OUTCOME_LABELS = Map.of(
            "in_progress", "跟进中",
            "done", "已完成",
            "blocked", "受阻"
    );

    private final JdbcTemplate jdbc;
    private final AuthContext authContext;
    private final AssignedTaskService assignedTaskService;

    public OpsFeedbackServiceImpl(
            JdbcTemplate jdbc,
            AuthContext authContext,
            AssignedTaskService assignedTaskService
    ) {
        this.jdbc = jdbc;
        this.authContext = authContext;
        this.assignedTaskService = assignedTaskService;
    }

    @Override
    public List<Map<String, Object>> listToday() {
        Long tenantId = requireTenant();
        String today = LocalDate.now().toString();
        return jdbc.query(
                "SELECT * FROM ops_feedback WHERE tenant_id = ? AND feedback_date = ? ORDER BY submitted_at DESC",
                (rs, rowNum) -> mapRow(rs),
                tenantId,
                today
        );
    }

    @Override
    public List<Map<String, Object>> listByTaskId(String taskId) {
        Long tenantId = requireTenant();
        return jdbc.query(
                "SELECT * FROM ops_feedback WHERE tenant_id = ? AND task_id = ? ORDER BY submitted_at DESC",
                (rs, rowNum) -> mapRow(rs),
                tenantId,
                taskId
        );
    }

    @Override
    @Transactional
    public Map<String, Object> submitFeedback(Map<String, Object> payload) {
        Long tenantId = requireTenant();
        String taskId = text(payload.get("taskId"), "");
        if (taskId.isBlank()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "缺少任务 ID");
        }
        assignedTaskService.getTask(taskId);

        String outcome = text(payload.get("outcome"), "in_progress");
        String outcomeLabel = OUTCOME_LABELS.getOrDefault(outcome, "跟进中");
        String now = LocalDateTime.now().format(DT);
        String today = LocalDate.now().toString();
        String id = "fb_" + System.currentTimeMillis() + "_" + Integer.toHexString((int) (Math.random() * 0x10000));

        jdbc.update("""
                INSERT INTO ops_feedback (
                  id, tenant_id, task_id, employee_id, employee_name, employee_role,
                  platform, platform_key, task_title, category, outcome, outcome_label,
                  feedback, store_name, feedback_date, submitted_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                id,
                tenantId,
                taskId,
                text(payload.get("employeeId"), String.valueOf(authContext.userId())),
                text(payload.get("employeeName"), ""),
                text(payload.get("employeeRole"), ""),
                text(payload.get("platform"), ""),
                text(payload.get("platformKey"), ""),
                text(payload.get("taskTitle"), ""),
                text(payload.get("category"), ""),
                outcome,
                outcomeLabel,
                text(payload.get("feedback"), ""),
                text(payload.get("storeName"), "—"),
                today,
                now
        );

        String status = "done".equals(outcome) ? "已完成" : ("blocked".equals(outcome) ? "进行中" : "进行中");
        Map<String, Object> extra = new LinkedHashMap<>();
        extra.put("lastOutcome", outcome);
        extra.put("lastFeedback", text(payload.get("feedback"), ""));
        extra.put("lastFeedbackAt", now);
        extra.put("lastFeedbackBy", text(payload.get("employeeName"), text(payload.get("assigneeName"), "")));
        assignedTaskService.updateTaskStatus(taskId, status, extra);

        List<Map<String, Object>> rows = jdbc.query(
                "SELECT * FROM ops_feedback WHERE id = ?",
                (rs, rowNum) -> mapRow(rs),
                id
        );
        return rows.get(0);
    }

    private Map<String, Object> mapRow(java.sql.ResultSet rs) throws java.sql.SQLException {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("id", rs.getString("id"));
        row.put("taskId", rs.getString("task_id"));
        row.put("employeeId", rs.getString("employee_id"));
        row.put("employeeName", rs.getString("employee_name"));
        row.put("employeeRole", rs.getString("employee_role"));
        row.put("platform", rs.getString("platform"));
        row.put("platformKey", rs.getString("platform_key"));
        row.put("taskTitle", rs.getString("task_title"));
        row.put("category", rs.getString("category"));
        row.put("outcome", rs.getString("outcome"));
        row.put("outcomeLabel", rs.getString("outcome_label"));
        row.put("feedback", rs.getString("feedback"));
        row.put("storeName", rs.getString("store_name"));
        row.put("date", rs.getString("feedback_date"));
        row.put("submittedAt", rs.getString("submitted_at"));
        return row;
    }

    private Long requireTenant() {
        Long tenantId = authContext.tenantId();
        if (tenantId == null) {
            throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "未登录");
        }
        return tenantId;
    }

    private String text(Object value, String fallback) {
        if (value == null) return fallback;
        String s = String.valueOf(value).trim();
        return s.isEmpty() ? fallback : s;
    }
}
