package com.crosshub.aliexpress.service;

import com.crosshub.aliexpress.dto.AliExpressViolationPatchRequest;

import java.util.Map;

public interface AliExpressViolationService {
    Map<String, Object> patch(String id, AliExpressViolationPatchRequest request);
}

