package com.crosshub.amazon.service;

import java.util.Map;

public interface AmazonOperationalService {
    Map<String, Object> daily(String storeId);
    Map<String, Object> insights(String storeId);
    Map<String, Object> spApiStatus();
    Map<String, Object> integrationStatus();
}
