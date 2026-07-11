package com.crosshub.warehouse.service;

import java.util.Map;

public interface WarehouseOrderService {
    public Map<String, Object> listOrders();
    public Map<String, Object> getOrder(String id);
    public Map<String, Object> createOrder(Map<String, Object> payload);
    public Map<String, Object> createFromPlatformOrder(Map<String, Object> payload);
    public Map<String, Object> reviewOrder(String id, Map<String, Object> payload);
    public Map<String, Object> releaseOrder(String id, Map<String, Object> payload);
    public Map<String, Object> shipOrder(String id);
    public Map<String, Object> cancelOrder(String id);
    public void deleteOrder(String id);
}
