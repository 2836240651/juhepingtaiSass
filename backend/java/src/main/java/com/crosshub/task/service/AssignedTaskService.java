package com.crosshub.task.service;

import java.util.List;
import java.util.Map;

public interface AssignedTaskService {
    List<Map<String, Object>> listTasks(String status, String platformKey, boolean activeOnly);

    Map<String, Object> getTask(String id);

    Map<String, Object> createTask(Map<String, Object> payload);

    Map<String, Object> updateTask(String id, Map<String, Object> payload);

    Map<String, Object> updateTaskStatus(String id, String status, Map<String, Object> extra);

    void deleteTask(String id);
}
