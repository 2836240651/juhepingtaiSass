package com.crosshub.amazon.service;

import com.crosshub.amazon.entity.AmazonSyncJob;

public class AmazonSyncConflictException extends RuntimeException {
    private final AmazonSyncJob existingJob;

    public AmazonSyncConflictException(AmazonSyncJob existingJob) {
        super("Amazon 同步进行中");
        this.existingJob = existingJob;
    }

    public AmazonSyncJob getExistingJob() {
        return existingJob;
    }
}
