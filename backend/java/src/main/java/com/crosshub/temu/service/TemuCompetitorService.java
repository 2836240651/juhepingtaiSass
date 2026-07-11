package com.crosshub.temu.service;

import com.crosshub.temu.dto.TemuCompetitorDiscoverRequest;

import java.util.Map;

public interface TemuCompetitorService {
    Map<String, Object> discoverCandidates(TemuCompetitorDiscoverRequest request);
}

