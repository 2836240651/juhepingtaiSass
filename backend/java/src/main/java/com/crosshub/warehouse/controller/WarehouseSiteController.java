package com.crosshub.warehouse.controller;

import com.crosshub.common.StatusRequest;
import com.crosshub.warehouse.dto.SitePayload;
import com.crosshub.warehouse.service.WarehouseSiteService;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/warehouse")
public class WarehouseSiteController {
    private final WarehouseSiteService siteService;

    public WarehouseSiteController(WarehouseSiteService siteService) {
        this.siteService = siteService;
    }

    @GetMapping("/sites")
    public Map<String, Object> listSites(@RequestParam(value = "activeOnly", defaultValue = "false") boolean activeOnly) {
        return Map.of("code", 0, "data", siteService.listSites(activeOnly));
    }

    @PostMapping("/sites")
    public Map<String, Object> createSite(@RequestBody SitePayload request) {
        return Map.of("code", 0, "data", siteService.createSite(request));
    }

    @PutMapping("/sites/{id}")
    public Map<String, Object> updateSite(@PathVariable("id") String id, @RequestBody SitePayload request) {
        return Map.of("code", 0, "data", siteService.updateSite(id, request));
    }

    @PatchMapping("/sites/{id}/status")
    public Map<String, Object> updateStatus(@PathVariable("id") String id, @RequestBody StatusRequest request) {
        return Map.of("code", 0, "data", siteService.updateStatus(id, request.status()));
    }

    @DeleteMapping("/sites/{id}")
    public Map<String, Object> deleteSite(@PathVariable("id") String id) {
        siteService.deleteSite(id);
        return Map.of("code", 0, "data", true);
    }
}
