package com.crosshub.temu.web;

import com.crosshub.temu.entity.TemuShop;
import com.crosshub.temu.service.TemuOperationalService;
import org.springframework.web.bind.annotation.*;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/temu")
public class TemuController {
    private final TemuOperationalService operationalService;

    public TemuController(TemuOperationalService operationalService) {
        this.operationalService = operationalService;
    }

    @GetMapping("/shops")
    public Map<String, Object> shops() {
        List<Map<String, Object>> list = operationalService.shops().stream().map(shop -> {
            Map<String, Object> item = new LinkedHashMap<>();
            item.put("shop_id", shop.getShopId());
            item.put("shop_name", shop.getShopName());
            item.put("is_upload", shop.isUpload());
            return item;
        }).toList();
        return Map.of("code", 0, "data", list);
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
}
