package com.crosshub.agent.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "agent_task")
public class AgentTask {
    @Id
    private String id;

    @Column(name = "tenant_id", nullable = false)
    private Long tenantId;

    @Column(name = "agent_id", nullable = false)
    private String agentId = "";

    @Column(name = "task_type", nullable = false)
    private String taskType;

    @Column(nullable = false)
    private String status;

    @Column(name = "payload_json", nullable = false)
    private String payloadJson = "";

    @Column(name = "result_json", nullable = false)
    private String resultJson = "";

    @Column(name = "error_code", nullable = false)
    private String errorCode = "";

    @Column(name = "error_message", nullable = false)
    private String errorMessage = "";

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
    public String getAgentId() { return agentId; }
    public void setAgentId(String agentId) { this.agentId = agentId; }
    public String getTaskType() { return taskType; }
    public void setTaskType(String taskType) { this.taskType = taskType; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public String getPayloadJson() { return payloadJson; }
    public void setPayloadJson(String payloadJson) { this.payloadJson = payloadJson; }
    public String getResultJson() { return resultJson; }
    public void setResultJson(String resultJson) { this.resultJson = resultJson; }
    public String getErrorCode() { return errorCode; }
    public void setErrorCode(String errorCode) { this.errorCode = errorCode; }
    public String getErrorMessage() { return errorMessage; }
    public void setErrorMessage(String errorMessage) { this.errorMessage = errorMessage; }
    public String getCreatedAt() { return createdAt; }
    public void setCreatedAt(String createdAt) { this.createdAt = createdAt; }
    public String getStartedAt() { return startedAt; }
    public void setStartedAt(String startedAt) { this.startedAt = startedAt; }
    public String getFinishedAt() { return finishedAt; }
    public void setFinishedAt(String finishedAt) { this.finishedAt = finishedAt; }
}
