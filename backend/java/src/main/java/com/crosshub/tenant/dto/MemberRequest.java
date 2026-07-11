package com.crosshub.tenant.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

public record MemberRequest(
        String name,
        String account,
        String password,
        String phone,
        String role,
        List<String> platforms,
        @JsonProperty("shop_ids") List<String> shopIds,
        @JsonProperty("menu_codes") List<String> menuCodes,
        Boolean status
) {}
