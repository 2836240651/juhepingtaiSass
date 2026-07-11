package com.crosshub.platform.dto;

import java.util.List;

public record BatchBindRequest(String companyName, List<BindRequest> stores) {}
