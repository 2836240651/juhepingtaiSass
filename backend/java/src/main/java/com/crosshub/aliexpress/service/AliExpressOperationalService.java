package com.crosshub.aliexpress.service;

import java.util.Map;

public interface AliExpressOperationalService {
    Map<String, Object> operational(String storeId);
    Map<String, Object> todayOrders(String storeId);
    Map<String, Object> violations(String storeId);
}

