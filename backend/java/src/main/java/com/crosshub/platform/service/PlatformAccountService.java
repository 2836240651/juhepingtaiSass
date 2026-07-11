package com.crosshub.platform.service;

import com.crosshub.platform.dto.StorePayload;

import java.util.List;
import java.util.Map;

public interface PlatformAccountService {
    List<Map<String, Object>> list(String platform);

    Map<String, Object> upsert(StorePayload payload);

    List<Map<String, Object>> upsertBatch(String companyName, List<StorePayload> stores);

    Map<String, Object> delete(String id);

    /** 爬虫同步成功后，将未关联的 Temu 绑定账号与 temu_shop 自动匹配 */
    int autoLinkTemuShops(Long tenantId);
}
