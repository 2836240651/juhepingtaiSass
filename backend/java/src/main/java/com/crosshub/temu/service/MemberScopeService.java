package com.crosshub.temu.service;



import com.crosshub.temu.entity.UserMenuGrant;

import com.crosshub.temu.entity.UserPlatformScope;

import com.crosshub.temu.entity.UserShopScope;

import com.crosshub.temu.repository.SysMenuRepository;

import com.crosshub.temu.repository.TemuShopRepository;

import com.crosshub.temu.repository.UserMenuGrantRepository;

import com.crosshub.temu.repository.UserPlatformScopeRepository;

import com.crosshub.temu.repository.UserShopScopeRepository;

import org.springframework.http.HttpStatus;

import org.springframework.stereotype.Service;

import org.springframework.transaction.annotation.Transactional;

import org.springframework.web.server.ResponseStatusException;



import java.util.ArrayList;

import java.util.HashSet;

import java.util.LinkedHashSet;

import java.util.List;

import java.util.Locale;

import java.util.Set;

import java.util.regex.Matcher;

import java.util.regex.Pattern;



@Service

public class MemberScopeService {

    private static final Pattern DEMO_SHOP_PATTERN = Pattern.compile("^demo_([a-z0-9]+)_");



    private final UserPlatformScopeRepository platformScopeRepository;

    private final UserShopScopeRepository shopScopeRepository;

    private final UserMenuGrantRepository menuGrantRepository;

    private final TemuShopRepository temuShopRepository;

    private final SysMenuRepository menuRepository;



    public MemberScopeService(

            UserPlatformScopeRepository platformScopeRepository,

            UserShopScopeRepository shopScopeRepository,

            UserMenuGrantRepository menuGrantRepository,

            TemuShopRepository temuShopRepository,

            SysMenuRepository menuRepository

    ) {

        this.platformScopeRepository = platformScopeRepository;

        this.shopScopeRepository = shopScopeRepository;

        this.menuGrantRepository = menuGrantRepository;

        this.temuShopRepository = temuShopRepository;

        this.menuRepository = menuRepository;

    }



    public List<String> platformsForMember(Long tenantId, Long userId) {

        return platformScopeRepository.findByTenantIdAndUserId(tenantId, userId).stream()

                .map(scope -> scope.getPlatform().toLowerCase(Locale.ROOT))

                .distinct()

                .toList();

    }



    public List<String> shopIdsForMember(Long tenantId, Long userId) {

        return shopScopeRepository.findByTenantIdAndUserId(tenantId, userId).stream()

                .map(UserShopScope::getShopId)

                .distinct()

                .toList();

    }



    public List<String> menuCodesForMember(Long tenantId, Long userId) {

        return menuGrantRepository.findByTenantIdAndUserId(tenantId, userId).stream()

                .map(UserMenuGrant::getMenuCode)

                .distinct()

                .toList();

    }



    @Transactional

    public void replaceScopes(

            Long tenantId,

            Long userId,

            List<String> platforms,

            List<String> shopIds,

            List<String> menuCodes,

            boolean updateMenuCodes

    ) {

        List<String> normalizedPlatforms = normalizePlatforms(platforms);

        if (normalizedPlatforms.isEmpty()) {

            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "请至少选择一个负责平台");

        }



        platformScopeRepository.deleteByTenantIdAndUserId(tenantId, userId);

        shopScopeRepository.deleteByTenantIdAndUserId(tenantId, userId);



        for (String platform : normalizedPlatforms) {

            UserPlatformScope scope = new UserPlatformScope();

            scope.setTenantId(tenantId);

            scope.setUserId(userId);

            scope.setPlatform(platform);

            platformScopeRepository.save(scope);

        }



        Set<String> platformSet = new HashSet<>(normalizedPlatforms);

