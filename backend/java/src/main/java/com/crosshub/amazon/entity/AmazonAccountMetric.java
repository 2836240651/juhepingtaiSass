package com.crosshub.amazon.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "amazon_account_metric")
public class AmazonAccountMetric {
    @Id
    private String id;

    @Column(name = "tenant_id", nullable = false)
    private Long tenantId;

    @Column(name = "platform_account_id", nullable = false)
    private String platformAccountId;

    @Column(name = "metric_key", nullable = false)
    private String metricKey;

    @Column(name = "metric_label", nullable = false)
    private String metricLabel = "";

    @Column(nullable = false)
    private String status = "normal";

    @Column(name = "value_text", nullable = false)
    private String valueText = "";

    @Column(name = "threshold_text", nullable = false)
    private String thresholdText = "";

    @Column(nullable = false)
    private String trend = "stable";

    @Column(name = "note_text", nullable = false)
    private String noteText = "";

    @Column(name = "synced_at", nullable = false)
    private String syncedAt;

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    public Long getTenantId() { return tenantId; }
    public void setTenantId(Long tenantId) { this.tenantId = tenantId; }
    public String getPlatformAccountId() { return platformAccountId; }
    public void setPlatformAccountId(String platformAccountId) { this.platformAccountId = platformAccountId; }
    public String getMetricKey() { return metricKey; }
    public void setMetricKey(String metricKey) { this.metricKey = metricKey; }
    public String getMetricLabel() { return metricLabel; }
    public void setMetricLabel(String metricLabel) { this.metricLabel = metricLabel; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public String getValueText() { return valueText; }
    public void setValueText(String valueText) { this.valueText = valueText; }
    public String getThresholdText() { return thresholdText; }
    public void setThresholdText(String thresholdText) { this.thresholdText = thresholdText; }
    public String getTrend() { return trend; }
    public void setTrend(String trend) { this.trend = trend; }
    public String getNoteText() { return noteText; }
    public void setNoteText(String noteText) { this.noteText = noteText; }
    public String getSyncedAt() { return syncedAt; }
    public void setSyncedAt(String syncedAt) { this.syncedAt = syncedAt; }
}
