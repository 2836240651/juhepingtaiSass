package com.crosshub.tenant.service;

import com.crosshub.temu.entity.TemuSale;
import com.crosshub.temu.entity.TemuShop;
import java.util.List;

public interface DataScopeService {
    public Long requireTenantId();
    public List<TemuShop> scopedShops();
    public List<TemuSale> scopedSales(String reportTime, String shopId);
    public String latestReportTime();
    public List<String> resolveScopeForLogin(Long tenantId, Long userId, boolean bossPortal);
    public List<String> resolvePlatformsForLogin(Long tenantId, Long userId, boolean bossPortal);
    public List<String> resolveWarehouseScopeForLogin(Long tenantId, Long userId, String portalRole);
    public List<String> resolveWarehouseScopeNamesForLogin(Long tenantId, Long userId, String portalRole);
}
