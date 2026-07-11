package com.crosshub.amazon.service;

import com.crosshub.amazon.entity.AmazonSyncJob;

import java.util.Map;

public interface AmazonOperationalPersistenceService {
    void persistSyncResult(AmazonSyncJob job, Map<String, Object> result);
}
