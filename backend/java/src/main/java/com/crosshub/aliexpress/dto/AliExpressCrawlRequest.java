package com.crosshub.aliexpress.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public record AliExpressCrawlRequest(
        @JsonProperty("report_time") String reportTime
) {}

