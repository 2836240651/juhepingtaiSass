package com.crosshub.agent.service.impl;

import com.crosshub.agent.entity.AgentTask;
import com.crosshub.agent.entity.IntegrationAgent;
import com.crosshub.agent.repository.AgentTaskRepository;
import com.crosshub.agent.repository.IntegrationAgentRepository;
import com.crosshub.agent.service.AgentService;
import com.crosshub.common.AppErrorCode;
import com.crosshub.security.AgentContext;
import com.crosshub.security.AuthContext;
import com.crosshub.tenant.service.DataScopeService;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Lazy;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@Service
public class AgentServiceImpl implements AgentService {
    private static final DateTimeFormatter TS = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

    private final IntegrationAgentRepository agentRepository;
    private final AgentTaskRepository taskRepository;
    private final AuthContext authContext;
    private final AgentContext agentContext;
    private final DataScopeService dataScopeService;
    private final ObjectMapper objectMapper;
    private final AmazonSyncBridge amazonSyncBridge;

    public AgentServiceImpl(
            IntegrationAgentRepository agentRepository,
            AgentTaskRepository taskRepository,
            AuthContext authContext,
            AgentContext agentContext,
            DataScopeService dataScopeService,
            ObjectMapper objectMapper,
            @Autowired(required = false) @Lazy AmazonSyncBridge amazonSyncBridge
    ) {
        this.agentRepository = agentRepository;
        this.taskRepository = taskRepository;
        this.authContext = authContext;
        this.agentContext = agentContext;
        this.dataScopeService = dataScopeService;
        this.objectMapper = objectMapper;
        this.amazonSyncBridge = amazonSyncBridge;
    }

    public interface AmazonSyncBridge {
        void onAgentTaskStarted(AgentTask task);
        void onAgentTaskCompleted(AgentTask task, String status, Map<String, Object> result, String errorCode, String errorMessage);
    }

    private Long requireBossTenant() {
        if (!authContext.isBossPortal() && !authContext.isAdmin()) {
            throw new ResponseStatusException(HttpStatus.FORBIDDEN, AppErrorCode.FORBIDDEN.getUserMessage());
        }
        return dataScopeService.requireTenantId();
    }

    private IntegrationAgent requireAgent() {
        IntegrationAgent agent = agentContext.agent();
        if (agent == null) {
            throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "Agent 未认证");
        }
        return agent;
    }

    private String now() {
        return LocalDateTime.now().format(TS);
    }

    @Override
    @Transactional
    public Map<String, Object> registerAgent(String name) {
        Long tenantId = requireBossTenant();
        return createAgent(tenantId, name);
    }

    @Override
    @Transactional
    public Map<String, Object> setupLocalAgent(String name) {
        Long tenantId = requireBossTenant();
        return createAgent(tenantId, name == null || name.isBlank() ? "本机 Agent" : name.trim());
    }

    private Map<String, Object> createAgent(Long tenantId, String name) {
        IntegrationAgent agent = new IntegrationAgent();
        agent.setId(UUID.randomUUID().toString());
        agent.setTenantId(tenantId);
        agent.setName(name);
        agent.setAgentToken(UUID.randomUUID().toString().replace("-", ""));
        agent.setStatus("active");
        agent.setCreatedAt(now());
        agent.setLastHeartbeatAt("");
        agent.setZiniaoOnline(0);
        agentRepository.save(agent);
        Map<String, Object> data = new LinkedHashMap<>();
        data.put("node_id", agent.getId());
        data.put("agent_token", agent.getAgentToken());
        data.put("name", agent.getName());
        return data;
    }

    @Override
    public List<Map<String, Object>> listAgents() {
        Long tenantId = requireBossTenant();
        return agentRepository.findByTenantIdOrderByCreatedAtDesc(tenantId).stream()
                .map(this::toAgentDto)
                .toList();
    }

    @Override
    @Transactional
    public Map<String, Object> heartbeat(boolean ziniaoOnline) {
        IntegrationAgent agent = requireAgent();
        agent.setLastHeartbeatAt(now());
        agent.setZiniaoOnline(ziniaoOnline ? 1 : 0);
        agentRepository.save(agent);
        return Map.of("node_id", agent.getId(), "status", "ok");
    }

    @Override
    @Transactional
    public List<Map<String, Object>> pollTasks() {
        IntegrationAgent agent = requireAgent();
        Long tenantId = agent.getTenantId();
        List<AgentTask> pending = taskRepository.findByTenantIdAndStatusOrderByCreatedAtAsc(tenantId, "pending");
        boolean amazonSyncRunning = taskRepository.findByTenantIdAndStatusOrderByCreatedAtAsc(tenantId, "running")
                .stream()
                .anyMatch(task -> TASK_TYPE.equals(task.getTaskType()));
        List<Map<String, Object>> result = new ArrayList<>();
        for (AgentTask task : pending) {
            if (result.size() >= 5) {
                break;
            }
            if (TASK_TYPE.equals(task.getTaskType()) && amazonSyncRunning) {
                continue;
            }
            task.setStatus("running");
            task.setAgentId(agent.getId());
            task.setStartedAt(now());
            taskRepository.save(task);
            onAgentTaskStarted(task);
            result.add(toTaskDto(task));
            if (TASK_TYPE.equals(task.getTaskType())) {
                amazonSyncRunning = true;
            }
        }
        return result;
    }

    @Override
    @Transactional
    public Map<String, Object> completeTask(
            String taskId,
            String status,
            Map<String, Object> result,
            String errorCode,
            String errorMessage
    ) {
        IntegrationAgent agent = requireAgent();
        AgentTask task = taskRepository.findByIdAndTenantId(taskId, agent.getTenantId())
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "任务不存在"));
        String normalized = status == null ? "failed" : status.trim().toLowerCase();
        task.setStatus(normalized);
        task.setFinishedAt(now());
        task.setErrorCode(errorCode == null ? "" : errorCode);
        task.setErrorMessage(errorMessage == null ? "" : errorMessage);
        try {
            task.setResultJson(objectMapper.writeValueAsString(result == null ? Map.of() : result));
        } catch (Exception ex) {
            task.setResultJson("{}");
        }
        taskRepository.save(task);
        if (amazonSyncBridge != null) {
            amazonSyncBridge.onAgentTaskCompleted(task, normalized, result, task.getErrorCode(), task.getErrorMessage());
        }
        return Map.of("task_id", task.getId(), "status", task.getStatus());
    }

    @Override
    public void onAgentTaskStarted(AgentTask task) {
        if (amazonSyncBridge != null) {
            amazonSyncBridge.onAgentTaskStarted(task);
        }
    }

    private Map<String, Object> toAgentDto(IntegrationAgent agent) {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("id", agent.getId());
        row.put("name", agent.getName());
        row.put("status", agent.getStatus());
        row.put("last_heartbeat_at", agent.getLastHeartbeatAt());
        row.put("ziniao_online", agent.getZiniaoOnline());
        row.put("created_at", agent.getCreatedAt());
        return row;
    }

    private Map<String, Object> toTaskDto(AgentTask task) {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("task_id", task.getId());
        row.put("id", task.getId());
        row.put("task_type", task.getTaskType());
        row.put("status", task.getStatus());
        try {
            row.put("payload", objectMapper.readValue(
                    task.getPayloadJson() == null || task.getPayloadJson().isBlank() ? "{}" : task.getPayloadJson(),
                    new TypeReference<Map<String, Object>>() {}
            ));
        } catch (Exception ex) {
            row.put("payload", Map.of());
        }
        return row;
    }
}
