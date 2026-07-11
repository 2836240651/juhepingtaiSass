package com.crosshub.amazon.service.impl;

import com.crosshub.amazon.dto.AmazonSyncRequest;
import com.crosshub.amazon.entity.AmazonSyncJob;
import com.crosshub.amazon.repository.AmazonSyncJobRepository;
import com.crosshub.amazon.service.AmazonSyncConflictException;
import com.crosshub.amazon.service.AmazonSyncService;
import com.crosshub.common.AppErrorCode;
import com.crosshub.platform.entity.PlatformAccount;
import com.crosshub.platform.repository.PlatformAccountRepository;
import com.crosshub.tenant.service.DataScopeService;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;

@Service
public class AmazonSyncServiceImpl implements AmazonSyncService {
    private static final DateTimeFormatter TS = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
    private static final Set<String> ACTIVE = Set.of("pending", "running");
    private static final Set<String> NEEDS_PRODUCT_ROWS = Set.of("daily", "insights", "reports");
    private static final long RUNNING_TTL_SECONDS = 16 * 60;
    private static final long PENDING_TTL_SECONDS = 5 * 60;

    private final AmazonSyncJobRepository syncJobRepository;
    private final PlatformAccountRepository platformAccountRepository;
    private final DataScopeService dataScopeService;
    private final ObjectMapper objectMapper;
    private final JdbcTemplate jdbc;
    private final AmazonOperationalPersistenceServiceImpl persistenceService;

    public AmazonSyncServiceImpl(
            AmazonSyncJobRepository syncJobRepository,
            PlatformAccountRepository platformAccountRepository,
            DataScopeService dataScopeService,
            ObjectMapper objectMapper,
            JdbcTemplate jdbc,
            AmazonOperationalPersistenceServiceImpl persistenceService
    ) {
        this.syncJobRepository = syncJobRepository;
        this.platformAccountRepository = platformAccountRepository;
        this.dataScopeService = dataScopeService;
        this.objectMapper = objectMapper;
        this.jdbc = jdbc;
        this.persistenceService = persistenceService;
    }

    @Transactional
    public Map<String, Object> triggerSync(AmazonSyncRequest request) {
        Long tenantId = dataScopeService.requireTenantId();
        String scope = normalizeScope(request == null ? null : request.scope());
        List<PlatformAccount> targets = resolveTargets(tenantId, request == null ? null : request.platformAccountId());
        if (targets.isEmpty()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, AppErrorCode.ACCOUNT_NOT_FOUND.getUserMessage());
        }

        List<Map<String, Object>> jobs = new ArrayList<>();
        for (PlatformAccount account : targets) {
            Optional<AmazonSyncJob> active = syncJobRepository
                    .findFirstByTenantIdAndPlatformAccountIdAndScopeAndStatusInOrderByCreatedAtDesc(
                            tenantId, account.getId(), scope, ACTIVE
                    );
            if (active.isPresent()) {
                AmazonSyncJob existing = active.get();
                if (!isStale(existing)) {
                    throw new AmazonSyncConflictException(existing);
                }
                markStaleJobFailed(existing);
            }

            String taskId = "agt_" + UUID.randomUUID();
            AmazonSyncJob job = new AmazonSyncJob();
            job.setId("amz_sync_" + UUID.randomUUID());
            job.setTenantId(tenantId);
            job.setPlatformAccountId(account.getId());
            job.setAgentTaskId(taskId);
            job.setAgentId("");
            job.setScope(scope);
            job.setStatus("pending");
            job.setMode("ziniao_webdriver");
            job.setCreatedAt(now());
            job.setResultSummary("{}");
            syncJobRepository.save(job);

            enqueueAgentTask(tenantId, taskId, scope, account);
            jobs.add(jobDto(job));
        }

