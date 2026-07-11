package com.crosshub.temu.dto;

public record ReplenishResult(
        boolean needReplenish,
        int replenishQty,
        double coverDays,
        double targetStock,
        double dailySalesAdjusted,
        double warningDays
) {}
