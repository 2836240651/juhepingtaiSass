package com.crosshub.platform.controller;

import com.crosshub.platform.service.PlatformAccountService;
import com.crosshub.platform.dto.BatchBindRequest;
import com.crosshub.platform.dto.BindRequest;
import com.crosshub.platform.dto.StorePayload;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/platform-accounts")
public class PlatformAccountController {
    private final PlatformAccountService platformAccountService;

    public PlatformAccountController(PlatformAccountService platformAccountService) {
        this.platformAccountService = platformAccountService;
    }

    @GetMapping
    public Map<String, Object> list(@RequestParam(value = "platform", required = false) String platform) {
        return Map.of("success", true, "data", platformAccountService.list(platform));
    }

    @PostMapping("/bind")
    public Map<String, Object> bind(@RequestBody BindRequest request) {
        var data = platformAccountService.upsert(new StorePayload(
                request.id(),
                request.platform(),
                request.storeName(),
                request.account(),
                request.password(),
                request.companyName(),
                request.externalShopId()
        ));
        return Map.of(
                "success", true,
                "message", request.id() != null && !request.id().isBlank() ? "店铺更新成功" : "店铺绑定成功",
                "data", data
        );
    }

    @PostMapping("/bind-batch")
    public Map<String, Object> bindBatch(@RequestBody BatchBindRequest request) {
        List<Map<String, Object>> data = platformAccountService.upsertBatch(
                request.companyName(),
                request.stores() == null ? List.of() : request.stores().stream()
                        .map(item -> new StorePayload(
                                item.id(),
                                item.platform(),
                                item.storeName(),
                                item.account(),
                                item.password(),
                                request.companyName(),
                                item.externalShopId()
                        ))
                        .toList()
        );
        return Map.of(
                "success", true,
                "message", "成功绑定/更新 " + data.size() + " 个店铺",
                "data", data
        );
    }

    @DeleteMapping("/{id}")
    public Map<String, Object> delete(@PathVariable String id) {
        var data = platformAccountService.delete(id);
        return Map.of("success", true, "message", "店铺已解除绑定", "data", data);
    }
}
