package com.crosshub.aliexpress.service;

import com.crosshub.aliexpress.entity.AliExpressCrawlJob;

public class AliExpressCrawlConflictException extends RuntimeException {
    private final AliExpressCrawlJob existingJob;

    public AliExpressCrawlConflictException(AliExpressCrawlJob existingJob) {
        super("爬取进行中");
        this.existingJob = existingJob;
    }

    public AliExpressCrawlJob getExistingJob() {
        return existingJob;
    }
}

