package com.crosshub.temu.service.impl;

import com.crosshub.common.AppErrorCode;
import com.crosshub.config.CrawlerProperties;
import com.crosshub.temu.dto.TemuCompetitorDiscoverRequest;
import com.crosshub.temu.service.TemuCompetitorService;
import com.crosshub.tenant.service.DataScopeService;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Executor;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

@Service
public class TemuCompetitorServiceImpl implements TemuCompetitorService {
    private static final int DISCOVER_TIMEOUT_SECONDS = 90;

    private final DataScopeService dataScopeService;
    private final CrawlerProperties crawlerProperties;
    private final ObjectMapper objectMapper;
    private final Executor crawlExecutor;

    public TemuCompetitorServiceImpl(
            DataScopeService dataScopeService,
            CrawlerProperties crawlerProperties,
            ObjectMapper objectMapper,
            @Qualifier("crawlExecutor") Executor crawlExecutor
    ) {
        this.dataScopeService = dataScopeService;
        this.crawlerProperties = crawlerProperties;
        this.objectMapper = objectMapper;
        this.crawlExecutor = crawlExecutor;
    }

    @Override
    public Map<String, Object> discoverCandidates(TemuCompetitorDiscoverRequest request) {
        Long tenantId = dataScopeService.requireTenantId();
        String keyword = request == null || request.keyword() == null || request.keyword().isBlank()
                ? "fishing tackle"
                : request.keyword().trim();
        String region = request == null || request.region() == null || request.region().isBlank()
                ? "za"
                : request.region().trim();
        int limit = request == null || request.limit() == null || request.limit() <= 0 ? 10 : request.limit();

        Path scriptDir = Path.of(crawlerProperties.getScriptDir()).toAbsolutePath().normalize();
        if (!Files.isDirectory(scriptDir)) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, AppErrorCode.CRAWL_SCRIPT_MISSING.getUserMessage());
        }

        List<String> command = new ArrayList<>();
        command.add(crawlerProperties.getPythonExecutable());
        command.add("competitor_discover.py");
        command.add("--tenant-id");
        command.add(String.valueOf(tenantId));
        command.add("--keyword");
        command.add(keyword);
        command.add("--region");
        command.add(region);
        command.add("--limit");
        command.add(String.valueOf(limit));
        command.add("--json");

        ProcessBuilder builder = new ProcessBuilder(command);
        builder.directory(scriptDir.toFile());
        builder.environment().put("TENANT_ID", String.valueOf(tenantId));
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

            boolean finished = process.waitFor(DISCOVER_TIMEOUT_SECONDS, TimeUnit.SECONDS);
            if (!finished) {
                process.destroyForcibly();
                stdoutFuture.cancel(true);
                stderrFuture.cancel(true);
                throw new ResponseStatusException(HttpStatus.BAD_REQUEST, AppErrorCode.CRAWL_TIMEOUT.getUserMessage());
            }

            String stdout = "";
            String stderr = "";
            try { stdout = stdoutFuture.get(2, TimeUnit.SECONDS); } catch (TimeoutException ignored) { stdoutFuture.cancel(true); }
            try { stderr = stderrFuture.get(2, TimeUnit.SECONDS); } catch (TimeoutException ignored) { stderrFuture.cancel(true); }

            if (process.exitValue() != 0) {
                AppErrorCode code = AppErrorCode.classifyCrawlRaw(stderr + "\n" + stdout);
                throw new ResponseStatusException(HttpStatus.BAD_REQUEST, code.getUserMessage());
            }

            JsonNode json = parseJsonLine(stdout);
            if (json == null || !json.isObject()) {
                Map<String, Object> fallback = new LinkedHashMap<>();
                fallback.put("keyword", keyword);
                fallback.put("region", region);
                fallback.put("candidates", List.of());
                return fallback;
            }
            return objectMapper.convertValue(json, new com.fasterxml.jackson.core.type.TypeReference<>() {});
        } catch (ResponseStatusException ex) {
            throw ex;
        } catch (Exception ex) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, AppErrorCode.CRAWL_PROCESS_FAILED.getUserMessage());
        }
    }

    private JsonNode parseJsonLine(String stdout) {
        if (stdout == null || stdout.isBlank()) return null;
        for (String line : stdout.split("\\R")) {
            String trimmed = line.trim();
            if (!trimmed.startsWith("{")) continue;
            try {
                return objectMapper.readTree(trimmed);
            } catch (Exception ignored) {
                // continue
            }
        }
        return null;
    }

    private String safeReadStream(java.io.InputStream stream) {
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(stream, StandardCharsets.UTF_8))) {
            StringBuilder sb = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                if (!sb.isEmpty()) sb.append(System.lineSeparator());
                sb.append(line);
            }
            return sb.toString();
        } catch (Exception ex) {
            return "";
        }
    }
}
