package com.crosshub.task.controller;

import com.crosshub.task.service.OpsFeedbackService;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/ops-feedback")
public class OpsFeedbackController {
    private final OpsFeedbackService opsFeedbackService;

    public OpsFeedbackController(OpsFeedbackService opsFeedbackService) {
        this.opsFeedbackService = opsFeedbackService;
    }

    @GetMapping("/today")
    public Map<String, Object> today() {
        return Map.of("code", 0, "data", opsFeedbackService.listToday());
    }

    @GetMapping
    public Map<String, Object> byTask(@RequestParam("task_id") String taskId) {
        return Map.of("code", 0, "data", opsFeedbackService.listByTaskId(taskId));
    }

    @PostMapping
    public Map<String, Object> submit(@RequestBody Map<String, Object> payload) {
        return Map.of("code", 0, "data", opsFeedbackService.submitFeedback(payload));
    }
}
