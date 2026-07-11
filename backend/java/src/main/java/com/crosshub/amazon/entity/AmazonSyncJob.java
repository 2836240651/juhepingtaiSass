package com.crosshub.amazon.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "amazon_sync_job")
public class AmazonSyncJob {
    @Id
    private String id;

    @Column(name = "tenant_id", nullable = false)
    private Long tenantId;

    @Column(name = "platform_account_id", nullable = false)
    private String platformAccountId;

    @Column(name = "agent_task_id", nullable = false)
    private String agentTaskId = "";

    @Column(name = "agent_id", nullable = false)
    private String agentId = "";

    @Column(nullable = false)
    private String scope;

    @Column(nullable = false)
    private String status;

    @Column(nullable = false)
    private String mode = "ziniao_webdriver";

    @Column(name = "error_code", nullable = false)
    private String errorCode = "";

    @Column(name = "error_message", nullable = false)
    private String errorMessage = "";

    @Column(name = "result_summary", nullable = false)
    private String resultSummary = "";

    @Column(name = "created_at", nullable = false)
    private String createdAt;

    @Column(name = "started_at", nullable = false)
    private String startedAt = "";

    @Column(name = "finished_at", nullable = false)
    private String finishedAt = "";

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    public Long getTenantId() { return tenantId; }
    public void setTenantId(Long tenantId) { this.tenantId = tenantId; }
    public String getPlatformAccountId() { return platformAccountId; }
    public void setPlatformAccountId(String platformAccountId) { this.platformAccountId = platformAccountId; }
    public String getAgentTaskId() { return agentTaskId; }
    public void setAgentTaskId(String agentTaskId) { this.agentTaskId = agentTaskId; }
    public String getAgentId() { return agentId; }
    public void setAgentId(String agentId) { this.agentId = agentId; }
    public String getScope() { return scope; }
    public void setScope(String scope) { this.scope = scope; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public String getMode() { return mode; }
    public void setMode(String mode) { this.mode = mode; }
    public String getErrorCode() { return errorCode; }
    public void setErrorCode(String errorCode) { this.errorCode = errorCode; }
    public String getErrorMessage() { return errorMessage; }
    public void setErrorMessage(String errorMessage) { this.errorMessage = errorMessage; }
    public String getResultSummary() { return resultSummary; }
    public void setResultSummary(String resultSummary) { this.resultSummary = resultSummary; }
    public String getCreatedAt() { return createdAt; }
    public void setCreatedAt(String createdAt) { this.createdAt = createdAt; }
    public String getStartedAt() { return startedAt; }
    public void setStartedAt(String startedAt) { this.startedAt = startedAt; }
    public String getFinishedAt() { return finishedAt; }
    public void setFinishedAt(String finishedAt) { this.finishedAt = finishedAt; }
}
