package com.crosshub.amazon.service;

import com.crosshub.amazon.dto.AmazonSyncRequest;
import com.crosshub.amazon.entity.AmazonSyncJob;

import java.util.Map;

public interface AmazonSyncService {
    Map<String, Object> triggerSync(AmazonSyncRequest request);
    AmazonSyncJob getJob(String jobId);
    void onAgentTaskCompleted(String taskId, String status, Map<String, Object> result, String errorCode, String errorMessage);
}
