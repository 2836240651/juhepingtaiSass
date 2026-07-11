package com.crosshub.agent.dto;

import java.util.Map;

public record AgentTaskCompleteRequest(
        String status,
        Map<String, Object> result,
        String errorCode,
        String errorMessage
) {}
