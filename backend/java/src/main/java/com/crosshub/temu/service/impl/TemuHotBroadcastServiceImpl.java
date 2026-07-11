package com.crosshub.temu.service.impl;

import com.crosshub.security.AuthContext;
import com.crosshub.temu.service.TemuHotBroadcastService;
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
import java.util.Map;

@Service
public class TemuHotBroadcastServiceImpl implements TemuHotBroadcastService {
    private static final DateTimeFormatter DT = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

    private final JdbcTemplate jdbc;
    private final AuthContext authContext;

    public TemuHotBroadcastServiceImpl(JdbcTemplate jdbc, AuthContext authContext) {
        this.jdbc = jdbc;
        this.authContext = authContext;
    }

    @Override
    public List<Map<String, Object>> listBroadcasts() {
        Long tenantId = requireTenant();
        List<Map<String, Object>> rows = jdbc.query(
                """
                SELECT * FROM temu_hot_broadcast
                WHERE tenant_id = ?
                ORDER BY broadcast_at DESC
                LIMIT 200
                """,
                (rs, rowNum) -> mapBroadcastRow(rs),
                tenantId
        );
        Map<String, List<String>> readers = loadReadersByBroadcastId(tenantId);
        for (Map<String, Object> row : rows) {
            String id = String.valueOf(row.get("id"));
            row.put("readBy", readers.getOrDefault(id, List.of()));
        }
        return rows;
    }

    @Override
    public Map<String, Object> createBroadcast(Map<String, Object> payload) {
        Long tenantId = requireTenant();
        String sku = text(payload.get("sku"), "");
        String productName = text(payload.get("name"), text(payload.get("productName"), ""));
        if (sku.isBlank()) {
            throw badRequest("SKU 不能为空");
        }
        if (productName.isBlank()) {
            throw badRequest("商品名称不能为空");
        }

        String now = nowText();
        String id = "hot_" + System.currentTimeMillis() + "_" + Integer.toHexString((int) (Math.random() * 0x10000));
        int dailySales = intValue(payload.get("dailySales"), payload.get("daily_sales"), 0);
        double avg7 = doubleValue(payload.get("avg7DayDaily"), payload.get("avg7_day_daily"), 0);
        double surgeRatio = doubleValue(payload.get("surgeRatio"), payload.get("surge_ratio"), 1);

        jdbc.update("""
                INSERT INTO temu_hot_broadcast (
                  id, tenant_id, shop_id, sku, product_name, daily_sales, avg7_day_daily,
                  surge_ratio, operator_name, source, broadcast_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                id,
                tenantId,
                text(payload.get("shopId"), text(payload.get("shop_id"), "")),
                sku,
                productName,
                dailySales,
                avg7,
                surgeRatio,
                resolveOperatorName(payload),
                text(payload.get("source"), "manual"),
                text(payload.get("time"), now),
                now
        );

        Map<String, Object> row = findBroadcast(tenantId, id);
        row.put("readBy", List.of());
        return row;
    }

    @Override
    public Map<String, Object> markRead(String broadcastId, Map<String, Object> payload) {
        Long tenantId = requireTenant();
        Map<String, Object> broadcast = findBroadcast(tenantId, broadcastId);
        String readerName = text(payload.get("readerName"), text(payload.get("reader_name"), resolveReaderName()));
        if (readerName.isBlank()) {
            throw badRequest("缺少阅读人信息");
        }
        String readerId = text(payload.get("readerId"), text(payload.get("reader_id"), String.valueOf(authContext.userId())));

        Integer exists = jdbc.queryForObject(
                """
                SELECT COUNT(*) FROM temu_hot_broadcast_read
                WHERE tenant_id = ? AND broadcast_id = ? AND reader_name = ?
                """,
                Integer.class,
                tenantId,
                broadcastId,
                readerName
        );
        if (exists == null || exists == 0) {
            String readId = "hotread_" + System.currentTimeMillis();
            jdbc.update("""
                    INSERT INTO temu_hot_broadcast_read (
                      id, tenant_id, broadcast_id, reader_id, reader_name, read_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    readId,
                    tenantId,
                    broadcastId,
                    readerId,
                    readerName,
                    nowText()
            );
        }

        broadcast.put("readBy", loadReadersForBroadcast(tenantId, broadcastId));
        return broadcast;
    }

