package com.crosshub.tenant.dto;

import java.util.List;

public record UpdateTenantFeaturesRequest(List<FeatureToggleItem> features) {}
