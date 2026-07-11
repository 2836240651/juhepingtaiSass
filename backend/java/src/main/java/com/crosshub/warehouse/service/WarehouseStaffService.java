package com.crosshub.warehouse.service;

import com.crosshub.warehouse.dto.StaffPayload;

import java.util.List;
import java.util.Map;

public interface WarehouseStaffService {
    List<Map<String, Object>> listStaff();

    Map<String, Object> createStaff(StaffPayload payload);

    Map<String, Object> updateStaff(Long staffId, StaffPayload payload);

    void deleteStaff(Long staffId);

    Map<String, Object> updateStatus(Long staffId, boolean active);
}