    private Map<String, List<String>> loadReadersByBroadcastId(Long tenantId) {
        List<Map<String, Object>> rows = jdbc.query(
                """
                SELECT broadcast_id, reader_name FROM temu_hot_broadcast_read
                WHERE tenant_id = ?
                ORDER BY read_at ASC
                """,
                (rs, rowNum) -> Map.of(
                        "broadcast_id", rs.getString("broadcast_id"),
                        "reader_name", rs.getString("reader_name")
                ),
                tenantId
        );
        Map<String, List<String>> grouped = new LinkedHashMap<>();
        for (Map<String, Object> row : rows) {
            String broadcastId = String.valueOf(row.get("broadcast_id"));
            grouped.computeIfAbsent(broadcastId, key -> new ArrayList<>())
                    .add(String.valueOf(row.get("reader_name")));
        }
        return grouped;
    }

    private List<String> loadReadersForBroadcast(Long tenantId, String broadcastId) {
        return jdbc.query(
                """
                SELECT reader_name FROM temu_hot_broadcast_read
                WHERE tenant_id = ? AND broadcast_id = ?
                ORDER BY read_at ASC
                """,
                (rs, rowNum) -> rs.getString("reader_name"),
                tenantId,
                broadcastId
        );
    }

    private Map<String, Object> findBroadcast(Long tenantId, String id) {
        List<Map<String, Object>> rows = jdbc.query(
                "SELECT * FROM temu_hot_broadcast WHERE tenant_id = ? AND id = ? LIMIT 1",
                (rs, rowNum) -> mapBroadcastRow(rs),
                tenantId,
                id
        );
        if (rows.isEmpty()) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "通报记录不存在");
        }
        return rows.get(0);
    }

    private Map<String, Object> mapBroadcastRow(ResultSet rs) throws SQLException {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("id", rs.getString("id"));
        row.put("shop_id", rs.getString("shop_id"));
        row.put("shopId", rs.getString("shop_id"));
        row.put("sku", rs.getString("sku"));
        row.put("name", rs.getString("product_name"));
        row.put("product_name", rs.getString("product_name"));
        row.put("daily_sales", rs.getInt("daily_sales"));
        row.put("dailySales", rs.getInt("daily_sales"));
        row.put("avg7_day_daily", rs.getDouble("avg7_day_daily"));
        row.put("avg7DayDaily", rs.getDouble("avg7_day_daily"));
        row.put("surge_ratio", rs.getDouble("surge_ratio"));
        row.put("surgeRatio", rs.getDouble("surge_ratio"));
        row.put("operator", rs.getString("operator_name"));
        row.put("operator_name", rs.getString("operator_name"));
        row.put("source", rs.getString("source"));
        row.put("broadcast_at", rs.getString("broadcast_at"));
        row.put("time", rs.getString("broadcast_at"));
        row.put("fromServer", "overload".equals(rs.getString("source")) || "seed".equals(rs.getString("source")));
        return row;
    }

    private String resolveOperatorName(Map<String, Object> payload) {
        String operator = text(payload.get("operator"), text(payload.get("operatorName"), ""));
        if (!operator.isBlank()) return operator;
        return resolveReaderName();
    }

    private String resolveReaderName() {
        if (authContext.isBossPortal() || authContext.isAdmin()) {
            return "企业管理员";
        }
        return "运营人员";
    }

    private Long requireTenant() {
        Long tenantId = authContext.tenantId();
        if (tenantId == null) {
            throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "缺少租户上下文");
        }
        return tenantId;
    }

    private String text(Object value, String fallback) {
        if (value == null) return fallback;
        return String.valueOf(value).trim();
    }

    private int intValue(Object primary, Object secondary, int fallback) {
        Number number = asNumber(primary);
        if (number == null) number = asNumber(secondary);
        return number == null ? fallback : number.intValue();
    }

    private double doubleValue(Object primary, Object secondary, double fallback) {
        Number number = asNumber(primary);
        if (number == null) number = asNumber(secondary);
        return number == null ? fallback : number.doubleValue();
    }

    private Number asNumber(Object value) {
        if (value == null) return null;
        if (value instanceof Number number) return number;
        try {
            return Double.parseDouble(String.valueOf(value));
        } catch (NumberFormatException ex) {
            return null;
        }
    }

    private String nowText() {
        return DT.format(LocalDateTime.now());
    }

    private ResponseStatusException badRequest(String message) {
        return new ResponseStatusException(HttpStatus.BAD_REQUEST, message);
    }
}
