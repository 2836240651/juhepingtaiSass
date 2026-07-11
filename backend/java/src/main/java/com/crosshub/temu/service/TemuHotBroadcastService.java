package com.crosshub.temu.service;

import java.util.List;
import java.util.Map;

public interface TemuHotBroadcastService {
    List<Map<String, Object>> listBroadcasts();

    Map<String, Object> createBroadcast(Map<String, Object> payload);

    Map<String, Object> markRead(String broadcastId, Map<String, Object> payload);
}
