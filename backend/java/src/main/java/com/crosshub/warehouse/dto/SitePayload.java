package com.crosshub.warehouse.dto;

public record SitePayload(
        String name,
        String code,
        String address,
        Boolean status,
        Integer sortOrder
) {}
