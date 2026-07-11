package com.crosshub.tenant.service.impl;

import com.crosshub.common.DemoDataFilter;
import com.crosshub.tenant.service.DataScopeService;

import com.crosshub.temu.entity.TemuSale;
import com.crosshub.temu.entity.TemuShop;
import com.crosshub.warehouse.entity.WarehouseSite;
import com.crosshub.temu.repository.TemuSaleRepository;
import com.crosshub.temu.repository.TemuShopRepository;
import com.crosshub.tenant.repository.UserPlatformScopeRepository;
import com.crosshub.tenant.repository.UserShopScopeRepository;
import com.crosshub.warehouse.repository.UserWarehouseScopeRepository;
import com.crosshub.warehouse.repository.WarehouseSiteRepository;
import com.crosshub.security.AuthContext;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.stream.Collectors;

@Service
public class DataScopeServiceImpl implements DataScopeService {
    private final AuthContext authContext;
    private final TemuShopRepository shopRepository;
    private final TemuSaleRepository saleRepository;
    private final UserPlatformScopeRepository platformScopeRepository;
    private final UserShopScopeRepository shopScopeRepository;
    private final UserWarehouseScopeRepository warehouseScopeRepository;
    private final WarehouseSiteRepository warehouseSiteRepository;

    public DataScopeServiceImpl(
            AuthContext authContext,
            TemuShopRepository shopRepository,
            TemuSaleRepository saleRepository,
            UserPlatformScopeRepository platformScopeRepository,
            UserShopScopeRepository shopScopeRepository,
            UserWarehouseScopeRepository warehouseScopeRepository,
            WarehouseSiteRepository warehouseSiteRepository
    ) {
        this.authContext = authContext;
        this.shopRepository = shopRepository;
        this.saleRepository = saleRepository;
        this.platformScopeRepository = platformScopeRepository;
        this.shopScopeRepository = shopScopeRepository;
        this.warehouseScopeRepository = warehouseScopeRepository;
        this.warehouseSiteRepository = warehouseSiteRepository;
    }

    public Long requireTenantId() {
        Long tenantId = authContext.tenantId();
        if (tenantId == null) {
            throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "缺少租户上下文");
        }
        return tenantId;
    }

    public List<TemuShop> scopedShops() {
        Long tenantId = requireTenantId();
        List<TemuShop> shops = DemoDataFilter.filterDemoShops(
                shopRepository.findByTenantId(tenantId),
                TemuShop::getShopId
        );
        if (authContext.isBossPortal() || authContext.isAdmin()) {
            return shops;
        }
        return filterShopsForEmployee(tenantId, shops);
    }

    public List<TemuSale> scopedSales(String reportTime, String shopId) {
        Long tenantId = requireTenantId();
        Set<String> allowedShopIds = scopedShops().stream()
                .map(TemuShop::getShopId)
                .collect(Collectors.toSet());

        if (allowedShopIds.isEmpty()) {
            return List.of();
        }

        if (shopId != null && !shopId.isBlank() && !"all".equalsIgnoreCase(shopId)) {
            if (!allowedShopIds.contains(shopId) || DemoDataFilter.isDemoShopId(shopId)) {
                throw new ResponseStatusException(HttpStatus.FORBIDDEN, "无权访问该店铺数据");
            }
            return saleRepository.findByTenantIdAndReportTimeAndShopId(tenantId, reportTime, shopId).stream()
                    .filter(sale -> !DemoDataFilter.isDemoSku(sale.getExtCode()))
                    .toList();
        }

        return saleRepository.findByTenantIdAndReportTimeAndShopIdIn(
                        tenantId, reportTime, List.copyOf(allowedShopIds)).stream()
                .filter(sale -> !DemoDataFilter.isDemoSku(sale.getExtCode()))
                .toList();
    }

    public String latestReportTime() {
        return saleRepository.findLatestReportTimeByTenantId(requireTenantId());
    }

    public List<String> resolveScopeForLogin(Long tenantId, Long userId, boolean bossPortal) {
        if (bossPortal) {
            return List.of();
        }
        return shopScopeRepository.findByTenantIdAndUserId(tenantId, userId).stream()
                .map(scope -> scope.getShopId())
                .distinct()
                .toList();
    }

    public List<String> resolvePlatformsForLogin(Long tenantId, Long userId, boolean bossPortal) {
        if (bossPortal) {
            return List.of();
        }
        return platformScopeRepository.findByTenantIdAndUserId(tenantId, userId).stream()
                .map(scope -> scope.getPlatform().toLowerCase(Locale.ROOT))
                .distinct()
                .toList();
    }

    public List<String> resolveWarehouseScopeForLogin(Long tenantId, Long userId, String portalRole) {
        if (!"warehouse".equalsIgnoreCase(portalRole)) {
            return List.of();
        }
        return warehouseScopeRepository.findByTenantIdAndUserId(tenantId, userId).stream()
                .map(scope -> scope.getWarehouseId())
                .distinct()
                .toList();
    }

    public List<String> resolveWarehouseScopeNamesForLogin(Long tenantId, Long userId, String portalRole) {
        if (!"warehouse".equalsIgnoreCase(portalRole)) {
            return List.of();
        }
        Set<String> allowed = new HashSet<>(resolveWarehouseScopeForLogin(tenantId, userId, portalRole));
        if (allowed.isEmpty()) {
            return List.of();
        }
        return warehouseSiteRepository.findByTenantIdOrderBySortOrderAscNameAsc(tenantId).stream()
                .filter(site -> allowed.contains(site.getId()))
                .map(WarehouseSite::getName)
                .toList();
    }

    private List<TemuShop> filterShopsForEmployee(Long tenantId, List<TemuShop> shops) {
        Long userId = authContext.userId();
        if (userId == null) {
            return List.of();
        }

        List<String> assignedShopIds = shopScopeRepository.findByTenantIdAndUserId(tenantId, userId).stream()
                .map(scope -> scope.getShopId())
                .toList();
        if (!assignedShopIds.isEmpty()) {
            Set<String> allowed = new HashSet<>(assignedShopIds);
            return shops.stream().filter(shop -> allowed.contains(shop.getShopId())).toList();
        }

        Set<String> platforms = platformScopeRepository.findByTenantIdAndUserId(tenantId, userId).stream()
                .map(scope -> scope.getPlatform().toLowerCase(Locale.ROOT))
                .collect(Collectors.toSet());
        if (platforms.isEmpty()) {
            return List.of();
        }
        if (platforms.contains("temu")) {
            return shops;
        }
        return List.of();
    }
}
