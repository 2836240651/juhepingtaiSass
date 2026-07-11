package com.crosshub.tenant.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

public record MemberScopeRequest(
        List<String> platforms,
        @JsonProperty("shop_ids") List<String> shopIds,
        @JsonProperty("menu_codes") List<String> menuCodes
) {}
