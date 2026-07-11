package com.crosshub.task.service;

import java.util.List;
import java.util.Map;

public interface OpsFeedbackService {
    List<Map<String, Object>> listToday();

    List<Map<String, Object>> listByTaskId(String taskId);

    Map<String, Object> submitFeedback(Map<String, Object> payload);
}
