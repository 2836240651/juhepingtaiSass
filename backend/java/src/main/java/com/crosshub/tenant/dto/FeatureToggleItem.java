package com.crosshub.tenant.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public record FeatureToggleItem(
        @JsonProperty("feature_code") String featureCode,
        Boolean enabled
) {}
