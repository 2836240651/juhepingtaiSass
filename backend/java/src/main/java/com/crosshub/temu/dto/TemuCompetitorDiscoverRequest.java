package com.crosshub.temu.dto;

public record TemuCompetitorDiscoverRequest(
        String keyword,
        String region,
        Integer limit
) {}

