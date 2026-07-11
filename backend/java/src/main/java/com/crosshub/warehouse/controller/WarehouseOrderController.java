package com.crosshub.warehouse.controller;

import com.crosshub.warehouse.service.WarehouseOrderService;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/warehouse")
public class WarehouseOrderController {
    private final WarehouseOrderService orderService;

    public WarehouseOrderController(WarehouseOrderService orderService) {
        this.orderService = orderService;
    }

    @GetMapping("/orders")
    public Map<String, Object> list() {
        return Map.of("code", 0, "data", orderService.listOrders());
    }

    @GetMapping("/orders/{id}")
    public Map<String, Object> detail(@PathVariable String id) {
        return Map.of("code", 0, "data", orderService.getOrder(id));
    }

    @PostMapping("/orders")
    public Map<String, Object> create(@RequestBody Map<String, Object> payload) {
        return Map.of("code", 0, "data", orderService.createOrder(payload));
    }

    @PostMapping("/orders/from-platform")
    public Map<String, Object> createFromPlatform(@RequestBody Map<String, Object> payload) {
        return Map.of("code", 0, "data", orderService.createFromPlatformOrder(payload));
    }

    @PostMapping("/orders/{id}/review")
    public Map<String, Object> review(@PathVariable String id, @RequestBody Map<String, Object> payload) {
        return Map.of("code", 0, "data", orderService.reviewOrder(id, payload));
    }

    @PostMapping("/orders/{id}/release")
    public Map<String, Object> release(@PathVariable String id, @RequestBody Map<String, Object> payload) {
        return Map.of("code", 0, "data", orderService.releaseOrder(id, payload));
    }

    @PostMapping("/orders/{id}/ship")
    public Map<String, Object> ship(@PathVariable String id) {
        return Map.of("code", 0, "data", orderService.shipOrder(id));
    }

    @PostMapping("/orders/{id}/cancel")
    public Map<String, Object> cancel(@PathVariable String id) {
        return Map.of("code", 0, "data", orderService.cancelOrder(id));
    }

    @DeleteMapping("/orders/{id}")
    public Map<String, Object> delete(@PathVariable String id) {
        orderService.deleteOrder(id);
        return Map.of("code", 0, "data", true);
    }
}
