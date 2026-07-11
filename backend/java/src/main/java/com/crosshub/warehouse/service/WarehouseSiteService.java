package com.crosshub.warehouse.service;

import com.crosshub.warehouse.dto.SitePayload;
import com.crosshub.warehouse.entity.WarehouseSite;

import java.util.List;
import java.util.Map;

public interface WarehouseSiteService {
    List<Map<String, Object>> listSites(boolean activeOnly);

    Map<String, Object> createSite(SitePayload payload);

    Map<String, Object> updateSite(String id, SitePayload payload);

    Map<String, Object> updateStatus(String id, boolean active);

    void deleteSite(String id);

    WarehouseSite requireActiveSite(Long tenantId, String warehouseId);

    WarehouseSite requireSite(Long tenantId, String warehouseId);
}
