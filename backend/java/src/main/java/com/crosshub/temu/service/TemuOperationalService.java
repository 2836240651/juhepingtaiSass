package com.crosshub.temu.service;

import com.crosshub.temu.entity.TemuSale;
import com.crosshub.temu.entity.TemuShop;
import com.crosshub.temu.repository.TemuSaleRepository;
import com.crosshub.temu.repository.TemuShopRepository;
import com.crosshub.temu.security.AuthContext;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.util.*;

@Service
public class TemuOperationalService {
    private final TemuSaleRepository saleRepository;
    private final TemuShopRepository shopRepository;
    private final TemuWarningService warningService;
    private final AuthContext authContext;

    public TemuOperationalService(
            TemuSaleRepository saleRepository,
            TemuShopRepository shopRepository,
            TemuWarningService warningService,
            AuthContext authContext
    ) {
        this.saleRepository = saleRepository;
        this.shopRepository = shopRepository;
        this.warningService = warningService;
        this.authContext = authContext;
    }

    public String latestReportTime() {
        String latest = saleRepository.findLatestReportTime();
        return latest != null ? latest : LocalDate.now().toString();
    }

    public List<TemuShop> shops() {
        return shopRepository.findAll();
    }

    public List<TemuSale> scopedSales(String reportTime, String shopId) {
        List<TemuSale> sales;
        if (authContext.isAdmin()) {
            sales = shopId == null || shopId.isBlank() || "all".equals(shopId)
                    ? saleRepository.findByReportTime(reportTime)
                    : saleRepository.findByReportTimeAndShopId(reportTime, shopId);
        } else {
            Long uid = authContext.userId();
            if (uid == null) return List.of();
            sales = shopId == null || shopId.isBlank() || "all".equals(shopId)
                    ? saleRepository.findByReportTimeAndUserId(reportTime, uid)
                    : saleRepository.findByReportTimeAndShopIdAndUserId(reportTime, shopId, uid);
        }
        return sales;
    }

    public Map<String, Object> operationalBundle(String shopId, String reportTime) {
        String day = reportTime == null || reportTime.isBlank() ? latestReportTime() : reportTime;
        List<TemuSale> sales = scopedSales(day, shopId);

        List<Map<String, Object>> loseProducts = warningService.loseProducts(sales).stream()
                .map(this::saleMap)
                .toList();

        List<Map<String, Object>> lowWarnings = warningService.allLowSaleEstimates(sales).stream()
                .map(this::lowSaleMap)
                .toList();

        List<Map<String, Object>> inventoryWarnings = warningService.inventoryWarnings(sales).stream()
                .map(this::inventoryMap)
                .toList();

        List<Map<String, Object>> overloadProducts = warningService.overloadProducts(sales, 300).stream()
                .map(this::saleMap)
                .toList();

        Map<String, Object> body = new LinkedHashMap<>();
        body.put("code", 0);
        body.put("report_time", day);
        body.put("products", sales.stream().map(this::saleMap).toList());
        body.put("lose_products", loseProducts);
        body.put("low_warnings", lowWarnings);
        body.put("inventory_warnings", inventoryWarnings);
        body.put("overload_products", overloadProducts);
        return body;
    }

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

        return Map.of(
                "code", 0,
                "labels", labels,
                "values", values
        );
    }

    private Map<String, Object> saleMap(TemuSale sale) {
        Map<String, Object> map = new LinkedHashMap<>();
        map.put("id", sale.getId());
        map.put("platform", sale.getPlatform());
        map.put("status", sale.getStatus());
        map.put("report_time", sale.getReportTime());
        map.put("shop_name", sale.getShopName());
        map.put("shop_id", sale.getShopId());
        map.put("user_id", sale.getUserId());
        map.put("cost", sale.getCost());
        map.put("category_name", sale.getCategoryName());
        map.put("img_url", sale.getImgUrl());
        map.put("title", sale.getTitle());
        map.put("skc", sale.getSkc());
        map.put("spu", sale.getSpu());
        map.put("ext_code", sale.getExtCode());
        map.put("son_sku", sale.getSonSku());
        map.put("son_price", sale.getSonPrice());
        map.put("son_today_sales", sale.getSonTodaySales());
        map.put("son_sales_seven_days", sale.getSonSalesSevenDays());
        map.put("son_sales_thirty_days", sale.getSonSalesThirtyDays());
        map.put("join_site_time", sale.getJoinSiteTime());
        map.put("warehouse_available_stock", sale.getWarehouseAvailableStock());
        map.put("nickname", sale.getNickname());
        map.put("username", sale.getUsername());
        map.put("enterprise", sale.getEnterprise());
        return map;
    }

    private Map<String, Object> lowSaleMap(TemuWarningService.LowSaleWarning warning) {
        Map<String, Object> map = saleMap(warning.sale());
        map.put("s10", warning.s10());
        map.put("s15", warning.s15());
        return map;
    }

    private Map<String, Object> inventoryMap(TemuWarningService.InventoryWarning warning) {
        Map<String, Object> map = saleMap(warning.sale());
        TemuWarningService.ReplenishResult calc = warning.calc();
        map.put("s7", safeInt(warning.sale().getSonSalesSevenDays()));
        map.put("s30", safeInt(warning.sale().getSonSalesThirtyDays()));
        map.put("stock", safeInt(warning.sale().getWarehouseAvailableStock()));
        map.put("cover_days", round2(calc.coverDays()));
        map.put("warning_days", calc.warningDays());
        map.put("replenish_qty", calc.replenishQty());
        map.put("target_stock", round2(calc.targetStock()));
        map.put("daily_sales_adj", round2(calc.dailySalesAdjusted()));
        return map;
    }

    private int safeInt(Integer value) {
        return value == null ? 0 : value;
    }

    private double round2(double value) {
        return Math.round(value * 100.0) / 100.0;
    }
}
