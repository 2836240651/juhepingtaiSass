package com.crosshub.aliexpress.service;

import com.crosshub.aliexpress.dto.AliExpressHotBroadcastCreateRequest;
import com.crosshub.aliexpress.dto.AliExpressHotBroadcastReadRequest;

import java.util.List;
import java.util.Map;

public interface AliExpressHotBroadcastService {
    List<Map<String, Object>> list(String storeId);
    Map<String, Object> create(AliExpressHotBroadcastCreateRequest request);
    Map<String, Object> markRead(String id, AliExpressHotBroadcastReadRequest request);
}

