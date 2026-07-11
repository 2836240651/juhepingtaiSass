package com.crosshub.aliexpress.service.impl;

import com.crosshub.aliexpress.entity.AliExpressOrder;
import com.crosshub.aliexpress.entity.AliExpressProduct;
import com.crosshub.aliexpress.entity.AliExpressViolation;
import com.crosshub.aliexpress.repository.AliExpressOrderRepository;
import com.crosshub.aliexpress.repository.AliExpressProductRepository;
import com.crosshub.aliexpress.repository.AliExpressViolationRepository;
import com.crosshub.aliexpress.service.AliExpressOperationalService;
import com.crosshub.tenant.service.DataScopeService;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Service
public class AliExpressOperationalServiceImpl implements AliExpressOperationalService {
    private final JdbcTemplate jdbcTemplate;
    private final AliExpressProductRepository productRepository;
    private final AliExpressOrderRepository orderRepository;
    private final AliExpressViolationRepository violationRepository;
    private final DataScopeService dataScopeService;

    public AliExpressOperationalServiceImpl(
            JdbcTemplate jdbcTemplate,
            AliExpressProductRepository productRepository,
            AliExpressOrderRepository orderRepository,
            AliExpressViolationRepository violationRepository,
            DataScopeService dataScopeService
    ) {
        this.jdbcTemplate = jdbcTemplate;
        this.productRepository = productRepository;
        this.orderRepository = orderRepository;
        this.violationRepository = violationRepository;
        this.dataScopeService = dataScopeService;
    }

    @Override
    public Map<String, Object> operational(String storeId) {
        Long tenantId = requireTenantId();
        String reportDay = latestReportDay(tenantId);
        List<AliExpressProduct> rows = reportDay.isBlank()
                ? List.of()
                : (isBlank(storeId)
                ? productRepository.findByTenantIdAndReportDayOrderByDailySalesDesc(tenantId, reportDay)
                : productRepository.findByTenantIdAndReportDayAndStoreIdOrderByDailySalesDesc(tenantId, reportDay, storeId));
        List<Map<String, Object>> products = new ArrayList<>();
        for (AliExpressProduct row : rows) {
            Map<String, Object> item = new LinkedHashMap<>();
            item.put("id", row.getId());
            item.put("store_id", row.getStoreId());
            item.put("store_name", row.getStoreName());
            item.put("sku", row.getSku());
            item.put("name", row.getName());
            item.put("category", row.getCategory());
            item.put("selling_price", row.getSellingPrice());
            item.put("cost_price", row.getCostPrice());
            item.put("platform_fee_rate", row.getPlatformFeeRate());
            item.put("logistics_fee", row.getLogisticsFee());
            item.put("official_stock", row.getOfficialStock());
            item.put("local_stock", row.getLocalStock());
            item.put("days_without_sale", row.getDaysWithoutSale());
            item.put("daily_sales", row.getDailySales());
            item.put("sales_last7_days", row.getSalesLast7Days());
            item.put("owner", row.getOwner());
            products.add(item);
        }
        return Map.of(
                "products", products,
                "broadcasts", List.of(),
                "report_day", reportDay
        );
    }

    @Override
    public Map<String, Object> todayOrders(String storeId) {
        Long tenantId = requireTenantId();
        String reportDay = latestOrderDay(tenantId);
        List<AliExpressOrder> rows = reportDay.isBlank()
                ? List.of()
                : (isBlank(storeId)
                ? orderRepository.findByTenantIdAndReportDayOrderByOrderedAtDesc(tenantId, reportDay)
                : orderRepository.findByTenantIdAndReportDayAndStoreIdOrderByOrderedAtDesc(tenantId, reportDay, storeId));
        List<Map<String, Object>> orders = new ArrayList<>();
        for (AliExpressOrder row : rows) {
            Map<String, Object> item = new LinkedHashMap<>();
            item.put("id", row.getId());
            item.put("storeId", row.getStoreId());
            item.put("storeName", row.getStoreName());
            item.put("orderNo", row.getOrderNo());
            item.put("fulfillmentType", row.getFulfillmentType());
            item.put("sku", row.getSku());
            item.put("productName", row.getProductName());
            item.put("quantity", row.getQuantity());
            item.put("amount", row.getAmount());
            item.put("currency", row.getCurrency());
            item.put("country", row.getCountry());
            item.put("status", row.getStatus());
            item.put("orderedAt", row.getOrderedAt());
            item.put("shipDeadline", row.getShipDeadline());
            item.put("warehouseName", row.getWarehouseName());
            orders.add(item);
        }
        return Map.of("orders", orders, "syncedAt", reportDay, "date", reportDay);
    }

    @Override
    public Map<String, Object> violations(String storeId) {
        Long tenantId = requireTenantId();
        List<AliExpressViolation> rows = isBlank(storeId)
                ? violationRepository.findByTenantIdOrderByViolatedAtDesc(tenantId)
                : violationRepository.findByTenantIdAndStoreIdOrderByViolatedAtDesc(tenantId, storeId);
        List<Map<String, Object>> violations = new ArrayList<>();
        String syncedAt = "";
        for (AliExpressViolation row : rows) {
            Map<String, Object> item = new LinkedHashMap<>();
            item.put("id", row.getId());
            item.put("storeId", row.getStoreId());
            item.put("storeName", row.getStoreName());
            item.put("typeCode", row.getTypeCode());
            item.put("typeLabel", row.getTypeLabel());
            item.put("orderNo", row.getOrderNo());
            item.put("description", row.getDescription());
            item.put("fineAmount", row.getFineAmount());
            item.put("currency", row.getCurrency());
            item.put("violatedAt", row.getViolatedAt());
            item.put("appealStatus", row.getAppealStatus());
            item.put("appealResult", row.getAppealResult());
            item.put("confirmed", row.getConfirmed());
            item.put("severity", row.getSeverity());
            item.put("owner", row.getOwner());
            violations.add(item);
            if (syncedAt.isBlank() || syncedAt.compareTo(row.getViolatedAt()) < 0) {
                syncedAt = row.getViolatedAt();
            }
        }
        return Map.of("violations", violations, "syncedAt", syncedAt);
    }

    private Long requireTenantId() {
        return dataScopeService.requireTenantId();
    }

    private String latestReportDay(Long tenantId) {
        return latestText(
                "SELECT report_day FROM aliexpress_product WHERE tenant_id=? ORDER BY report_day DESC LIMIT 1",
                tenantId
        );
    }

    private String latestOrderDay(Long tenantId) {
        return latestText(
                "SELECT report_day FROM aliexpress_order WHERE tenant_id=? ORDER BY report_day DESC LIMIT 1",
                tenantId
        );
    }

    private String latestText(String sql, Long tenantId) {
        List<String> rows = jdbcTemplate.query(sql, (rs, rn) -> rs.getString(1), tenantId);
        return rows.isEmpty() ? "" : rows.get(0);
    }

    private boolean isBlank(String value) {
        return value == null || value.isBlank() || "all".equalsIgnoreCase(value);
    }
}

