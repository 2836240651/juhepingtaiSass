package com.crosshub.temu.dto;

import com.crosshub.temu.entity.TemuSale;

public record LowSaleWarning(TemuSale sale, int s10, int s15) {}
