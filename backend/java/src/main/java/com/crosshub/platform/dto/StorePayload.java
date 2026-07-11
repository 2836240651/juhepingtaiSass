package com.crosshub.platform.dto;

public record StorePayload(
        String id,
        String platform,
        String storeName,
        String account,
        String password,
        String companyName,
        String externalShopId
) {
    public StorePayload(String id, String platform, String storeName, String account, String password, String companyName) {
        this(id, platform, storeName, account, password, companyName, null);
    }
}
