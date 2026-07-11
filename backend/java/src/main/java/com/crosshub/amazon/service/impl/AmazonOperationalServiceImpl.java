package com.crosshub.amazon.service.impl;

import com.crosshub.agent.entity.IntegrationAgent;
import com.crosshub.agent.repository.IntegrationAgentRepository;
import com.crosshub.amazon.entity.*;
import com.crosshub.amazon.repository.*;
import com.crosshub.amazon.service.AmazonOperationalService;
import com.crosshub.platform.entity.PlatformAccount;
import com.crosshub.platform.repository.PlatformAccountRepository;
import com.crosshub.tenant.service.DataScopeService;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;

@Service
public class AmazonOperationalServiceImpl implements AmazonOperationalService {
    private static final DateTimeFormatter TS = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
    private static final long AGENT_HEARTBEAT_TTL_SECONDS = 90;

    private final DataScopeService dataScopeService;
    private final PlatformAccountRepository platformAccountRepository;
    private final IntegrationAgentRepository integrationAgentRepository;
    private final AmazonAccountMetricRepository accountMetricRepository;
    private final AmazonOperationalItemRepository operationalItemRepository;
    private final AmazonProductSnapshotRepository productSnapshotRepository;
    private final ObjectMapper objectMapper;

    public AmazonOperationalServiceImpl(
            DataScopeService dataScopeService,
            PlatformAccountRepository platformAccountRepository,
            IntegrationAgentRepository integrationAgentRepository,
            AmazonAccountMetricRepository accountMetricRepository,
            AmazonOperationalItemRepository operationalItemRepository,
            AmazonProductSnapshotRepository productSnapshotRepository,
            ObjectMapper objectMapper
    ) {
        this.dataScopeService = dataScopeService;
        this.platformAccountRepository = platformAccountRepository;
        this.integrationAgentRepository = integrationAgentRepository;
        this.accountMetricRepository = accountMetricRepository;
        this.operationalItemRepository = operationalItemRepository;
        this.productSnapshotRepository = productSnapshotRepository;
        this.objectMapper = objectMapper;
    }

    public Map<String, Object> daily(String storeId) {
        Long tenantId = dataScopeService.requireTenantId();
        List<String> storeIds = storeIds(tenantId, storeId);
        if (storeIds.isEmpty()) {
            return Map.of("buyer_messages", List.of(), "account_metrics", List.of(), "reviews", List.of(), "coupons", List.of(), "seller_news", List.of(), "shipments", List.of(), "cases", List.of(), "synced_at", "");
        }
        List<AmazonAccountMetric> metrics = accountMetricRepository.findByTenantIdAndPlatformAccountIdInOrderBySyncedAtDesc(tenantId, storeIds);
        List<AmazonOperationalItem> items = operationalItemRepository.findByTenantIdAndPlatformAccountIdInAndItemTypeInOrderBySyncedAtDesc(
                tenantId, storeIds, List.of("buyer_message", "review", "coupon", "seller_news", "shipment", "case")
        );
        Map<String, List<Map<String, Object>>> byType = new HashMap<>();
        byType.put("buyer_message", new ArrayList<>());
        byType.put("review", new ArrayList<>());
        byType.put("coupon", new ArrayList<>());
        byType.put("seller_news", new ArrayList<>());
        byType.put("shipment", new ArrayList<>());
        byType.put("case", new ArrayList<>());
        String syncedAt = "";
        for (AmazonOperationalItem item : items) {
            Map<String, Object> payload = payload(item.getPayloadJson());
            payload.putIfAbsent("id", item.getId());
            payload.putIfAbsent("store_id", item.getPlatformAccountId());
            byType.get(item.getItemType()).add(payload);
            if (syncedAt.isBlank() || syncedAt.compareTo(item.getSyncedAt()) < 0) syncedAt = item.getSyncedAt();
        }
        List<Map<String, Object>> metricRows = new ArrayList<>();
        for (AmazonAccountMetric metric : metrics) {
            metricRows.add(Map.of(
                    "id", metric.getId(),
                    "store_id", metric.getPlatformAccountId(),
                    "metric_key", metric.getMetricKey(),
                    "metric_label", metric.getMetricLabel() == null ? "" : metric.getMetricLabel(),
                    "status", metric.getStatus(),
                    "value_text", metric.getValueText() == null ? "" : metric.getValueText(),
                    "threshold_text", metric.getThresholdText() == null ? "" : metric.getThresholdText(),
                    "trend", metric.getTrend() == null ? "" : metric.getTrend(),
                    "note_text", metric.getNoteText() == null ? "" : metric.getNoteText(),
                    "synced_at", metric.getSyncedAt()
            ));
            if (syncedAt.isBlank() || syncedAt.compareTo(metric.getSyncedAt()) < 0) syncedAt = metric.getSyncedAt();
        }
        return Map.of(
                "buyer_messages", byType.get("buyer_message"),
                "account_metrics", metricRows,
                "reviews", byType.get("review"),
                "coupons", byType.get("coupon"),
                "seller_news", byType.get("seller_news"),
                "shipments", byType.get("shipment"),
                "cases", byType.get("case"),
                "synced_at", syncedAt
        );
    }

