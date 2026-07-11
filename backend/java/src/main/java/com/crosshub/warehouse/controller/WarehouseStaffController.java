package com.crosshub.warehouse.controller;

import com.crosshub.common.StatusRequest;
import com.crosshub.warehouse.dto.StaffPayload;
import com.crosshub.warehouse.service.WarehouseStaffService;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/warehouse")
public class WarehouseStaffController {
    private final WarehouseStaffService staffService;

    public WarehouseStaffController(WarehouseStaffService staffService) {
        this.staffService = staffService;
    }

    @GetMapping("/members")
    public Map<String, Object> listMembers() {
        return Map.of("code", 0, "data", staffService.listStaff());
    }

    @PostMapping("/members")
    public Map<String, Object> createMember(@RequestBody StaffPayload request) {
        return Map.of("code", 0, "data", staffService.createStaff(request));
    }

    @PutMapping("/members/{id}")
    public Map<String, Object> updateMember(@PathVariable("id") Long id, @RequestBody StaffPayload request) {
        return Map.of("code", 0, "data", staffService.updateStaff(id, request));
    }

    @PatchMapping("/members/{id}/status")
    public Map<String, Object> updateStatus(@PathVariable("id") Long id, @RequestBody StatusRequest request) {
        return Map.of("code", 0, "data", staffService.updateStatus(id, request.status()));
    }

    @DeleteMapping("/members/{id}")
    public Map<String, Object> deleteMember(@PathVariable("id") Long id) {
        staffService.deleteStaff(id);
        return Map.of("code", 0, "data", true);
    }
}
