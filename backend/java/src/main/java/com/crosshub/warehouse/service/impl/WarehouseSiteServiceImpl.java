package com.crosshub.warehouse.service.impl;

import com.crosshub.warehouse.service.WarehouseSiteService;
import com.crosshub.warehouse.dto.SitePayload;

import com.crosshub.warehouse.entity.WarehouseSite;
import com.crosshub.warehouse.repository.WarehouseSiteRepository;
import com.crosshub.security.AuthContext;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

@Service
public class WarehouseSiteServiceImpl implements WarehouseSiteService {
    private static final DateTimeFormatter CREATED_AT = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

    private final WarehouseSiteRepository siteRepository;
    private final AuthContext authContext;
    private final JdbcTemplate jdbc;

    public WarehouseSiteServiceImpl(
            WarehouseSiteRepository siteRepository,
            AuthContext authContext,
            JdbcTemplate jdbc
    ) {
        this.siteRepository = siteRepository;
        this.authContext = authContext;
        this.jdbc = jdbc;
    }

    public List<Map<String, Object>> listSites(boolean activeOnly) {
        Long tenantId = requireTenant();
        List<WarehouseSite> sites = activeOnly
                ? siteRepository.findByTenantIdAndStatusOrderBySortOrderAscNameAsc(tenantId, "active")
                : siteRepository.findByTenantIdOrderBySortOrderAscNameAsc(tenantId);
        return sites.stream().map(this::toDto).toList();
    }

    @Transactional
    public Map<String, Object> createSite(SitePayload payload) {
        requireBossPortal();
        Long tenantId = requireTenant();
        validateSitePayload(payload, true);

        String code = normalizeCode(payload.code());
        if (siteRepository.existsByTenantIdAndCodeIgnoreCase(tenantId, code)) {
            throw badRequest("仓库编码已存在");
        }

        WarehouseSite site = new WarehouseSite();
        site.setId("wh_site_" + System.currentTimeMillis() + "_" + randomSuffix());
        site.setTenantId(tenantId);
        site.setName(trim(payload.name()));
        site.setCode(code);
        site.setAddress(trim(payload.address()));
        site.setStatus(payload.status() == null || payload.status() ? "active" : "inactive");
        site.setSortOrder(payload.sortOrder() == null ? 0 : payload.sortOrder());
        site.setCreatedAt(CREATED_AT.format(LocalDateTime.now()));
        siteRepository.save(site);
        return toDto(site);
    }

    @Transactional
    public Map<String, Object> updateSite(String id, SitePayload payload) {
        requireBossPortal();
        Long tenantId = requireTenant();
        WarehouseSite site = requireSite(tenantId, id);
        validateSitePayload(payload, false);

        if (payload.name() != null) site.setName(trim(payload.name()));
        if (payload.code() != null) {
            String code = normalizeCode(payload.code());
            if (siteRepository.existsByTenantIdAndCodeIgnoreCaseAndIdNot(tenantId, code, id)) {
                throw badRequest("仓库编码已存在");
            }
            site.setCode(code);
        }
        if (payload.address() != null) site.setAddress(trim(payload.address()));
        if (payload.status() != null) site.setStatus(payload.status() ? "active" : "inactive");
        if (payload.sortOrder() != null) site.setSortOrder(payload.sortOrder());
        siteRepository.save(site);
        return toDto(site);
    }

    @Transactional
    public Map<String, Object> updateStatus(String id, boolean active) {
        requireBossPortal();
        Long tenantId = requireTenant();
        WarehouseSite site = requireSite(tenantId, id);
        site.setStatus(active ? "active" : "inactive");
        siteRepository.save(site);
        return toDto(site);
    }

    @Transactional
    public void deleteSite(String id) {
        requireBossPortal();
        Long tenantId = requireTenant();
        requireSite(tenantId, id);

        Integer orderCount = jdbc.queryForObject(
                "SELECT COUNT(*) FROM warehouse_order WHERE tenant_id = ? AND warehouse_id = ?",
                Integer.class,
                tenantId,
                id
        );
        if (orderCount != null && orderCount > 0) {
            throw badRequest("该仓库已有出库单，无法删除");
        }

        siteRepository.deleteById(id);
    }

    public WarehouseSite requireActiveSite(Long tenantId, String warehouseId) {
        WarehouseSite site = requireSite(tenantId, warehouseId);
        if (!site.isActive()) {
            throw badRequest("目标仓库已停用");
        }
        return site;
    }

    public WarehouseSite requireSite(Long tenantId, String warehouseId) {
        if (warehouseId == null || warehouseId.isBlank()) {
            throw badRequest("请选择出库仓库");
        }
        return siteRepository.findByIdAndTenantId(warehouseId.trim(), tenantId)
                .orElseThrow(() -> badRequest("仓库不存在"));
    }

    private Map<String, Object> toDto(WarehouseSite site) {
        Map<String, Object> item = new LinkedHashMap<>();
        item.put("id", site.getId());
        item.put("name", site.getName());
        item.put("code", site.getCode());
        item.put("address", site.getAddress() == null ? "" : site.getAddress());
        item.put("status", site.isActive());
        item.put("sortOrder", site.getSortOrder());
        item.put("createdAt", site.getCreatedAt());
        return item;
    }

    private void validateSitePayload(SitePayload payload, boolean creating) {
        if (creating || payload.name() != null) {
            if (trim(payload.name()).isBlank()) {
                throw badRequest("请填写仓库名称");
            }
        }
        if (creating || payload.code() != null) {
            if (normalizeCode(payload.code()).isBlank()) {
                throw badRequest("请填写仓库编码");
            }
        }
    }

    private String normalizeCode(String code) {
        return trim(code).toLowerCase(Locale.ROOT);
    }

    private String trim(String value) {
        return value == null ? "" : value.trim();
    }

    private String randomSuffix() {
        return Long.toHexString(Double.doubleToLongBits(Math.random())).substring(0, 6);
    }

    private Long requireTenant() {
        Long tenantId = authContext.tenantId();
        if (tenantId == null) {
            throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "未登录");
        }
        return tenantId;
    }

    private void requireBossPortal() {
        if (!authContext.isBossPortal() || !authContext.isAdmin()) {
            throw new ResponseStatusException(HttpStatus.FORBIDDEN, "仅企业管理员可管理仓库");
        }
    }

    private ResponseStatusException badRequest(String message) {
        return new ResponseStatusException(HttpStatus.BAD_REQUEST, message);
    }

}
