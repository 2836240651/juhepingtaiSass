package com.crosshub.amazon.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "amazon_operational_item")
public class AmazonOperationalItem {
    @Id
    private String id;

    @Column(name = "tenant_id", nullable = false)
    private Long tenantId;

    @Column(name = "platform_account_id", nullable = false)
    private String platformAccountId;

    @Column(name = "item_type", nullable = false)
    private String itemType;

    @Column(name = "external_key", nullable = false)
    private String externalKey = "";

    @Column(name = "payload_json", nullable = false)
    private String payloadJson = "{}";

    @Column(name = "synced_at", nullable = false)
    private String syncedAt;

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    public Long getTenantId() { return tenantId; }
    public void setTenantId(Long tenantId) { this.tenantId = tenantId; }
    public String getPlatformAccountId() { return platformAccountId; }
    public void setPlatformAccountId(String platformAccountId) { this.platformAccountId = platformAccountId; }
    public String getItemType() { return itemType; }
    public void setItemType(String itemType) { this.itemType = itemType; }
    public String getExternalKey() { return externalKey; }
    public void setExternalKey(String externalKey) { this.externalKey = externalKey; }
    public String getPayloadJson() { return payloadJson; }
    public void setPayloadJson(String payloadJson) { this.payloadJson = payloadJson; }
    public String getSyncedAt() { return syncedAt; }
    public void setSyncedAt(String syncedAt) { this.syncedAt = syncedAt; }
}
