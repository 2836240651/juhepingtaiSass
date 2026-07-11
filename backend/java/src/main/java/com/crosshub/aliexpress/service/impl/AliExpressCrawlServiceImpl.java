package com.crosshub.aliexpress.service.impl;

import com.crosshub.aliexpress.dto.AliExpressCrawlRequest;
import com.crosshub.aliexpress.entity.AliExpressCrawlJob;
import com.crosshub.aliexpress.repository.AliExpressCrawlJobRepository;
import com.crosshub.aliexpress.service.AliExpressCrawlConflictException;
import com.crosshub.aliexpress.service.AliExpressCrawlService;
import com.crosshub.common.AppErrorCode;
import com.crosshub.config.CrawlerProperties;
import com.crosshub.security.AuthContext;
import com.crosshub.tenant.service.DataScopeService;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.support.TransactionSynchronization;
import org.springframework.transaction.support.TransactionSynchronizationManager;
import org.springframework.web.server.ResponseStatusException;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Executor;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

@Service
public class AliExpressCrawlServiceImpl implements AliExpressCrawlService {
    private static final Logger log = LoggerFactory.getLogger(AliExpressCrawlServiceImpl.class);
    private static final DateTimeFormatter TS = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
    private static final Set<String> ACTIVE_STATUSES = Set.of("pending", "running");
    private static final long PENDING_TTL_SECONDS = 5 * 60;

    private final AliExpressCrawlJobRepository jobRepository;
    private final DataScopeService dataScopeService;
    private final AuthContext authContext;
    private final CrawlerProperties crawlerProperties;
    private final ObjectMapper objectMapper;
    private final Executor crawlExecutor;

    public AliExpressCrawlServiceImpl(
            AliExpressCrawlJobRepository jobRepository,
            DataScopeService dataScopeService,
            AuthContext authContext,
            CrawlerProperties crawlerProperties,
            ObjectMapper objectMapper,
            @Qualifier("crawlExecutor") Executor crawlExecutor
    ) {
        this.jobRepository = jobRepository;
        this.dataScopeService = dataScopeService;
        this.authContext = authContext;
        this.crawlerProperties = crawlerProperties;
        this.objectMapper = objectMapper;
        this.crawlExecutor = crawlExecutor;
    }

    @Override
    @Transactional
    public AliExpressCrawlJob triggerCrawl(AliExpressCrawlRequest request) {
        return createJob(request == null ? null : request.reportTime(), "all");
    }

    @Override
    @Transactional
    public AliExpressCrawlJob triggerViolationSync() {
        return createJob(null, "violations");
    }