        for (String shopId : normalizeShopIds(shopIds)) {

            String platform = resolveShopPlatform(tenantId, shopId, platformSet);

            UserShopScope scope = new UserShopScope();

            scope.setTenantId(tenantId);

            scope.setUserId(userId);

            scope.setPlatform(platform);

            scope.setShopId(shopId);

            shopScopeRepository.save(scope);

        }



        if (updateMenuCodes) {

            replaceMenuGrants(tenantId, userId, menuCodes == null ? List.of() : menuCodes);

        }

    }



    @Transactional
    public void deleteAllScopes(Long tenantId, Long userId) {
        platformScopeRepository.deleteByTenantIdAndUserId(tenantId, userId);
        shopScopeRepository.deleteByTenantIdAndUserId(tenantId, userId);
        menuGrantRepository.deleteByTenantIdAndUserId(tenantId, userId);
    }

    @Transactional
    public void replaceMenuGrants(Long tenantId, Long userId, List<String> menuCodes) {

        menuGrantRepository.deleteByTenantIdAndUserId(tenantId, userId);

        if (menuCodes == null || menuCodes.isEmpty()) {

            return;

        }



        Set<String> allowed = assignableEmployeeMenuCodes();
        for (String code : menuCodes) {
            String normalized = normalizeMenuCode(code);
            if (normalized.isBlank()) continue;
            if (!allowed.contains(normalized)) {
                throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "无效的菜单编码: " + normalized);
            }
            String canonicalCode = menuRepository.findByPortalOrderBySortOrderAsc("employee").stream()
                    .filter(menu -> "module".equals(menu.getMenuType()))
                    .filter(menu -> menu.getCode().equalsIgnoreCase(normalized))
                    .map(menu -> menu.getCode())
                    .findFirst()
                    .orElse(normalized);
            UserMenuGrant grant = new UserMenuGrant();
            grant.setTenantId(tenantId);
            grant.setUserId(userId);
            grant.setMenuCode(canonicalCode);
            menuGrantRepository.save(grant);
        }

    }



    public Set<String> assignableEmployeeMenuCodes() {

        return menuRepository.findByPortalOrderBySortOrderAsc("employee").stream()

                .filter(menu -> "module".equals(menu.getMenuType()))

                .map(menu -> menu.getCode().toLowerCase(Locale.ROOT))

                .collect(LinkedHashSet::new, Set::add, Set::addAll);

    }



    private List<String> normalizePlatforms(List<String> platforms) {

        if (platforms == null) return List.of();

        LinkedHashSet<String> normalized = new LinkedHashSet<>();

        for (String platform : platforms) {

            if (platform == null || platform.isBlank()) continue;

            normalized.add(platform.trim().toLowerCase(Locale.ROOT));

        }

        return new ArrayList<>(normalized);

    }



    private List<String> normalizeShopIds(List<String> shopIds) {

        if (shopIds == null) return List.of();

        LinkedHashSet<String> normalized = new LinkedHashSet<>();

        for (String shopId : shopIds) {

            if (shopId == null || shopId.isBlank()) continue;

            normalized.add(shopId.trim());

        }

        return new ArrayList<>(normalized);

    }



    private String normalizeMenuCode(String code) {

        return code == null ? "" : code.trim().toLowerCase(Locale.ROOT);

    }



    private String resolveShopPlatform(Long tenantId, String shopId, Set<String> allowedPlatforms) {

        boolean temuShop = temuShopRepository.findById(shopId)

                .filter(shop -> tenantId.equals(shop.getTenantId()))

                .isPresent();

        if (temuShop) {

            if (!allowedPlatforms.contains("temu")) {

                throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "店铺 " + shopId + " 不属于已选平台");

            }

            return "temu";

        }



        Matcher matcher = DEMO_SHOP_PATTERN.matcher(shopId.toLowerCase(Locale.ROOT));

        if (matcher.find()) {

            String platform = matcher.group(1);

            if (!allowedPlatforms.contains(platform)) {

                throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "店铺 " + shopId + " 不属于已选平台");

            }

            return platform;

        }



        throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "无法识别店铺所属平台: " + shopId);

    }

}

