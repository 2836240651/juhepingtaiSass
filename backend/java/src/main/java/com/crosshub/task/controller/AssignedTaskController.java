package com.crosshub.task.controller;

import com.crosshub.task.service.AssignedTaskService;
import com.crosshub.task.service.OpsFeedbackService;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/tasks")
public class AssignedTaskController {
    private final AssignedTaskService assignedTaskService;

    public AssignedTaskController(AssignedTaskService assignedTaskService) {
        this.assignedTaskService = assignedTaskService;
    }

    @GetMapping
    public Map<String, Object> list(
            @RequestParam(value = "status", required = false) String status,
            @RequestParam(value = "platform_key", required = false) String platformKey,
            @RequestParam(value = "active_only", defaultValue = "false") boolean activeOnly
    ) {
        return Map.of(
                "code", 0,
                "data", assignedTaskService.listTasks(status, platformKey, activeOnly)
        );
    }

    @GetMapping("/{id}")
    public Map<String, Object> detail(@PathVariable String id) {
        return Map.of("code", 0, "data", assignedTaskService.getTask(id));
    }

    @PostMapping
    public Map<String, Object> create(@RequestBody Map<String, Object> payload) {
        return Map.of("code", 0, "data", assignedTaskService.createTask(payload));
    }

    @PatchMapping("/{id}")
    public Map<String, Object> patch(@PathVariable String id, @RequestBody Map<String, Object> payload) {
        if (payload.containsKey("status")) {
            return Map.of(
                    "code", 0,
                    "data", assignedTaskService.updateTaskStatus(id, String.valueOf(payload.get("status")), payload)
            );
        }
        return Map.of("code", 0, "data", assignedTaskService.updateTask(id, payload));
    }

    @DeleteMapping("/{id}")
    public Map<String, Object> delete(@PathVariable String id) {
        assignedTaskService.deleteTask(id);
        return Map.of("code", 0, "data", true);
    }
}
