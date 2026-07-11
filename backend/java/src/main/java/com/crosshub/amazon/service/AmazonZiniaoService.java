package com.crosshub.amazon.service;

import com.crosshub.amazon.dto.ZiniaoBindRequest;

import java.util.List;
import java.util.Map;

public interface AmazonZiniaoService {
    Map<String, Object> triggerDiscover();
    Map<String, Object> getDiscoverJob(String jobId);
    List<Map<String, Object>> listCandidates();
    List<Map<String, Object>> bindStores(ZiniaoBindRequest request);
}
