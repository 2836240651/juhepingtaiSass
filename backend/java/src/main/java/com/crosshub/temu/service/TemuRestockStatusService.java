package com.crosshub.temu.service;

import java.util.List;
import java.util.Map;

public interface TemuRestockStatusService {
    List<Map<String, Object>> listAll();

    Map<String, Object> upsert(Map<String, Object> payload);
}
