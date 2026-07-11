package com.crosshub.amazon.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public record AmazonOutboundShipPatchRequest(
        @JsonProperty("tracking_no") String trackingNo
) {}
