package com.crosshub.temu.service.impl;

import com.crosshub.security.AuthContext;
import com.crosshub.temu.service.TemuRestockStatusService;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;

@Service
public class TemuRestockStatusServiceImpl implements TemuRestockStatusService {
    private static final DateTimeFormatter DT = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
    private static final Set<String> VALID_STATUS = Set.of("pending", "in_progress", "done");

    private final JdbcTemplate jdbc;
    private final AuthContext authContext;

    public TemuRestockStatusServiceImpl(JdbcTemplate jdbc, AuthContext authContext) {
        this.jdbc = jdbc;
        this.authContext = authContext;
    }

    @Override
    public List<Map<String, Object>> listAll() {
        Long tenantId = requireTenant();
        return jdbc.query(
                "SELECT * FROM temu_restock_status WHERE tenant_id = ? ORDER BY updated_at DESC",
                (rs, rowNum) -> mapRow(rs),
                tenantId
        );
    }

    @Override
    public Map<String, Object> upsert(Map<String, Object> payload) {
        Long tenantId = requireTenant();
        String sku = text(payload.get("sku"), "");
        if (sku.isBlank()) {
            throw badRequest("SKU 不能为空");
        }
        String shopId = text(payload.get("shopId"), text(payload.get("shop_id"), ""));
        String status = normalizeStatus(text(payload.get("status"), "pending"));
        String note = text(payload.get("note"), "");
        String updatedBy = resolveActorName();
        String now = nowText();

        String existingId = jdbc.query(
                "SELECT id FROM temu_restock_status WHERE tenant_id = ? AND shop_id = ? AND sku = ? LIMIT 1",
                rs -> rs.next() ? rs.getString("id") : null,
                tenantId,
                shopId,
                sku
        );

        if (existingId == null) {
            String id = "restock_" + System.currentTimeMillis() + "_" + Integer.toHexString((int) (Math.random() * 0x10000));
            jdbc.update("""
                    INSERT INTO temu_restock_status (
                      id, tenant_id, shop_id, sku, status, note, updated_at, updated_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    id,
                    tenantId,
                    shopId,
                    sku,
                    status,
                    note,
                    now,
                    updatedBy
            );
            return findByKey(tenantId, shopId, sku);
        }

        jdbc.update("""
                UPDATE temu_restock_status
                SET status = ?, note = ?, updated_at = ?, updated_by = ?
                WHERE id = ? AND tenant_id = ?
                """,
                status,
                note,
                now,
                updatedBy,
                existingId,
                tenantId
        );
        return findByKey(tenantId, shopId, sku);
    }

    private Map<String, Object> findByKey(Long tenantId, String shopId, String sku) {
        List<Map<String, Object>> rows = jdbc.query(
                "SELECT * FROM temu_restock_status WHERE tenant_id = ? AND shop_id = ? AND sku = ? LIMIT 1",
                (rs, rowNum) -> mapRow(rs),
                tenantId,
                shopId,
                sku
        );
        if (rows.isEmpty()) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "备货状态不存在");
        }
        return rows.get(0);
    }

    private Map<String, Object> mapRow(ResultSet rs) throws SQLException {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("id", rs.getString("id"));
        row.put("shop_id", rs.getString("shop_id"));
        row.put("shopId", rs.getString("shop_id"));
        row.put("sku", rs.getString("sku"));
        row.put("status", rs.getString("status"));
        row.put("note", rs.getString("note"));
        row.put("updated_at", rs.getString("updated_at"));
        row.put("updatedAt", rs.getString("updated_at"));
        row.put("updated_by", rs.getString("updated_by"));
        row.put("updatedBy", rs.getString("updated_by"));
        return row;
    }

    private String normalizeStatus(String status) {
        String key = status.trim().toLowerCase(Locale.ROOT);
        if (!VALID_STATUS.contains(key)) {
            throw badRequest("无效的备货状态");
        }
        return key;
    }

    private Long requireTenant() {
        Long tenantId = authContext.tenantId();
        if (tenantId == null) {
            throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "缺少租户上下文");
        }
        return tenantId;
    }

    private String resolveActorName() {
        if (authContext.isBossPortal() || authContext.isAdmin()) {
            return "企业管理员";
        }
        return "运营人员";
    }

    private String text(Object value, String fallback) {
        if (value == null) return fallback;
        return String.valueOf(value).trim();
    }

    private String nowText() {
        return DT.format(LocalDateTime.now());
    }

    private ResponseStatusException badRequest(String message) {
        return new ResponseStatusException(HttpStatus.BAD_REQUEST, message);
    }
}
