package com.crosshub.warehouse.dto;

import java.util.List;

public record StaffPayload(
        String name,
        String account,
        String password,
        String phone,
        String role,
        Boolean status,
        List<String> warehouseIds
) {}
