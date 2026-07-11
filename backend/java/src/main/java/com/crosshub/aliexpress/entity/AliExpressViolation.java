package com.crosshub.aliexpress.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "aliexpress_violation")
public class AliExpressViolation {
    @Id
    private String id;

    @Column(name = "tenant_id", nullable = false)
    private Long tenantId;

    @Column(name = "store_id", nullable = false)
    private String storeId;

    @Column(name = "store_name", nullable = false)
    private String storeName = "";

    @Column(name = "type_code", nullable = false)
    private String typeCode = "";

    @Column(name = "type_label", nullable = false)
    private String typeLabel = "";

    @Column(name = "order_no", nullable = false)
    private String orderNo = "";

    @Column(nullable = false)
    private String description = "";

    @Column(name = "fine_amount", nullable = false)
    private Double fineAmount = 0d;

    @Column(nullable = false)
    private String currency = "USD";

    @Column(name = "violated_at", nullable = false)
    private String violatedAt = "";

    @Column(name = "appeal_status")
    private String appealStatus;

    @Column(name = "appeal_result")
    private String appealResult;

    @Column(nullable = false)
    private Integer confirmed = 0;

    @Column(nullable = false)
    private String severity = "medium";

    @Column(nullable = false)
    private String owner = "";

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    public Long getTenantId() { return tenantId; }
    public void setTenantId(Long tenantId) { this.tenantId = tenantId; }
    public String getStoreId() { return storeId; }
    public void setStoreId(String storeId) { this.storeId = storeId; }
    public String getStoreName() { return storeName; }
    public void setStoreName(String storeName) { this.storeName = storeName == null ? "" : storeName; }
    public String getTypeCode() { return typeCode; }
    public void setTypeCode(String typeCode) { this.typeCode = typeCode == null ? "" : typeCode; }
    public String getTypeLabel() { return typeLabel; }
    public void setTypeLabel(String typeLabel) { this.typeLabel = typeLabel == null ? "" : typeLabel; }
    public String getOrderNo() { return orderNo; }
    public void setOrderNo(String orderNo) { this.orderNo = orderNo == null ? "" : orderNo; }
    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description == null ? "" : description; }
    public Double getFineAmount() { return fineAmount; }
    public void setFineAmount(Double fineAmount) { this.fineAmount = fineAmount == null ? 0d : fineAmount; }
    public String getCurrency() { return currency; }
    public void setCurrency(String currency) { this.currency = currency == null || currency.isBlank() ? "USD" : currency; }
    public String getViolatedAt() { return violatedAt; }
    public void setViolatedAt(String violatedAt) { this.violatedAt = violatedAt == null ? "" : violatedAt; }
    public String getAppealStatus() { return appealStatus; }
    public void setAppealStatus(String appealStatus) { this.appealStatus = appealStatus; }
    public String getAppealResult() { return appealResult; }
    public void setAppealResult(String appealResult) { this.appealResult = appealResult; }
    public Integer getConfirmed() { return confirmed; }
    public void setConfirmed(Integer confirmed) { this.confirmed = confirmed == null ? 0 : confirmed; }
    public String getSeverity() { return severity; }
    public void setSeverity(String severity) { this.severity = severity == null || severity.isBlank() ? "medium" : severity; }
    public String getOwner() { return owner; }
    public void setOwner(String owner) { this.owner = owner == null ? "" : owner; }
}

