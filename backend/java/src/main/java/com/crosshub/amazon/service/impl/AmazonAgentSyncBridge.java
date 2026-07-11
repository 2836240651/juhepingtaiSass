package com.crosshub.amazon.service.impl;

import com.crosshub.agent.entity.AgentTask;
import com.crosshub.agent.service.AgentService;
import com.crosshub.agent.service.impl.AgentServiceImpl;
import com.crosshub.amazon.service.AmazonSyncService;
import org.springframework.stereotype.Component;

import java.util.Map;

@Component
public class AmazonAgentSyncBridge implements AgentServiceImpl.AmazonSyncBridge {
    private final AmazonSyncService amazonSyncService;

    public AmazonAgentSyncBridge(AmazonSyncService amazonSyncService) {
        this.amazonSyncService = amazonSyncService;
    }

    @Override
    public void onAgentTaskStarted(AgentTask task) {
        // Amazon sync job status is finalized in onAgentTaskCompleted.
    }

    @Override
    public void onAgentTaskCompleted(
            AgentTask task,
            String status,
            Map<String, Object> result,
            String errorCode,
            String errorMessage
    ) {
        if (task == null || !AgentService.TASK_TYPE.equals(task.getTaskType())) {
            return;
        }
        amazonSyncService.onAgentTaskCompleted(task.getId(), status, result, errorCode, errorMessage);
    }
}
