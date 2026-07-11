package com.crosshub.temu.dto;

import com.crosshub.temu.entity.TemuSale;

public record InventoryWarning(TemuSale sale, ReplenishResult calc) {}
