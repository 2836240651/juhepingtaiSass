package com.crosshub.tenant.service.impl;

import com.crosshub.tenant.dto.FeatureToggleItem;
import com.crosshub.tenant.entity.SysMenu;
import com.crosshub.tenant.entity.TenantFeature;
import com.crosshub.tenant.repository.SysMenuRepository;
import com.crosshub.tenant.repository.TenantFeatureRepository;
import com.crosshub.tenant.service.TenantFeatureService;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

@Service
public class TenantFeatureServiceImpl implements TenantFeatureService {
    private static final Set<String> PROTECTED_FEATURES = Set.of(
            "boss.settings",
            "boss.employees",
            "boss.accounts",
            "boss.dashboard",
            "boss.features",
            "employee.dashboard",
            "employee.tasks",
            "warehouse.pending_review",
            "warehouse.pending_shipment",
            "warehouse.shipped",
            "warehouse.tasks"
    );

    private final SysMenuRepository menuRepository;
    private final TenantFeatureRepository featureRepository;

    public TenantFeatureServiceImpl(
            SysMenuRepository menuRepository,
            TenantFeatureRepository featureRepository
    ) {
        this.menuRepository = menuRepository;
        this.featureRepository = featureRepository;
    }

    public List<Map<String, Object>> listForTenant(Long tenantId) {
        Map<String, TenantFeature> byCode = featureRepository.findByTenantId(tenantId).stream()
                .collect(Collectors.toMap(TenantFeature::getFeatureCode, row -> row, (a, b) -> a));

        return menuRepository.findAll().stream()
                .sorted(Comparator
                        .comparing(SysMenu::getPortal)
                        .thenComparing(menu -> menu.getSortOrder() == null ? 0 : menu.getSortOrder()))
                .map(menu -> {
                    TenantFeature row = byCode.get(menu.getCode());
                    boolean enabled = row == null || row.isEnabled();
                    Map<String, Object> item = new LinkedHashMap<>();
                    item.put("feature_code", menu.getCode());
                    item.put("enabled", enabled);
                    item.put("label", menu.getLabel());
                    item.put("portal", menu.getPortal());
                    item.put("platform", menu.getPlatform());
                    item.put("menu_type", menu.getMenuType());
                    item.put("protected", PROTECTED_FEATURES.contains(menu.getCode()));
                    return item;
                })
                .toList();
    }

    @Transactional
    public int updateForTenant(Long tenantId, List<FeatureToggleItem> features) {
        if (features == null || features.isEmpty()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "请至少提交一项功能开关");
        }

        Set<String> knownCodes = menuRepository.findAll().stream()
                .map(SysMenu::getCode)
                .collect(Collectors.toSet());

        int updated = 0;
        for (FeatureToggleItem item : features) {
            if (item == null || item.featureCode() == null || item.featureCode().isBlank()) {
                continue;
            }
            String code = item.featureCode().trim();
            if (!knownCodes.contains(code)) {
                throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "无效的功能编码: " + code);
            }
            boolean enabled = Boolean.TRUE.equals(item.enabled());
            if (!enabled && PROTECTED_FEATURES.contains(code)) {
                throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "核心功能不可关闭: " + code);
            }

            Set<String> targets = cascadeCodes(code);
            for (String target : targets) {
                upsertFeature(tenantId, target, enabled);
                updated += 1;
            }
        }
        return updated;
    }

    private void upsertFeature(Long tenantId, String code, boolean enabled) {
        TenantFeature row = featureRepository.findByTenantIdAndFeatureCode(tenantId, code)
                .orElseGet(() -> {
                    TenantFeature created = new TenantFeature();
                    created.setTenantId(tenantId);
                    created.setFeatureCode(code);
                    return created;
                });
        row.setEnabled(enabled);
        featureRepository.save(row);
    }

    private Set<String> cascadeCodes(String code) {
        Set<String> targets = new LinkedHashSet<>();
        targets.add(code);

        if (code.startsWith("boss.platform.")) {
            String platform = code.substring("boss.platform.".length());
            targets.add("employee.platform." + platform);
        } else if (code.startsWith("employee.platform.")) {
            String platform = code.substring("employee.platform.".length());
            targets.add("boss.platform." + platform);
        }
        return targets;
    }
}
