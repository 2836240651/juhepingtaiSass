package com.crosshub.agent.service;

import java.util.List;
import java.util.Map;

public interface AgentService {
    String TASK_TYPE = "amazon_sync";

    Map<String, Object> registerAgent(String name);

    Map<String, Object> setupLocalAgent(String name);

    List<Map<String, Object>> listAgents();

    Map<String, Object> heartbeat(boolean ziniaoOnline);

    List<Map<String, Object>> pollTasks();

    Map<String, Object> completeTask(String taskId, String status, Map<String, Object> result, String errorCode, String errorMessage);

    void onAgentTaskStarted(com.crosshub.agent.entity.AgentTask task);
}