    public Map<String, Object> insights(String storeId) {
        Long tenantId = dataScopeService.requireTenantId();
        List<String> storeIds = storeIds(tenantId, storeId);
        if (storeIds.isEmpty()) return Map.of("products", List.of(), "outbound_orders", List.of(), "synced_at", "");

        List<AmazonProductSnapshot> products = productSnapshotRepository.findByTenantIdAndPlatformAccountIdInOrderBySyncedAtDesc(tenantId, storeIds);
        List<AmazonOperationalItem> outbound = operationalItemRepository.findByTenantIdAndPlatformAccountIdInAndItemTypeInOrderBySyncedAtDesc(
                tenantId, storeIds, List.of("outbound_order")
        );

        List<Map<String, Object>> productRows = new ArrayList<>();
        String syncedAt = "";
        for (AmazonProductSnapshot p : products) {
            Map<String, Object> row = new LinkedHashMap<>();
            row.put("id", p.getId());
            row.put("store_id", p.getPlatformAccountId());
            row.put("asin", str(p.getAsin()));
            row.put("sku", str(p.getSku()));
            row.put("product_name", str(p.getProductName()));
            row.put("orders_30d", p.getOrders30d());
            row.put("revenue_30d", str(p.getRevenue30d()));
            row.put("page_views", p.getPageViews());
            row.put("inventory", p.getInventory());
            row.put("acos", p.getAcos());
            row.put("ad_spend_30d", str(p.getAdSpend30d()));
            row.put("rank_no", p.getRankNo());
            row.put("currency", str(p.getCurrency()));
            productRows.add(row);
            if (syncedAt.isBlank() || syncedAt.compareTo(p.getSyncedAt()) < 0) syncedAt = p.getSyncedAt();
        }
        List<Map<String, Object>> outboundRows = new ArrayList<>();
        for (AmazonOperationalItem item : outbound) {
            Map<String, Object> row = payload(item.getPayloadJson());
            row.putIfAbsent("id", item.getId());
            row.putIfAbsent("store_id", item.getPlatformAccountId());
            outboundRows.add(row);
            if (syncedAt.isBlank() || syncedAt.compareTo(item.getSyncedAt()) < 0) syncedAt = item.getSyncedAt();
        }
        return Map.of("products", productRows, "outbound_orders", outboundRows, "synced_at", syncedAt);
    }

    public Map<String, Object> spApiStatus() {
        Long tenantId = dataScopeService.requireTenantId();
        int count = platformAccountRepository.findByTenantIdAndPlatformOrderByBoundAtDesc(tenantId, "amazon").size();
        Map<String, Object> integration = integrationStatus();
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("connected", count > 0);
        out.put("store_count", count);
        out.put("agent_online", integration.get("agent_online"));
        out.put("ziniao_online", integration.get("ziniao_online"));
        return out;
    }

    @Override
    public Map<String, Object> integrationStatus() {
        Long tenantId = dataScopeService.requireTenantId();
        List<IntegrationAgent> agents = integrationAgentRepository.findByTenantIdOrderByCreatedAtDesc(tenantId);
        IntegrationAgent latestOnline = null;
        boolean ziniaoOnline = false;
        for (IntegrationAgent agent : agents) {
            if (!isAgentHeartbeatFresh(agent)) {
                continue;
            }
            if (latestOnline == null) {
                latestOnline = agent;
            }
            if (agent.getZiniaoOnline() != null && agent.getZiniaoOnline() == 1) {
                ziniaoOnline = true;
            }
        }
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("agent_online", latestOnline != null);
        out.put("ziniao_online", ziniaoOnline);
        out.put("agent_count", agents.size());
        if (latestOnline != null) {
            out.put("node_id", latestOnline.getId());
            out.put("node_name", latestOnline.getName());
            out.put("last_heartbeat_at", latestOnline.getLastHeartbeatAt());
        } else {
            out.put("node_id", "");
            out.put("node_name", "");
            out.put("last_heartbeat_at", "");
        }
        return out;
    }

    private boolean isAgentHeartbeatFresh(IntegrationAgent agent) {
        if (agent == null || !"active".equalsIgnoreCase(agent.getStatus())) {
            return false;
        }
        LocalDateTime heartbeat = parseTime(agent.getLastHeartbeatAt());
        if (heartbeat == null) {
            return false;
        }
        return !heartbeat.plusSeconds(AGENT_HEARTBEAT_TTL_SECONDS).isBefore(LocalDateTime.now());
    }

    private LocalDateTime parseTime(String text) {
        if (text == null || text.isBlank()) {
            return null;
        }
        try {
            return LocalDateTime.parse(text, TS);
        } catch (Exception ex) {
            return null;
        }
    }

    private List<String> storeIds(Long tenantId, String storeId) {
        if (storeId != null && !storeId.isBlank()) {
            platformAccountRepository.findByIdAndTenantId(storeId, tenantId)
                    .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "店铺不存在"));
            return List.of(storeId);
        }
        List<PlatformAccount> stores = platformAccountRepository.findByTenantIdAndPlatformOrderByBoundAtDesc(tenantId, "amazon");
        return stores.stream().map(PlatformAccount::getId).toList();
    }

    private Map<String, Object> payload(String json) {
        if (json == null || json.isBlank()) return new LinkedHashMap<>();
        try { return objectMapper.readValue(json, new TypeReference<>() {}); }
        catch (Exception ex) { return new LinkedHashMap<>(); }
    }

    private String str(String text) { return text == null ? "" : text; }
}
