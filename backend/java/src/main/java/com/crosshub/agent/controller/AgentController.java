package com.crosshub.agent.controller;

import com.crosshub.agent.dto.AgentHeartbeatRequest;
import com.crosshub.agent.dto.AgentRegisterRequest;
import com.crosshub.agent.dto.AgentTaskCompleteRequest;
import com.crosshub.agent.service.AgentService;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/agent")
public class AgentController {
    private final AgentService agentService;

    public AgentController(AgentService agentService) {
        this.agentService = agentService;
    }

    @PostMapping("/register")
    public Map<String, Object> register(@RequestBody AgentRegisterRequest request) {
        return Map.of("success", true, "data", agentService.registerAgent(request.name()));
    }

    @PostMapping("/setup")
    public Map<String, Object> setup(@RequestBody(required = false) AgentRegisterRequest request) {
        String name = request == null ? null : request.name();
        return Map.of("success", true, "data", agentService.setupLocalAgent(name));
    }

    @GetMapping("/nodes")
    public Map<String, Object> nodes() {
        List<Map<String, Object>> rows = agentService.listAgents();
        return Map.of("success", true, "data", rows);
    }

    @PostMapping("/heartbeat")
    public Map<String, Object> heartbeat(@RequestBody AgentHeartbeatRequest request) {
        boolean online = request != null && Boolean.TRUE.equals(request.ziniaoOnline());
        return Map.of("success", true, "data", agentService.heartbeat(online));
    }

    @GetMapping("/tasks")
    public Map<String, Object> pollTasks() {
        return Map.of("success", true, "data", agentService.pollTasks());
    }

    @PostMapping("/tasks/{taskId}/complete")
    public Map<String, Object> completeTask(@PathVariable String taskId, @RequestBody AgentTaskCompleteRequest request) {
        return Map.of(
                "success", true,
                "data", agentService.completeTask(
                        taskId,
                        request.status(),
                        request.result(),
                        request.errorCode(),
                        request.errorMessage()
                )
        );
    }
}
