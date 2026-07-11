package com.crosshub.temu.service.impl;

import com.crosshub.temu.service.TemuCrawlAuthService;
import com.crosshub.tenant.service.DataScopeService;

import com.crosshub.temu.entity.TemuShop;
import com.crosshub.security.AuthContext;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import java.util.List;
import java.util.Locale;

@Service
public class TemuCrawlAuthServiceImpl implements TemuCrawlAuthService {
    private final AuthContext authContext;
    private final DataScopeService dataScopeService;

    public TemuCrawlAuthServiceImpl(AuthContext authContext, DataScopeService dataScopeService) {
        this.authContext = authContext;
        this.dataScopeService = dataScopeService;
    }

    public void assertCanTriggerCrawl() {
        dataScopeService.requireTenantId();
        if (authContext.isBossPortal() || authContext.isAdmin()) {
            return;
        }

        List<TemuShop> shops = dataScopeService.scopedShops();
        if (!shops.isEmpty()) {
            return;
        }

        boolean hasTemuPlatform = authContext.platforms().stream()
                .anyMatch(platform -> "temu".equalsIgnoreCase(platform));
        if (hasTemuPlatform) {
            return;
        }

        throw new ResponseStatusException(HttpStatus.FORBIDDEN, "无权触发 Temu 爬取");
    }
}
