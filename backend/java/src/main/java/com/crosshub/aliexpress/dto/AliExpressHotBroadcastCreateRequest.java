package com.crosshub.aliexpress.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public record AliExpressHotBroadcastCreateRequest(
        @JsonProperty("store_id") String storeId,
        String sku,
        String name,
        @JsonProperty("daily_sales") Integer dailySales,
        @JsonProperty("avg7_day_daily") Double avg7DayDaily,
        @JsonProperty("surge_ratio") Double surgeRatio,
        String operator,
        String source,
        String time,
        String message
) {}

