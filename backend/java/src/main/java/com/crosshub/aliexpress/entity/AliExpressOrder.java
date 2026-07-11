package com.crosshub.aliexpress.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "aliexpress_order")
public class AliExpressOrder {
    @Id
    private String id;

    @Column(name = "tenant_id", nullable = false)
    private Long tenantId;

    @Column(name = "store_id", nullable = false)
    private String storeId;

    @Column(name = "store_name", nullable = false)
    private String storeName = "";

    @Column(name = "report_day", nullable = false)
    private String reportDay;

    @Column(name = "order_no", nullable = false)
    private String orderNo;

    @Column(name = "fulfillment_type", nullable = false)
    private String fulfillmentType;

    @Column(nullable = false)
    private String sku = "";

    @Column(name = "product_name", nullable = false)
    private String productName = "";

    @Column(nullable = false)
    private Integer quantity = 0;

    @Column(nullable = false)
    private Double amount = 0d;

    @Column(nullable = false)
    private String currency = "USD";

    @Column(nullable = false)
    private String country = "";

    @Column(nullable = false)
    private String status = "";

    @Column(name = "ordered_at", nullable = false)
    private String orderedAt = "";

    @Column(name = "ship_deadline")
    private String shipDeadline;

    @Column(name = "warehouse_name")
    private String warehouseName;

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    public Long getTenantId() { return tenantId; }
    public void setTenantId(Long tenantId) { this.tenantId = tenantId; }
    public String getStoreId() { return storeId; }
    public void setStoreId(String storeId) { this.storeId = storeId; }
    public String getStoreName() { return storeName; }
    public void setStoreName(String storeName) { this.storeName = storeName == null ? "" : storeName; }
    public String getReportDay() { return reportDay; }
    public void setReportDay(String reportDay) { this.reportDay = reportDay; }
    public String getOrderNo() { return orderNo; }
    public void setOrderNo(String orderNo) { this.orderNo = orderNo; }
    public String getFulfillmentType() { return fulfillmentType; }
    public void setFulfillmentType(String fulfillmentType) { this.fulfillmentType = fulfillmentType; }
    public String getSku() { return sku; }
    public void setSku(String sku) { this.sku = sku == null ? "" : sku; }
    public String getProductName() { return productName; }
    public void setProductName(String productName) { this.productName = productName == null ? "" : productName; }
    public Integer getQuantity() { return quantity; }
    public void setQuantity(Integer quantity) { this.quantity = quantity == null ? 0 : quantity; }
    public Double getAmount() { return amount; }
    public void setAmount(Double amount) { this.amount = amount == null ? 0d : amount; }
    public String getCurrency() { return currency; }
    public void setCurrency(String currency) { this.currency = currency == null || currency.isBlank() ? "USD" : currency; }
    public String getCountry() { return country; }
    public void setCountry(String country) { this.country = country == null ? "" : country; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status == null ? "" : status; }
    public String getOrderedAt() { return orderedAt; }
    public void setOrderedAt(String orderedAt) { this.orderedAt = orderedAt == null ? "" : orderedAt; }
    public String getShipDeadline() { return shipDeadline; }
    public void setShipDeadline(String shipDeadline) { this.shipDeadline = shipDeadline; }
    public String getWarehouseName() { return warehouseName; }
    public void setWarehouseName(String warehouseName) { this.warehouseName = warehouseName; }
}