    @Override
    public AliExpressCrawlJob getJob(String jobId) {
        Long tenantId = dataScopeService.requireTenantId();
        AliExpressCrawlJob job = jobRepository.findByIdAndTenantId(jobId, tenantId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, AppErrorCode.CRAWL_JOB_NOT_FOUND.getUserMessage()));
        return reconcileStaleJob(job);
    }

    private AliExpressCrawlJob createJob(String reportTime, String scope) {
        Long tenantId = dataScopeService.requireTenantId();
        Long userId = authContext.userId();
        if (userId == null) {
            throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, AppErrorCode.AUTH_MISSING_USER.getUserMessage());
        }
        Optional<AliExpressCrawlJob> active = jobRepository.findFirstByTenantIdAndStatusInOrderByCreatedAtDesc(
                tenantId, ACTIVE_STATUSES
        );
        if (active.isPresent()) {
            AliExpressCrawlJob existing = reconcileStaleJob(active.get());
            if (ACTIVE_STATUSES.contains(existing.getStatus())) {
                throw new AliExpressCrawlConflictException(existing);
            }
        }

        AliExpressCrawlJob job = new AliExpressCrawlJob();
        job.setId(UUID.randomUUID().toString());
        job.setTenantId(tenantId);
        job.setTriggeredBy(userId);
        job.setStatus("pending");
        job.setMode("live");
        job.setScope(scope);
        job.setReportTime(reportTime);
        job.setCreatedAt(now());
        jobRepository.save(job);

        String jobId = job.getId();
        scheduleAfterCommit(() -> crawlExecutor.execute(() -> executeJob(jobId)));
        return job;
    }

    private void scheduleAfterCommit(Runnable task) {
        if (TransactionSynchronizationManager.isSynchronizationActive()) {
            TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
                @Override
                public void afterCommit() {
                    task.run();
                }
            });
            return;
        }
        task.run();
    }

    void executeJob(String jobId) {
        AliExpressCrawlJob job = jobRepository.findById(jobId).orElse(null);
        if (job == null) {
            return;
        }

        job.setStatus("running");
        job.setStartedAt(now());
        jobRepository.save(job);

        Path scriptDir = Path.of(crawlerProperties.getScriptDir()).toAbsolutePath().normalize();
        if (!Files.isDirectory(scriptDir)) {
            failJob(job, AppErrorCode.CRAWL_SCRIPT_MISSING, "Python 脚本目录不存在: " + scriptDir);
            return;
        }

        List<String> command = new ArrayList<>();
        command.add(crawlerProperties.getPythonExecutable());
        command.add("operational_crawl.py");
        command.add("--platform");
        command.add("aliexpress");
        command.add("--tenant-id");
        command.add(String.valueOf(job.getTenantId()));
        command.add("--scope");
        command.add(normalizeScope(job.getScope()));
        command.add("--json");
        if (job.getReportTime() != null && !job.getReportTime().isBlank()) {
            command.add("--date");
            command.add(job.getReportTime());
        }

        ProcessBuilder builder = new ProcessBuilder(command);
        builder.directory(scriptDir.toFile());
        builder.environment().put("TENANT_ID", String.valueOf(job.getTenantId()));
        builder.redirectErrorStream(false);

        try {
            Process process = builder.start();
            CompletableFuture<String> stdoutFuture = CompletableFuture.supplyAsync(
                    () -> safeReadStream(process.getInputStream()),
                    crawlExecutor
            );
            CompletableFuture<String> stderrFuture = CompletableFuture.supplyAsync(
                    () -> safeReadStream(process.getErrorStream()),
                    crawlExecutor
            );
            boolean finished = process.waitFor(crawlerProperties.getTimeoutSeconds(), TimeUnit.SECONDS);
            if (!finished) {
                process.destroyForcibly();
                stdoutFuture.cancel(true);
                stderrFuture.cancel(true);
                failJob(job, AppErrorCode.CRAWL_TIMEOUT, "爬取超时（" + crawlerProperties.getTimeoutSeconds() + "s）");
                return;
            }
            String stdout = "";
            String stderr = "";
            try {
                stdout = stdoutFuture.get(3, TimeUnit.SECONDS);
            } catch (TimeoutException ignored) {
                stdoutFuture.cancel(true);
            }
            try {
                stderr = stderrFuture.get(3, TimeUnit.SECONDS);
            } catch (TimeoutException ignored) {
                stderrFuture.cancel(true);
            }
            if (process.exitValue() != 0) {
                String raw = combineOutput(stderr, stdout);
                failJob(job, AppErrorCode.classifyCrawlRaw(raw), raw);
                return;
            }

            JsonNode json = parseJsonLine(stdout);
            if (json != null) {
                if (json.has("report_time")) {
                    job.setReportTime(json.get("report_time").asText(""));
                }
                if (json.has("shops")) {
                    job.setShopsCount(json.get("shops").asInt(0));
                }
                if (json.has("rows")) {
                    job.setRowsCount(json.get("rows").asInt(0));
                }
                if (json.has("orders")) {
                    job.setOrdersCount(json.get("orders").asInt(0));
                }
                if (json.has("violations")) {
                    job.setViolationsCount(json.get("violations").asInt(0));
                }
                if (json.has("products")) {
                    job.setProductsCount(json.get("products").asInt(0));
                }
            }

            job.setStatus("success");
            job.setFinishedAt(now());
            job.setErrorCode(null);
            job.setErrorMessage(null);
            jobRepository.save(job);
        } catch (Exception ex) {
            log.error("AliExpress crawl job {} failed", jobId, ex);
            String raw = ex.getMessage() == null ? "爬取进程异常" : ex.getMessage();
            failJob(job, AppErrorCode.classifyCrawlRaw(raw), raw);
        }
    }

    private AliExpressCrawlJob reconcileStaleJob(AliExpressCrawlJob job) {
        if (job == null || !ACTIVE_STATUSES.contains(job.getStatus())) {
            return job;
        }
        if (!isStale(job)) {
            return job;
        }
        markStaleJobFailed(job);
        return job;
    }

    private boolean isStale(AliExpressCrawlJob job) {
        LocalDateTime base = parseTime("running".equals(job.getStatus()) ? job.getStartedAt() : job.getCreatedAt());
        if (base == null) {
            return true;
        }
        long ttl = "running".equals(job.getStatus())
                ? crawlerProperties.getTimeoutSeconds() + 60L
                : PENDING_TTL_SECONDS;
        return base.plusSeconds(ttl).isBefore(LocalDateTime.now());
    }

    private void markStaleJobFailed(AliExpressCrawlJob job) {
        job.setStatus("failed");
        job.setFinishedAt(now());
        job.setErrorCode(AppErrorCode.CRAWL_INTERRUPTED.getCode());
        job.setErrorMessage(AppErrorCode.CRAWL_INTERRUPTED.getUserMessage());
        jobRepository.save(job);
        log.warn("AliExpress crawl job {} marked stale -> failed", job.getId());
    }

    private LocalDateTime parseTime(String text) {
        if (text == null || text.isBlank()) {
            return null;
        }
        try {
            return LocalDateTime.parse(text, TS);
        } catch (Exception ex) {
            return null;
        }
    }

    private String normalizeScope(String scope) {
        String value = scope == null || scope.isBlank() ? "all" : scope.trim().toLowerCase(Locale.ROOT);
        return switch (value) {
            case "all", "orders", "violations", "operational" -> value;
            default -> "all";
        };
    }

    private void failJob(AliExpressCrawlJob job, AppErrorCode code, String raw) {
        job.setStatus("failed");
        job.setFinishedAt(now());
        job.setErrorCode(code.getCode());
        job.setErrorMessage(code.getUserMessage());
        jobRepository.save(job);
        log.warn("AliExpress crawl job {} failed [{}]: {}", job.getId(), code.getCode(), trimMessage(raw));
    }

    private JsonNode parseJsonLine(String stdout) {
        if (stdout == null || stdout.isBlank()) {
            return null;
        }
        for (String line : stdout.split("\\R")) {
            String trimmed = line.trim();
            if (!trimmed.startsWith("{")) {
                continue;
            }
            try {
                return objectMapper.readTree(trimmed);
            } catch (Exception ignored) {
                // continue
            }
        }
        return null;
    }

    private String combineOutput(String stderr, String stdout) {
        if (stderr != null && !stderr.isBlank()) {
            return stderr;
        }
        return stdout == null ? "" : stdout;
    }

    private String readStream(java.io.InputStream stream) throws Exception {
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(stream, StandardCharsets.UTF_8))) {
            StringBuilder sb = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                if (!sb.isEmpty()) {
                    sb.append(System.lineSeparator());
                }
                sb.append(line);
            }
            return sb.toString();
        }
    }

    private String safeReadStream(java.io.InputStream stream) {
        try {
            return readStream(stream);
        } catch (Exception ex) {
            return "";
        }
    }

    private String trimMessage(String message) {
        if (message == null) {
            return "";
        }
        String trimmed = message.trim();
        return trimmed.length() <= 2000 ? trimmed : trimmed.substring(trimmed.length() - 2000);
    }

    private String now() {
        return LocalDateTime.now().format(TS);
    }
}

