package com.crosshub.common;

import java.util.List;
import java.util.Locale;

public final class DemoDataFilter {
    private DemoDataFilter() {
    }

    public static boolean isDemoShopId(String shopId) {
        if (shopId == null || shopId.isBlank()) {
            return false;
        }
        String normalized = shopId.trim().toLowerCase(Locale.ROOT);
        return normalized.startsWith("demo_") || normalized.startsWith("mock_");
    }

    public static boolean isDemoSku(String sku) {
        if (sku == null || sku.isBlank()) {
            return false;
        }
        return sku.trim().toUpperCase(Locale.ROOT).startsWith("YT-T");
    }

    public static <T> List<T> filterDemoShops(List<T> shops, java.util.function.Function<T, String> shopIdGetter) {
        return shops.stream().filter(shop -> !isDemoShopId(shopIdGetter.apply(shop))).toList();
    }
}
