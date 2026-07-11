package com.crosshub.monitor.service;

import java.util.Map;

public class MonitorJobConflictException extends RuntimeException {
    private final Map<String, Object> existingJob;

    public MonitorJobConflictException(Map<String, Object> existingJob) {
        super("monitor job in progress");
        this.existingJob = existingJob;
    }

    public Map<String, Object> getExistingJob() {
        return existingJob;
    }
}
