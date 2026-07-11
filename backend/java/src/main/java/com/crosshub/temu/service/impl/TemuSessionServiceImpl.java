package com.crosshub.temu.service.impl;

import com.crosshub.common.AppErrorCode;
import com.crosshub.config.CrawlerProperties;
import com.crosshub.temu.service.TemuSessionService;
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
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Executor;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

@Service
public class TemuSessionServiceImpl implements TemuSessionService {
    private final DataScopeService dataScopeService;
    private final CrawlerProperties crawlerProperties;
    private final ObjectMapper objectMapper;
    private final Executor crawlExecutor;

    public TemuSessionServiceImpl(
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
    public java.util.Map<String, Object> getSessionStatus() {
        Long tenantId = dataScopeService.requireTenantId();
        JsonNode json = runPythonJson(tenantId, "seller_session_status.py", List.of("--cache-only"));
        if (json == null || !json.isObject()) {
            return java.util.Map.of(
                    "ready", false,
                    "logged_in", false,
                    "profile_busy", false,
                    "mall_id", "",
                    "mall_count", 0,
                    "malls", java.util.List.of(),
                    "message", "未检测到会话"
            );
        }
        return objectMapper.convertValue(json, new com.fasterxml.jackson.core.type.TypeReference<>() {});
    }

    @Override
    public java.util.Map<String, Object> openLoginWindow() {
        Long tenantId = dataScopeService.requireTenantId();
        JsonNode json = runPythonJson(tenantId, "seller_login.py", List.of("--open-only"));
        if (json == null || !json.isObject()) {
            return java.util.Map.of("opened", true, "tenant_id", tenantId);
        }
        return objectMapper.convertValue(json, new com.fasterxml.jackson.core.type.TypeReference<>() {});
    }

    private JsonNode runPythonJson(Long tenantId, String script, List<String> extraArgs) {
        Path scriptDir = Path.of(crawlerProperties.getScriptDir()).toAbsolutePath().normalize();
        if (!Files.isDirectory(scriptDir)) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, AppErrorCode.CRAWL_SCRIPT_MISSING.getUserMessage());
        }
        List<String> command = new ArrayList<>();
        command.add(crawlerProperties.getPythonExecutable());
        command.add(script);
        command.add("--tenant-id");
        command.add(String.valueOf(tenantId));
        command.add("--json");
        if (extraArgs != null) {
            command.addAll(extraArgs);
        }

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

            boolean finished = process.waitFor(Math.max(30, crawlerProperties.getTimeoutSeconds()), TimeUnit.SECONDS);
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

            for (String line : stdout.split("\\R")) {
                String trimmed = line.trim();
                if (!trimmed.startsWith("{")) continue;
                try {
                    return objectMapper.readTree(trimmed);
                } catch (Exception ignored) {
                    // try next line
                }
            }
            return null;
        } catch (ResponseStatusException ex) {
            throw ex;
        } catch (Exception ex) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, AppErrorCode.CRAWL_PROCESS_FAILED.getUserMessage());
        }
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

