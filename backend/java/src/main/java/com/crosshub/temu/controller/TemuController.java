package com.crosshub.temu.controller;



import com.crosshub.common.ApiResult;

import com.crosshub.platform.entity.PlatformAccount;

import com.crosshub.temu.entity.TemuShop;

import com.crosshub.temu.mapper.TemuMapper;

import com.crosshub.platform.repository.PlatformAccountRepository;

import com.crosshub.security.AuthContext;

import com.crosshub.temu.dto.TemuCompetitorDiscoverRequest;
import com.crosshub.temu.service.TemuCompetitorService;
import com.crosshub.temu.service.TemuHotBroadcastService;
import com.crosshub.temu.service.TemuOperationalService;
import com.crosshub.temu.service.TemuRestockStatusService;
import com.crosshub.temu.service.TemuSessionService;

import org.springframework.web.bind.annotation.*;



import java.util.HashMap;

import java.util.LinkedHashMap;

import java.util.List;

import java.util.Map;



@RestController

@RequestMapping("/api/temu")

public class TemuController {

    private final TemuOperationalService operationalService;

    private final TemuRestockStatusService restockStatusService;

    private final TemuHotBroadcastService hotBroadcastService;

    private final TemuSessionService sessionService;

    private final TemuCompetitorService competitorService;

    private final TemuMapper temuMapper;

    private final PlatformAccountRepository platformAccountRepository;

    private final AuthContext authContext;



    public TemuController(

            TemuOperationalService operationalService,

            TemuRestockStatusService restockStatusService,

            TemuHotBroadcastService hotBroadcastService,

            TemuSessionService sessionService,

            TemuCompetitorService competitorService,

            TemuMapper temuMapper,

            PlatformAccountRepository platformAccountRepository,

            AuthContext authContext

    ) {

        this.operationalService = operationalService;

        this.restockStatusService = restockStatusService;

        this.hotBroadcastService = hotBroadcastService;

        this.sessionService = sessionService;

        this.competitorService = competitorService;

        this.temuMapper = temuMapper;

        this.platformAccountRepository = platformAccountRepository;

        this.authContext = authContext;

    }



    @GetMapping("/shops")

    public Map<String, Object> shops() {

        Map<String, PlatformAccount> boundByExternalShopId = loadBoundTemuAccountsByExternalShopId();

        List<Map<String, Object>> items = operationalService.shops().stream()

                .map(shop -> enrichShopDto(shop, boundByExternalShopId))

                .toList();

        return ApiResult.ok(items);

    }



    @GetMapping("/session")
    public Map<String, Object> session() {
        return ApiResult.ok(sessionService.getSessionStatus());
    }

    @PostMapping("/login/open")
    public Map<String, Object> openLogin() {
        return ApiResult.ok(sessionService.openLoginWindow());
    }

    @PostMapping("/competitors/discover")
    public Map<String, Object> discoverCompetitors(@RequestBody(required = false) TemuCompetitorDiscoverRequest request) {
        return ApiResult.ok(competitorService.discoverCandidates(request));
    }

    @GetMapping("/operational")

    public Map<String, Object> operational(

            @RequestParam(value = "shop_id", required = false) String shopId,

            @RequestParam(value = "report_time", required = false) String reportTime

    ) {

        return operationalService.operationalBundle(shopId, reportTime);

    }



    @GetMapping("/trend")

    public Map<String, Object> trend(

            @RequestParam(value = "shop_id", required = false) String shopId,

            @RequestParam(value = "days", defaultValue = "7") int days

    ) {

        return operationalService.salesTrend(shopId, days);

    }



    @GetMapping("/restock-status")

    public Map<String, Object> listRestockStatus() {

        return ApiResult.ok(restockStatusService.listAll());

    }



    @PutMapping("/restock-status")

    public Map<String, Object> upsertRestockStatus(@RequestBody Map<String, Object> payload) {

        return ApiResult.ok(restockStatusService.upsert(payload));

    }



    @GetMapping("/hot-broadcasts")

    public Map<String, Object> listHotBroadcasts() {

        return ApiResult.ok(hotBroadcastService.listBroadcasts());

    }



    @PostMapping("/hot-broadcasts")

    public Map<String, Object> createHotBroadcast(@RequestBody Map<String, Object> payload) {

        return ApiResult.ok(hotBroadcastService.createBroadcast(payload));

    }



    @PostMapping("/hot-broadcasts/{id}/read")

    public Map<String, Object> markHotBroadcastRead(

            @PathVariable String id,

            @RequestBody(required = false) Map<String, Object> payload

    ) {

        return ApiResult.ok(hotBroadcastService.markRead(id, payload == null ? Map.of() : payload));

    }



    private Map<String, PlatformAccount> loadBoundTemuAccountsByExternalShopId() {

        Long tenantId = authContext.tenantId();

        if (tenantId == null) {

            return Map.of();

        }

        List<PlatformAccount> bound = platformAccountRepository.findByTenantIdAndPlatformOrderByBoundAtDesc(tenantId, "temu");

        Map<String, PlatformAccount> map = new HashMap<>();

        for (PlatformAccount account : bound) {

            String externalShopId = account.getExternalShopId();

            if (externalShopId == null || externalShopId.isBlank()) {

                continue;

            }

            map.put(externalShopId.trim(), account);

        }

        return map;

    }



    private Map<String, Object> enrichShopDto(TemuShop shop, Map<String, PlatformAccount> boundByExternalShopId) {

        Map<String, Object> dto = new LinkedHashMap<>(temuMapper.toShopDto(shop));

        PlatformAccount account = boundByExternalShopId.get(shop.getShopId());

        if (account != null) {

            dto.put("platform_account_id", account.getId());

            dto.put("bound_store_name", account.getStoreName());

            dto.put("external_shop_id", account.getExternalShopId());

        }

        return dto;

    }

}


