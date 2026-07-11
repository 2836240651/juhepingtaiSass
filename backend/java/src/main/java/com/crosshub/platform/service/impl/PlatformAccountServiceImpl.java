package com.crosshub.platform.service.impl;

import com.crosshub.common.DemoDataFilter;
import com.crosshub.platform.service.PlatformAccountService;
import com.crosshub.temu.mapper.TemuMapper;
import com.crosshub.platform.dto.StorePayload;

import com.crosshub.platform.entity.PlatformAccount;
import com.crosshub.temu.entity.TemuShop;
import com.crosshub.platform.repository.PlatformAccountRepository;
import com.crosshub.temu.repository.TemuShopRepository;
import com.crosshub.security.AuthContext;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

@Service
public class PlatformAccountServiceImpl implements PlatformAccountService {
    private static final DateTimeFormatter BOUND_AT = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
    private static final List<String> ALLOWED_PLATFORMS = List.of(
            "temu", "aliexpress", "1688", "amazon", "walmart", "pdd", "douyin", "channels", "shopify", "wordpress", "dtc"
    );

    private final PlatformAccountRepository repository;
    private final AuthContext authContext;
    private final TemuMapper temuMapper;
    private final TemuShopRepository temuShopRepository;

    public PlatformAccountServiceImpl(
            PlatformAccountRepository repository,
            AuthContext authContext,
            TemuMapper temuMapper,
            TemuShopRepository temuShopRepository
    ) {
        this.repository = repository;
        this.authContext = authContext;
        this.temuMapper = temuMapper;
        this.temuShopRepository = temuShopRepository;
    }

    public List<Map<String, Object>> list(String platform) {
        Long tenantId = requireTenant();
        List<PlatformAccount> rows = platform == null || platform.isBlank()
                ? repository.findByTenantIdOrderByBoundAtDesc(tenantId)
                : repository.findByTenantIdAndPlatformOrderByBoundAtDesc(tenantId, normalizePlatform(platform));
        return rows.stream().map(temuMapper::toPlatformAccountDto).toList();
    }

