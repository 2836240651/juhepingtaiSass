package com.crosshub.temu.service;

import com.crosshub.temu.entity.TemuCrawlJob;

public class CrawlConflictException extends RuntimeException {
    private final TemuCrawlJob existingJob;

    public CrawlConflictException(TemuCrawlJob existingJob) {
        super("爬取进行中");
        this.existingJob = existingJob;
    }

    public TemuCrawlJob getExistingJob() {
        return existingJob;
    }
}
