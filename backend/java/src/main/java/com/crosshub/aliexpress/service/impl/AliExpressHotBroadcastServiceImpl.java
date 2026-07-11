package com.crosshub.aliexpress.service.impl;

import com.crosshub.aliexpress.dto.AliExpressHotBroadcastCreateRequest;
import com.crosshub.aliexpress.dto.AliExpressHotBroadcastReadRequest;
import com.crosshub.aliexpress.entity.AliExpressHotBroadcast;
import com.crosshub.aliexpress.entity.AliExpressHotBroadcastRead;
import com.crosshub.aliexpress.repository.AliExpressHotBroadcastReadRepository;
import com.crosshub.aliexpress.repository.AliExpressHotBroadcastRepository;
import com.crosshub.aliexpress.service.AliExpressHotBroadcastService;
import com.crosshub.common.AppErrorCode;
import com.crosshub.tenant.service.DataScopeService;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@Service
public class AliExpressHotBroadcastServiceImpl implements AliExpressHotBroadcastService {
    private static final DateTimeFormatter TS = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

    private final AliExpressHotBroadcastRepository broadcastRepository;
    private final AliExpressHotBroadcastReadRepository readRepository;
    private final DataScopeService dataScopeService;

    public AliExpressHotBroadcastServiceImpl(
            AliExpressHotBroadcastRepository broadcastRepository,
            AliExpressHotBroadcastReadRepository readRepository,
            DataScopeService dataScopeService
    ) {
        this.broadcastRepository = broadcastRepository;
        this.readRepository = readRepository;
        this.dataScopeService = dataScopeService;
    }

    @Override
    public List<Map<String, Object>> list(String storeId) {
        Long tenantId = dataScopeService.requireTenantId();
        List<AliExpressHotBroadcast> rows = isBlank(storeId)
                ? broadcastRepository.findByTenantIdOrderByBroadcastAtDescCreatedAtDesc(tenantId)
                : broadcastRepository.findByTenantIdAndStoreIdOrderByBroadcastAtDescCreatedAtDesc(tenantId, storeId);
        List<String> ids = rows.stream().map(AliExpressHotBroadcast::getId).toList();
        Map<String, List<String>> readBy = new LinkedHashMap<>();
        for (AliExpressHotBroadcastRead row : readRepository.findByTenantIdAndBroadcastIdInOrderByReadAtDesc(tenantId, ids)) {
            readBy.computeIfAbsent(row.getBroadcastId(), ignored -> new ArrayList<>()).add(row.getReaderName());
        }
        List<Map<String, Object>> result = new ArrayList<>();
        for (AliExpressHotBroadcast row : rows) {
            result.add(toDto(row, readBy.getOrDefault(row.getId(), List.of())));
        }
        return result;
    }

    @Override
    @Transactional
    public Map<String, Object> create(AliExpressHotBroadcastCreateRequest request) {
        Long tenantId = dataScopeService.requireTenantId();
        AliExpressHotBroadcast row = new AliExpressHotBroadcast();
        row.setId(UUID.randomUUID().toString());
        row.setTenantId(tenantId);
        row.setStoreId(request == null || request.storeId() == null ? "" : request.storeId());
        row.setSku(request == null || request.sku() == null ? "" : request.sku());
        row.setProductName(request == null || request.name() == null ? "" : request.name());
        row.setDailySales(request == null ? 0 : request.dailySales());
        row.setAvg7DayDaily(request == null ? 0d : request.avg7DayDaily());
        row.setSurgeRatio(request == null ? 0d : request.surgeRatio());
        row.setOperatorName(request == null || request.operator() == null ? "" : request.operator());
        row.setSource(request == null || request.source() == null ? "manual" : request.source());
        row.setBroadcastAt(request == null || request.time() == null || request.time().isBlank() ? now() : request.time());
        row.setCreatedAt(now());
        row.setMessage(request == null || request.message() == null || request.message().isBlank() ? "爆款通报" : request.message());
        broadcastRepository.save(row);
        return toDto(row, List.of());
    }

    @Override
    @Transactional
    public Map<String, Object> markRead(String id, AliExpressHotBroadcastReadRequest request) {
        Long tenantId = dataScopeService.requireTenantId();
        AliExpressHotBroadcast broadcast = broadcastRepository.findByIdAndTenantId(id, tenantId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, AppErrorCode.HOT_BROADCAST_NOT_FOUND.getUserMessage()));
        AliExpressHotBroadcastRead read = new AliExpressHotBroadcastRead();
        read.setId(UUID.randomUUID().toString());
        read.setTenantId(tenantId);
        read.setBroadcastId(id);
        read.setReaderId(request == null || request.readerId() == null ? "" : request.readerId());
        read.setReaderName(request == null || request.readerName() == null ? "" : request.readerName());
        read.setReadAt(now());
        readRepository.save(read);
        List<String> readBy = readRepository.findByTenantIdAndBroadcastIdInOrderByReadAtDesc(tenantId, List.of(id))
                .stream().map(AliExpressHotBroadcastRead::getReaderName).toList();
        return toDto(broadcast, readBy);
    }

    private Map<String, Object> toDto(AliExpressHotBroadcast row, List<String> readBy) {
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("id", row.getId());
        out.put("store_id", row.getStoreId());
        out.put("sku", row.getSku());
        out.put("product_name", row.getProductName());
        out.put("daily_sales", row.getDailySales());
        out.put("avg7_day_daily", row.getAvg7DayDaily());
        out.put("surge_ratio", row.getSurgeRatio());
        out.put("operator_name", row.getOperatorName());
        out.put("source", row.getSource());
        out.put("broadcast_at", row.getBroadcastAt());
        out.put("message", row.getMessage());
        out.put("read_by", readBy);
        return out;
    }

    private boolean isBlank(String value) {
        return value == null || value.isBlank() || "all".equalsIgnoreCase(value);
    }

    private String now() {
        return LocalDateTime.now().format(TS);
    }
}