    @Transactional
    public Map<String, Object> upsert(StorePayload payload) {
        Long tenantId = requireTenant();
        String platform = normalizePlatform(payload.platform());
        validatePlatform(platform);

        String storeName = trim(payload.storeName());
        String account = trim(payload.account());
        String password = payload.password() == null ? "" : payload.password();
        String id = trim(payload.id());

        if (storeName.isBlank()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "店铺名称不能为空");
        }
        if (account.isBlank()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "登录账号不能为空");
        }
        if (id.isBlank() && password.isBlank()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "登录密码不能为空");
        }

        PlatformAccount row;
        if (!id.isBlank()) {
            row = repository.findByIdAndTenantId(id, tenantId)
                    .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "店铺不存在"));
            if (!platform.equalsIgnoreCase(row.getPlatform())) {
                throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "不允许修改店铺所属平台");
            }
            if (repository.existsByTenantIdAndPlatformIgnoreCaseAndStoreNameIgnoreCaseAndIdNot(
                    tenantId, platform, storeName, id)) {
                throw new ResponseStatusException(HttpStatus.CONFLICT, "该平台下已存在同名店铺");
            }
            row.setStoreName(storeName);
            row.setAccount(account);
            if (!password.isBlank()) {
                row.setPassword(password);
            }
        } else {
            if (repository.existsByTenantIdAndPlatformIgnoreCaseAndStoreNameIgnoreCase(tenantId, platform, storeName)) {
                throw new ResponseStatusException(HttpStatus.CONFLICT, "该平台下已存在名为「" + storeName + "」的店铺");
            }
            row = new PlatformAccount();
            row.setId(UUID.randomUUID().toString());
            row.setTenantId(tenantId);
            row.setPlatform(platform);
            row.setStoreName(storeName);
            row.setAccount(account);
            row.setPassword(password);
        }

        row.setCompanyName(trim(payload.companyName()));
        row.setExternalShopId(resolveExternalShopId(tenantId, platform, storeName, account, trim(payload.externalShopId())));
        row.setBoundAt(BOUND_AT.format(LocalDateTime.now()));
        repository.save(row);
        return temuMapper.toPlatformAccountDto(row);
    }

    @Transactional
    public List<Map<String, Object>> upsertBatch(String companyName, List<StorePayload> stores) {
        if (stores == null || stores.isEmpty()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "请至少提交一个店铺");
        }
        return stores.stream()
                .map(item -> upsert(new StorePayload(
                        item.id(),
                        item.platform(),
                        item.storeName(),
                        item.account(),
                        item.password(),
                        companyName != null && !companyName.isBlank() ? companyName : item.companyName(),
                        item.externalShopId()
                )))
                .toList();
    }

    @Transactional
    public Map<String, Object> delete(String id) {
        Long tenantId = requireTenant();
        PlatformAccount row = repository.findByIdAndTenantId(id, tenantId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "店铺不存在"));
        repository.delete(row);
        return temuMapper.toPlatformAccountDto(row);
    }

    @Transactional
    public int autoLinkTemuShops(Long tenantId) {
        if (tenantId == null) {
            return 0;
        }
        List<PlatformAccount> accounts = repository.findByTenantIdAndPlatformOrderByBoundAtDesc(tenantId, "temu");
        List<TemuShop> shops = temuShopRepository.findByTenantId(tenantId);
        if (shops.isEmpty() || accounts.isEmpty()) {
            return 0;
        }

        Set<String> usedShopIds = new HashSet<>();
        for (PlatformAccount account : accounts) {
            String linkedId = trim(account.getExternalShopId());
            if (!linkedId.isBlank()) {
                usedShopIds.add(linkedId);
            }
        }

        int linked = 0;
        for (PlatformAccount account : accounts) {
            if (!trim(account.getExternalShopId()).isBlank()) {
                continue;
            }
            String shopId = matchShopId(account, shops, usedShopIds);
            if (shopId.isBlank()) {
                continue;
            }
            account.setExternalShopId(shopId);
            repository.save(account);
            usedShopIds.add(shopId);
            linked++;
        }

        List<PlatformAccount> stillUnlinked = accounts.stream()
                .filter(account -> trim(account.getExternalShopId()).isBlank())
                .toList();
        List<TemuShop> availableShops = shops.stream()
                .filter(shop -> !usedShopIds.contains(shop.getShopId()))
                .toList();
        if (stillUnlinked.size() == 1 && availableShops.size() == 1) {
            PlatformAccount account = stillUnlinked.get(0);
            account.setExternalShopId(availableShops.get(0).getShopId());
            repository.save(account);
            linked++;
        }
        return linked;
    }

    private String matchShopId(PlatformAccount account, List<TemuShop> shops, Set<String> usedShopIds) {
        String storeName = trim(account.getStoreName());
        String loginAccount = trim(account.getAccount());
        for (TemuShop shop : shops) {
            if (DemoDataFilter.isDemoShopId(shop.getShopId())) {
                continue;
            }
            if (usedShopIds.contains(shop.getShopId())) {
                continue;
            }
            String shopName = trim(shop.getShopName());
            if (!storeName.isBlank() && !shopName.isBlank() && storeName.equalsIgnoreCase(shopName)) {
                return shop.getShopId();
            }
        }
        for (TemuShop shop : shops) {
            if (DemoDataFilter.isDemoShopId(shop.getShopId())) {
                continue;
            }
            if (usedShopIds.contains(shop.getShopId())) {
                continue;
            }
            String shopName = trim(shop.getShopName());
            if (!storeName.isBlank() && !shopName.isBlank()
                    && (storeName.contains(shopName) || shopName.contains(storeName))) {
                return shop.getShopId();
            }
        }
        for (TemuShop shop : shops) {
            if (DemoDataFilter.isDemoShopId(shop.getShopId())) {
                continue;
            }
            if (usedShopIds.contains(shop.getShopId())) {
                continue;
            }
            String shopId = shop.getShopId();
            String shopName = trim(shop.getShopName());
            if (!loginAccount.isBlank()
                    && (loginAccount.equalsIgnoreCase(shopId) || loginAccount.equalsIgnoreCase(shopName))) {
                return shopId;
            }
        }
        return "";
    }

    private Long requireTenant() {
        Long tenantId = authContext.tenantId();
        if (tenantId == null) {
            throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "缺少租户上下文");
        }
        return tenantId;
    }

    private void validatePlatform(String platform) {
        if (!ALLOWED_PLATFORMS.contains(platform)) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "不支持的平台: " + platform);
        }
    }

    private String normalizePlatform(String platform) {
        return String.valueOf(platform == null ? "" : platform).trim().toLowerCase(Locale.ROOT);
    }

    private String trim(String value) {
        return value == null ? "" : value.trim();
    }

    private String resolveExternalShopId(Long tenantId, String platform, String storeName, String account, String explicit) {
        if (explicit != null && !explicit.isBlank()) {
            return explicit.trim();
        }
        if (!"temu".equals(platform)) {
            return "";
        }
        List<TemuShop> shops = temuShopRepository.findByTenantId(tenantId);
        if (shops.isEmpty()) {
            return "";
        }
        Set<String> used = new HashSet<>();
        for (PlatformAccount bound : repository.findByTenantIdAndPlatformOrderByBoundAtDesc(tenantId, "temu")) {
            String linkedId = trim(bound.getExternalShopId());
            if (!linkedId.isBlank()) {
                used.add(linkedId);
            }
        }
        PlatformAccount probe = new PlatformAccount();
        probe.setStoreName(storeName);
        probe.setAccount(account);
        String matched = matchShopId(probe, shops, used);
        if (!matched.isBlank()) {
            return matched;
        }
        if (shops.size() == 1) {
            return shops.get(0).getShopId();
        }
        return "";
    }

}
