package com.crosshub.amazon.service.impl;

import com.crosshub.amazon.entity.*;
import com.crosshub.amazon.repository.*;
import com.crosshub.amazon.service.AmazonOperationalPersistenceService;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;

@Service
public class AmazonOperationalPersistenceServiceImpl implements AmazonOperationalPersistenceService {
    private static final DateTimeFormatter TS = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

    private final AmazonProductSnapshotRepository productSnapshotRepository;
    private final AmazonAccountMetricRepository accountMetricRepository;
    private final AmazonOperationalItemRepository operationalItemRepository;
    private final ObjectMapper objectMapper;

    public AmazonOperationalPersistenceServiceImpl(
            AmazonProductSnapshotRepository productSnapshotRepository,
            AmazonAccountMetricRepository accountMetricRepository,
            AmazonOperationalItemRepository operationalItemRepository,
            ObjectMapper objectMapper
    ) {
        this.productSnapshotRepository = productSnapshotRepository;
        this.accountMetricRepository = accountMetricRepository;
        this.operationalItemRepository = operationalItemRepository;
        this.objectMapper = objectMapper;
    }

    @Transactional
    public void persistSyncResult(AmazonSyncJob job, Map<String, Object> result) {
        Long tenantId = job.getTenantId();
        String accountId = job.getPlatformAccountId();
        String syncedAt = text(result.get("synced_at"));
        if (syncedAt.isBlank()) syncedAt = LocalDateTime.now().format(TS);

        List<Map<String, Object>> metrics = rows(result.get("account_metrics"));
        if (!metrics.isEmpty()) {
            accountMetricRepository.deleteByTenantIdAndPlatformAccountId(tenantId, accountId);
            for (Map<String, Object> row : metrics) {
                AmazonAccountMetric m = new AmazonAccountMetric();
                m.setId(textOr(row.get("id"), "metric_" + UUID.randomUUID()));
                m.setTenantId(tenantId);
                m.setPlatformAccountId(accountId);
                m.setMetricKey(text(row.get("metric_key")));
                m.setMetricLabel(textOr(row.get("metric_label"), text(row.get("label"))));
                m.setStatus(textOr(row.get("status"), "normal"));
                m.setValueText(textOr(row.get("value_text"), text(row.get("value"))));
                m.setThresholdText(textOr(row.get("threshold_text"), text(row.get("threshold"))));
                m.setTrend(textOr(row.get("trend"), "stable"));
                m.setNoteText(textOr(row.get("note_text"), text(row.get("note"))));
                m.setSyncedAt(textOr(row.get("synced_at"), syncedAt));
                accountMetricRepository.save(m);
            }
        }

        List<Map<String, Object>> products = rows(result.get("products"));
        if (!products.isEmpty()) {
            productSnapshotRepository.deleteByTenantIdAndPlatformAccountId(tenantId, accountId);
            for (Map<String, Object> row : products) {
                AmazonProductSnapshot p = new AmazonProductSnapshot();
                p.setId(textOr(row.get("id"), "prd_" + UUID.randomUUID()));
                p.setTenantId(tenantId);
                p.setPlatformAccountId(accountId);
                p.setAsin(text(row.get("asin")));
                p.setSku(text(row.get("sku")));
                p.setProductName(textOr(row.get("product_name"), text(row.get("productName"))));
                p.setOrders30d(intVal(row.get("orders_30d")));
                p.setRevenue30d(text(row.get("revenue_30d")));
                p.setPageViews(intVal(row.get("page_views")));
                p.setInventory(intVal(row.get("inventory")));
                p.setAcos(doubleVal(row.get("acos")));
                p.setAdSpend30d(text(row.get("ad_spend_30d")));
                p.setRankNo(intVal(row.get("rank_no")));
                p.setCurrency(textOr(row.get("currency"), "USD"));
                p.setSyncedAt(textOr(row.get("synced_at"), syncedAt));
                productSnapshotRepository.save(p);
            }
        }

        persistItems(tenantId, accountId, syncedAt, "buyer_message", rows(result.get("buyer_messages")));
        persistItems(tenantId, accountId, syncedAt, "review", rows(result.get("reviews")));
        persistItems(tenantId, accountId, syncedAt, "coupon", rows(result.get("coupons")));
        persistItems(tenantId, accountId, syncedAt, "seller_news", rows(result.get("seller_news")));
        persistItems(tenantId, accountId, syncedAt, "shipment", rows(result.get("shipments")));
        persistItems(tenantId, accountId, syncedAt, "case", rows(result.get("cases")));
        persistItems(tenantId, accountId, syncedAt, "outbound_order", rows(result.get("outbound_orders")));
    }

    private void persistItems(Long tenantId, String accountId, String syncedAt, String type, List<Map<String, Object>> rows) {
        if (rows.isEmpty()) return;
        operationalItemRepository.deleteByTenantIdAndPlatformAccountIdAndItemType(tenantId, accountId, type);
        for (Map<String, Object> row : rows) {
            AmazonOperationalItem item = new AmazonOperationalItem();
            item.setId(textOr(row.get("id"), type + "_" + UUID.randomUUID()));
            item.setTenantId(tenantId);
            item.setPlatformAccountId(accountId);
            item.setItemType(type);
            item.setExternalKey(text(row.get("external_key")));
            item.setPayloadJson(json(row));
            item.setSyncedAt(textOr(row.get("synced_at"), syncedAt));
            operationalItemRepository.save(item);
        }
    }

    @SuppressWarnings("unchecked")
    private List<Map<String, Object>> rows(Object value) {
        if (!(value instanceof List<?> list)) return List.of();
        List<Map<String, Object>> out = new ArrayList<>();
        for (Object row : list) if (row instanceof Map<?, ?> m) out.add((Map<String, Object>) m);
        return out;
    }
    private String json(Object v) { try { return objectMapper.writeValueAsString(v); } catch (Exception e) { return "{}"; } }
    private String text(Object v) { return v == null ? "" : String.valueOf(v).trim(); }
    private String textOr(Object v, String fb) { String t = text(v); return t.isBlank() ? fb : t; }
    private Integer intVal(Object v) { try { return v == null || String.valueOf(v).isBlank() ? 0 : Integer.parseInt(String.valueOf(v)); } catch (Exception e) { return 0; } }
    private Double doubleVal(Object v) { try { return v == null || String.valueOf(v).isBlank() ? 0d : Double.parseDouble(String.valueOf(v)); } catch (Exception e) { return 0d; } }
}
