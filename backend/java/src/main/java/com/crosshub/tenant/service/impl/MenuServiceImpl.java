package com.crosshub.tenant.service.impl;

import com.crosshub.tenant.service.MenuService;



import com.crosshub.auth.entity.AppUser;

import com.crosshub.tenant.entity.SysMenu;

import com.crosshub.tenant.entity.TenantFeature;

import com.crosshub.tenant.repository.SysMenuRepository;

import com.crosshub.tenant.repository.TenantFeatureRepository;

import com.crosshub.tenant.repository.UserMenuGrantRepository;

import com.crosshub.tenant.repository.UserPlatformScopeRepository;

import org.springframework.stereotype.Service;



import java.util.LinkedHashMap;

import java.util.List;

import java.util.Map;

import java.util.Set;

import java.util.stream.Collectors;



@Service

public class MenuServiceImpl implements MenuService {

    private final SysMenuRepository menuRepository;

    private final TenantFeatureRepository featureRepository;

    private final UserPlatformScopeRepository platformScopeRepository;

    private final UserMenuGrantRepository menuGrantRepository;



    public MenuServiceImpl(

            SysMenuRepository menuRepository,

            TenantFeatureRepository featureRepository,

            UserPlatformScopeRepository platformScopeRepository,

            UserMenuGrantRepository menuGrantRepository

    ) {

        this.menuRepository = menuRepository;

        this.featureRepository = featureRepository;

        this.platformScopeRepository = platformScopeRepository;

        this.menuGrantRepository = menuGrantRepository;

    }



    public List<Map<String, Object>> menusForUser(AppUser user, String portalRole) {

        Long tenantId = user.getTenantId();

        if (tenantId == null) {

            return List.of();

        }



        Set<String> enabledFeatures = featureRepository.findByTenantIdAndEnabled(tenantId, 1).stream()

                .map(TenantFeature::getFeatureCode)

                .collect(Collectors.toSet());



        boolean bossPortal = "boss".equalsIgnoreCase(portalRole);

        if ("warehouse".equalsIgnoreCase(portalRole)) {
            return menuRepository.findByPortalOrderBySortOrderAsc(portalRole).stream()
                    .filter(menu -> enabledFeatures.contains(menu.getCode()))
                    .map(this::toDto)
                    .toList();
        }

        if (bossPortal) {

            return menuRepository.findByPortalOrderBySortOrderAsc(portalRole).stream()

                    .filter(menu -> enabledFeatures.contains(menu.getCode()))

                    .map(this::toDto)

                    .toList();

        }



        Set<String> grantedMenus = menuGrantRepository.findByTenantIdAndUserId(tenantId, user.getId()).stream()

                .map(grant -> grant.getMenuCode().toLowerCase())

                .collect(Collectors.toSet());



        List<String> userPlatforms = platformScopeRepository.findByTenantIdAndUserId(tenantId, user.getId()).stream()

                .map(scope -> scope.getPlatform().toLowerCase())

                .toList();



        return menuRepository.findByPortalOrderBySortOrderAsc(portalRole).stream()

                .filter(menu -> enabledFeatures.contains(menu.getCode()))

                .filter(menu -> allowEmployeeMenu(menu, userPlatforms, grantedMenus))

                .map(this::toDto)

                .toList();

    }



    private boolean allowEmployeeMenu(SysMenu menu, List<String> userPlatforms, Set<String> grantedMenus) {

        if ("base".equals(menu.getMenuType())) {

            return true;

        }

        if ("admin".equals(menu.getMenuType())) {

            return false;

        }

        if ("employee.warehouse".equalsIgnoreCase(menu.getCode())) {

            return grantedMenus.contains("employee.warehouse");

        }

        if ("module".equals(menu.getMenuType())) {

            return allowEmployeeMenuByPlatform(menu, userPlatforms);

        }

        return false;

    }



    private boolean allowEmployeeMenuByPlatform(SysMenu menu, List<String> userPlatforms) {

        if (!"module".equals(menu.getMenuType())) {

            return false;

        }

        String platform = menu.getPlatform();

        if (platform == null || platform.isBlank()) {

            return false;

        }

        if ("dtc".equalsIgnoreCase(platform)) {

            return userPlatforms.stream().anyMatch(p ->

                    "shopify".equalsIgnoreCase(p) || "wordpress".equalsIgnoreCase(p) || "dtc".equalsIgnoreCase(p));

        }

        return userPlatforms.stream().anyMatch(p -> p.equalsIgnoreCase(platform));

    }



    private Map<String, Object> toDto(SysMenu menu) {

        Map<String, Object> item = new LinkedHashMap<>();

        item.put("code", menu.getCode());

        item.put("path", menu.getPath());

        item.put("label", menu.getLabel());

        item.put("platform", menu.getPlatform());

        item.put("menu_type", menu.getMenuType());

        item.put("sort_order", menu.getSortOrder());

        item.put("parent_code", menu.getParentCode());

        return item;

    }

}
