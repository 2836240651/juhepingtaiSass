package com.crosshub.amazon.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public record AmazonMessagePatchRequest(
        @JsonProperty("template_id") String templateId,
        String note
) {}
