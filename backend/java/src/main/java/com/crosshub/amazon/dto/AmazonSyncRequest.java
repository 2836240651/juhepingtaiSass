package com.crosshub.amazon.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public record AmazonSyncRequest(
        String scope,
        @JsonProperty("platform_account_id") String platformAccountId
) {}
