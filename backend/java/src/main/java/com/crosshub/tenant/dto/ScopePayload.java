package com.crosshub.tenant.dto;

import java.util.List;

public record ScopePayload(
        List<String> platforms,
        List<String> shopIds,
        List<String> menuCodes
) {}
