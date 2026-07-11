package com.crosshub.aliexpress.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "aliexpress_hot_broadcast")
public class AliExpressHotBroadcast {
    @Id
    private String id;

    @Column(name = "tenant_id", nullable = false)
    private Long tenantId;

    @Column(name = "store_id", nullable = false)
    private String storeId;

    @Column(nullable = false)
    private String sku = "";

    @Column(name = "product_name", nullable = false)
    private String productName = "";

    @Column(name = "daily_sales", nullable = false)
    private Integer dailySales = 0;

    @Column(nullable = false)
    private String message = "";

    @Column(name = "avg7_day_daily", nullable = false)
    private Double avg7DayDaily = 0d;

    @Column(name = "surge_ratio", nullable = false)
    private Double surgeRatio = 0d;

    @Column(name = "operator_name", nullable = false)
    private String operatorName = "";

    @Column(nullable = false)
    private String source = "manual";

    @Column(name = "broadcast_at", nullable = false)
    private String broadcastAt = "";

    @Column(name = "created_at", nullable = false)
    private String createdAt = "";

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    public Long getTenantId() { return tenantId; }
    public void setTenantId(Long tenantId) { this.tenantId = tenantId; }
    public String getStoreId() { return storeId; }
    public void setStoreId(String storeId) { this.storeId = storeId; }
    public String getSku() { return sku; }
    public void setSku(String sku) { this.sku = sku == null ? "" : sku; }
    public String getProductName() { return productName; }
    public void setProductName(String productName) { this.productName = productName == null ? "" : productName; }
    public Integer getDailySales() { return dailySales; }
    public void setDailySales(Integer dailySales) { this.dailySales = dailySales == null ? 0 : dailySales; }
    public String getMessage() { return message; }
    public void setMessage(String message) { this.message = message == null ? "" : message; }
    public Double getAvg7DayDaily() { return avg7DayDaily; }
    public void setAvg7DayDaily(Double avg7DayDaily) { this.avg7DayDaily = avg7DayDaily == null ? 0d : avg7DayDaily; }
    public Double getSurgeRatio() { return surgeRatio; }
    public void setSurgeRatio(Double surgeRatio) { this.surgeRatio = surgeRatio == null ? 0d : surgeRatio; }
    public String getOperatorName() { return operatorName; }
    public void setOperatorName(String operatorName) { this.operatorName = operatorName == null ? "" : operatorName; }
    public String getSource() { return source; }
    public void setSource(String source) { this.source = source == null || source.isBlank() ? "manual" : source; }
    public String getBroadcastAt() { return broadcastAt; }
    public void setBroadcastAt(String broadcastAt) { this.broadcastAt = broadcastAt == null ? "" : broadcastAt; }
    public String getCreatedAt() { return createdAt; }
    public void setCreatedAt(String createdAt) { this.createdAt = createdAt == null ? "" : createdAt; }
}

