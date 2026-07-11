package com.crosshub.platform.dto;

public record BindRequest(
        String id,
        String platform,
        String storeName,
        String account,
        String password,
        String companyName,
        String externalShopId
) {}
