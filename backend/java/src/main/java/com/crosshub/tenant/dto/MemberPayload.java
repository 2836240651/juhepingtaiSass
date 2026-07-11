package com.crosshub.tenant.dto;

import java.util.List;

public record MemberPayload(
        String name,
        String account,
        String password,
        String phone,
        String role,
        List<String> platforms,
        List<String> shopIds,
        List<String> menuCodes,
        Boolean status
) {}
