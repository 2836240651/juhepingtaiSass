package com.crosshub.amazon.service.impl;

import com.crosshub.amazon.entity.AmazonOperationalItem;
import com.crosshub.amazon.repository.AmazonOperationalItemRepository;
import com.crosshub.amazon.service.AmazonWriteService;
import com.crosshub.tenant.service.DataScopeService;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;

@Service
public class AmazonWriteServiceImpl implements AmazonWriteService {
    private static final DateTimeFormatter TS = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
    private final DataScopeService dataScopeService;
    private final AmazonOperationalItemRepository operationalItemRepository;
    private final ObjectMapper objectMapper;

    public AmazonWriteServiceImpl(DataScopeService dataScopeService, AmazonOperationalItemRepository operationalItemRepository, ObjectMapper objectMapper) {
        this.dataScopeService = dataScopeService;
        this.operationalItemRepository = operationalItemRepository;
        this.objectMapper = objectMapper;
    }

    @Transactional
    public Map<String, Object> replyMessage(String id, String templateId, String note) { return patch(id, "buyer_message", "replied", templateId, note, null); }
    @Transactional
    public Map<String, Object> handleReview(String id, String note) { return patch(id, "review", "handled", null, note, null); }
    @Transactional
    public Map<String, Object> acknowledgeCase(String id, String note) { return patch(id, "case", "read", null, note, null); }
    @Transactional
    public Map<String, Object> shipOutbound(String id, String trackingNo) { return patch(id, "outbound_order", "shipped", null, null, trackingNo); }

    private Map<String, Object> patch(String id, String type, String status, String templateId, String note, String trackingNo) {
        AmazonOperationalItem item = requireItem(id, type);
        Map<String, Object> payload = payload(item);
        payload.put("status", status);
        if (templateId != null) payload.put("template_used", templateId);
        if (note != null) payload.put("note", note);
        if (trackingNo != null) payload.put("tracking_no", trackingNo);
        if ("buyer_message".equals(type)) payload.put("replied_at", now());
        if ("review".equals(type)) payload.put("handled_at", now());
        if ("case".equals(type)) payload.put("read_at", now());
        if ("outbound_order".equals(type)) payload.put("shipped_at", now());
        item.setPayloadJson(json(payload));
        item.setSyncedAt(now());
        operationalItemRepository.save(item);
        return payload;
    }

    private AmazonOperationalItem requireItem(String id, String type) {
        Long tenantId = dataScopeService.requireTenantId();
        return operationalItemRepository.findAll().stream()
                .filter(x -> id.equals(x.getId()) && tenantId.equals(x.getTenantId()) && type.equals(x.getItemType()))
                .findFirst()
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "资源不存在"));
    }

    private Map<String, Object> payload(AmazonOperationalItem item) {
        try { return objectMapper.readValue(item.getPayloadJson(), new TypeReference<>() {}); }
        catch (Exception ex) { return new LinkedHashMap<>(); }
    }

    private String json(Object v) { try { return objectMapper.writeValueAsString(v); } catch (Exception ex) { return "{}"; } }
    private String now() { return LocalDateTime.now().format(TS); }
}
