package com.crosshub.aliexpress.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "aliexpress_hot_broadcast_read")
public class AliExpressHotBroadcastRead {
    @Id
    private String id;

    @Column(name = "tenant_id", nullable = false)
    private Long tenantId;

    @Column(name = "broadcast_id", nullable = false)
    private String broadcastId;

    @Column(name = "reader_id", nullable = false)
    private String readerId = "";

    @Column(name = "reader_name", nullable = false)
    private String readerName = "";

    @Column(name = "read_at", nullable = false)
    private String readAt;

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    public Long getTenantId() { return tenantId; }
    public void setTenantId(Long tenantId) { this.tenantId = tenantId; }
    public String getBroadcastId() { return broadcastId; }
    public void setBroadcastId(String broadcastId) { this.broadcastId = broadcastId; }
    public String getReaderId() { return readerId; }
    public void setReaderId(String readerId) { this.readerId = readerId == null ? "" : readerId; }
    public String getReaderName() { return readerName; }
    public void setReaderName(String readerName) { this.readerName = readerName == null ? "" : readerName; }
    public String getReadAt() { return readAt; }
    public void setReadAt(String readAt) { this.readAt = readAt; }
}

