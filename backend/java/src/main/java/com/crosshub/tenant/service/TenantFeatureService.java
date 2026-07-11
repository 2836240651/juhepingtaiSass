package com.crosshub.tenant.service;

import com.crosshub.tenant.dto.FeatureToggleItem;

import java.util.List;
import java.util.Map;

public interface TenantFeatureService {
    List<Map<String, Object>> listForTenant(Long tenantId);

    int updateForTenant(Long tenantId, List<FeatureToggleItem> features);
}