        return Map.of("jobs", jobs);
    }

    public AmazonSyncJob getJob(String jobId) {
        Long tenantId = dataScopeService.requireTenantId();
        return syncJobRepository.findByIdAndTenantId(jobId, tenantId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, AppErrorCode.AMAZON_SYNC_JOB_NOT_FOUND.getUserMessage()));
    }

    @Transactional
    public void onAgentTaskCompleted(String taskId, String status, Map<String, Object> result, String errorCode, String errorMessage) {
        if (taskId == null || taskId.isBlank()) {
            return;
        }
        AmazonSyncJob job = syncJobRepository.findAll().stream()
                .filter(x -> taskId.equals(x.getAgentTaskId()))
                .findFirst()
                .orElse(null);
        if (job == null) {
            return;
        }

        if (!"running".equals(job.getStatus())) {
            job.setStatus("running");
            job.setStartedAt(now());
        }

        if (!"success".equalsIgnoreCase(status)) {
            job.setStatus("failed");
            job.setErrorCode(defaultText(errorCode, AppErrorCode.AMAZON_SYNC_FAILED.getCode()));
            job.setErrorMessage(defaultText(errorMessage, AppErrorCode.AMAZON_SYNC_FAILED.getUserMessage()));
            job.setFinishedAt(now());
            syncJobRepository.save(job);
            return;
        }

        Map<String, Object> safe = result == null ? Map.of() : result;
        persistenceService.persistSyncResult(job, safe);

        Map<String, Object> summary = readMap(safe.get("summary"));
        if (summary.isEmpty()) {
            summary = readMap(safe.get("result_summary"));
        }
        if (summary.isEmpty()) {
            summary = Map.of("products_count", sizeOf(safe.get("products")));
        }

        boolean partial = NEEDS_PRODUCT_ROWS.contains(job.getScope()) && extractProductsCount(summary) <= 0;
        job.setStatus(partial ? "partial" : "success");
        if (partial) {
            job.setErrorCode(AppErrorCode.AMAZON_NO_PRODUCT_ROWS.getCode());
            job.setErrorMessage(AppErrorCode.AMAZON_NO_PRODUCT_ROWS.getUserMessage());
        } else {
            job.setErrorCode(null);
            job.setErrorMessage(null);
        }
        job.setResultSummary(writeJson(summary));
        job.setFinishedAt(now());
        syncJobRepository.save(job);
    }

    private List<PlatformAccount> resolveTargets(Long tenantId, String platformAccountId) {
        List<PlatformAccount> source;
        if (platformAccountId != null && !platformAccountId.isBlank()) {
            PlatformAccount one = platformAccountRepository.findByIdAndTenantId(platformAccountId, tenantId)
                    .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, AppErrorCode.ACCOUNT_NOT_FOUND.getUserMessage()));
            source = List.of(one);
        } else {
            source = platformAccountRepository.findByTenantIdAndPlatformOrderByBoundAtDesc(tenantId, "amazon");
        }

        Map<String, PlatformAccount> deduped = new LinkedHashMap<>();
        for (PlatformAccount account : source) {
            if (!"amazon".equalsIgnoreCase(account.getPlatform())) {
                continue;
            }
            String external = account.getExternalShopId() == null ? "" : account.getExternalShopId().trim();
            String key = external.isBlank() ? account.getId() : external;
            deduped.putIfAbsent(key, account);
        }
        return new ArrayList<>(deduped.values());
    }

    private void enqueueAgentTask(Long tenantId, String taskId, String scope, PlatformAccount account) {
        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("scope", scope);
        payload.put("platform", "amazon");
        payload.put("platform_account_id", account.getId());
        payload.put("external_shop_id", defaultText(account.getExternalShopId(), ""));
        payload.put("store_name", defaultText(account.getStoreName(), ""));

        jdbc.update(
                """
                INSERT INTO agent_task (
                  id, tenant_id, agent_id, task_type, status, payload_json, result_json,
                  error_code, error_message, created_at, started_at, finished_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                taskId, tenantId, "", "amazon_sync", "pending",
                writeJson(payload), "{}", "", "", now(), "", ""
        );
    }

    private String normalizeScope(String scope) {
        String s = scope == null || scope.isBlank() ? "account_health" : scope.trim().toLowerCase(Locale.ROOT);
        return switch (s) {
            case "account_health", "daily", "insights", "reports" -> s;
            default -> throw new ResponseStatusException(HttpStatus.BAD_REQUEST, AppErrorCode.BAD_REQUEST.getUserMessage());
        };
    }

    private boolean isStale(AmazonSyncJob job) {
        LocalDateTime base = parseTime("running".equals(job.getStatus()) ? job.getStartedAt() : job.getCreatedAt());
        if (base == null) {
            return true;
        }
        long ttl = "running".equals(job.getStatus()) ? RUNNING_TTL_SECONDS : PENDING_TTL_SECONDS;
        return base.plusSeconds(ttl).isBefore(LocalDateTime.now());
    }

    private void markStaleJobFailed(AmazonSyncJob job) {
        job.setStatus("failed");
        job.setErrorCode(AppErrorCode.CRAWL_INTERRUPTED.getCode());
        job.setErrorMessage(AppErrorCode.CRAWL_INTERRUPTED.getUserMessage());
        job.setFinishedAt(now());
        syncJobRepository.save(job);
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

    private Map<String, Object> jobDto(AmazonSyncJob job) {
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("job_id", job.getId());
        out.put("platform_account_id", job.getPlatformAccountId());
        out.put("agent_task_id", job.getAgentTaskId());
        out.put("scope", job.getScope());
        out.put("status", job.getStatus());
        out.put("mode", job.getMode());
        return out;
    }

    private Map<String, Object> readMap(Object value) {
        if (value instanceof Map<?, ?> map) {
            Map<String, Object> out = new LinkedHashMap<>();
            for (Map.Entry<?, ?> e : map.entrySet()) {
                out.put(String.valueOf(e.getKey()), e.getValue());
            }
            return out;
        }
        if (value instanceof String text && !text.isBlank()) {
            try {
                return objectMapper.readValue(text, new TypeReference<>() {});
            } catch (Exception ignored) {
                return Map.of();
            }
        }
        return Map.of();
    }

    private String writeJson(Object value) {
        try {
            return objectMapper.writeValueAsString(value);
        } catch (Exception ex) {
            return "{}";
        }
    }

    private int extractProductsCount(Map<String, Object> summary) {
        Object val = summary.get("products_count");
        if (val == null) {
            val = summary.get("productsCount");
        }
        if (val instanceof Number n) {
            return n.intValue();
        }
        if (val instanceof String text) {
            try {
                return Integer.parseInt(text.trim());
            } catch (Exception ignored) {
                return 0;
            }
        }
        return 0;
    }

    private int sizeOf(Object value) {
        return value instanceof Collection<?> c ? c.size() : 0;
    }

    private String defaultText(String text, String fallback) {
        return text == null || text.isBlank() ? fallback : text;
    }

    private String now() {
        return LocalDateTime.now().format(TS);
    }
}
