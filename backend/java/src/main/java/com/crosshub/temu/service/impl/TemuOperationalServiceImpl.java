package com.crosshub.temu.service.impl;

import com.crosshub.temu.dto.InventoryWarning;
import com.crosshub.temu.dto.LowSaleWarning;
import com.crosshub.temu.entity.TemuSale;
import com.crosshub.temu.entity.TemuShop;
import com.crosshub.temu.mapper.TemuMapper;
import com.crosshub.security.AuthContext;
import com.crosshub.tenant.service.DataScopeService;
import com.crosshub.temu.service.TemuOperationalService;
import com.crosshub.temu.service.TemuWarningService;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Service
public class TemuOperationalServiceImpl implements TemuOperationalService {
    private final DataScopeService dataScopeService;
    private final TemuWarningService warningService;
    private final AuthContext authContext;
    private final TemuMapper temuMapper;

    public TemuOperationalServiceImpl(
            DataScopeService dataScopeService,
            TemuWarningService warningService,
            AuthContext authContext,
            TemuMapper temuMapper
    ) {
        this.dataScopeService = dataScopeService;
        this.warningService = warningService;
        this.authContext = authContext;
        this.temuMapper = temuMapper;
    }

    @Override
    public String latestReportTime() {
        String latest = dataScopeService.latestReportTime();
        return latest != null ? latest : LocalDate.now().toString();
    }

    @Override
    public List<TemuShop> shops() {
        return dataScopeService.scopedShops();
    }

    @Override
    public List<TemuSale> scopedSales(String reportTime, String shopId) {
        return dataScopeService.scopedSales(reportTime, shopId);
    }

    @Override
    public Map<String, Object> operationalBundle(String shopId, String reportTime) {
        String day = reportTime == null || reportTime.isBlank() ? latestReportTime() : reportTime;
        List<TemuSale> sales = scopedSales(day, shopId);

        Map<String, Object> body = new LinkedHashMap<>();
        body.put("code", 0);
        body.put("report_time", day);
        body.put("tenant_id", authContext.tenantId());
        body.put("products", sales.stream().map(temuMapper::toSaleDto).toList());
        body.put("lose_products", warningService.loseProducts(sales).stream().map(temuMapper::toSaleDto).toList());
        body.put("low_warnings", warningService.allLowSaleEstimates(sales).stream().map(temuMapper::toLowSaleDto).toList());
        body.put("inventory_warnings", warningService.inventoryWarnings(sales).stream().map(temuMapper::toInventoryDto).toList());
        body.put("overload_products", warningService.overloadProducts(sales, 300).stream().map(temuMapper::toSaleDto).toList());
        return body;
    }

    @Override
    public Map<String, Object> salesTrend(String shopId, int days) {
        List<String> labels = new ArrayList<>();
        List<Integer> values = new ArrayList<>();
        LocalDate today = LocalDate.now();

        for (int offset = days - 1; offset >= 0; offset--) {
            LocalDate date = today.minusDays(offset);
            String reportTime = date.toString();
            List<TemuSale> sales = scopedSales(reportTime, shopId);
            int total = sales.stream().mapToInt(s -> s.getSonTodaySales() == null ? 0 : s.getSonTodaySales()).sum();
            labels.add(reportTime.substring(5));
            values.add(total);
        }

        return Map.of("code", 0, "labels", labels, "values", values);
    }
}
