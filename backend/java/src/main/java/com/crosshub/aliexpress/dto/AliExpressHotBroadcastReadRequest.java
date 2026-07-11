package com.crosshub.aliexpress.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public record AliExpressHotBroadcastReadRequest(
        @JsonProperty("reader_id") String readerId,
        @JsonProperty("reader_name") String readerName
) {}

