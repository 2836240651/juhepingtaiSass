package com.crosshub.aliexpress.dto;

public record AliExpressViolationPatchRequest(
        String appealStatus,
        String appealResult
) {}

