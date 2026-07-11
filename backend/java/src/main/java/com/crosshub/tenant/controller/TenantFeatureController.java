package com.crosshub.tenant.controller;

import com.crosshub.tenant.dto.UpdateTenantFeaturesRequest;
import com.crosshub.security.AuthContext;
import com.crosshub.tenant.service.TenantFeatureService;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

import java.util.LinkedHashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/tenant/features")
public class TenantFeatureController {
    private final TenantFeatureService featureService;
    private final AuthContext authContext;

    public TenantFeatureController(TenantFeatureService featureService, AuthContext authContext) {
        this.featureService = featureService;
        this.authContext = authContext;
    }

    @GetMapping
    public Map<String, Object> list() {
        Long tenantId = requireBossTenant();
        return Map.of("code", 0, "data", featureService.listForTenant(tenantId));
    }

    @PutMapping
    public Map<String, Object> update(@RequestBody UpdateTenantFeaturesRequest request) {
        Long tenantId = requireBossTenant();
        int updated = featureService.updateForTenant(
                tenantId,
                request == null ? null : request.features()
        );
        Map<String, Object> data = new LinkedHashMap<>();
        data.put("updated", updated);
        return Map.of(
                "code", 0,
                "message", "已更新 " + updated + " 项功能开关",
                "data", data
        );
    }

    private Long requireBossTenant() {
        if (!authContext.isBossPortal() && !authContext.isAdmin()) {
            throw new ResponseStatusException(HttpStatus.FORBIDDEN, "仅企业管理员可操作功能开关");
        }
        Long tenantId = authContext.tenantId();
        if (tenantId == null) {
            throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "缺少租户上下文");
        }
        return tenantId;
    }
}
