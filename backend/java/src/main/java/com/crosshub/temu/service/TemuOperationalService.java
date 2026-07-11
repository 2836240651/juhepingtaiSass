package com.crosshub.temu.service;

import com.crosshub.temu.entity.TemuSale;
import com.crosshub.temu.entity.TemuShop;
import java.util.List;
import java.util.Map;

public interface TemuOperationalService {
    public String latestReportTime();
    public List<TemuShop> shops();
    public List<TemuSale> scopedSales(String reportTime, String shopId);
    public Map<String, Object> operationalBundle(String shopId, String reportTime);
    public Map<String, Object> salesTrend(String shopId, int days);
}
