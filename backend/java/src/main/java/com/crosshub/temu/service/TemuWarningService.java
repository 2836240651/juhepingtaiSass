package com.crosshub.temu.service;

import com.crosshub.temu.dto.InventoryWarning;
import com.crosshub.temu.dto.LowSaleWarning;
import com.crosshub.temu.dto.ReplenishResult;
import com.crosshub.temu.entity.TemuSale;

import java.util.List;

public interface TemuWarningService {
    ReplenishResult calcReplenish(int s7, int s30, int stock, double leadTime);

    int[] estimateS10S15(int today, int last7, int last30);

    List<TemuSale> loseProducts(List<TemuSale> sales);

    List<LowSaleWarning> lowSaleWarnings(List<TemuSale> sales);

    List<LowSaleWarning> allLowSaleEstimates(List<TemuSale> sales);

    List<InventoryWarning> inventoryWarnings(List<TemuSale> sales);

    List<TemuSale> overloadProducts(List<TemuSale> sales, int limit);
}
