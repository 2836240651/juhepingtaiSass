package com.crosshub.aliexpress.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "aliexpress_product")
public class AliExpressProduct {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "tenant_id", nullable = false)
    private Long tenantId;

    @Column(name = "store_id", nullable = false)
    private String storeId;

    @Column(name = "store_name", nullable = false)
    private String storeName = "";

    @Column(name = "report_day", nullable = false)
    private String reportDay;

    @Column(nullable = false)
    private String sku;

    @Column(nullable = false)
    private String name = "";

    @Column(nullable = false)
    private String category = "";

    @Column(name = "selling_price", nullable = false)
    private Double sellingPrice = 0d;

    @Column(name = "cost_price", nullable = false)
    private Double costPrice = 0d;

    @Column(name = "platform_fee_rate", nullable = false)
    private Double platformFeeRate = 0d;

    @Column(name = "logistics_fee", nullable = false)
    private Double logisticsFee = 0d;

    @Column(name = "official_stock", nullable = false)
    private Integer officialStock = 0;

    @Column(name = "local_stock", nullable = false)
    private Integer localStock = 0;

    @Column(name = "days_without_sale", nullable = false)
    private Integer daysWithoutSale = 0;

    @Column(name = "daily_sales", nullable = false)
    private Integer dailySales = 0;

    @Column(name = "sales_last7_days", nullable = false)
    private String salesLast7Days = "[]";

    @Column(nullable = false)
    private String owner = "";

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public Long getTenantId() { return tenantId; }
    public void setTenantId(Long tenantId) { this.tenantId = tenantId; }
    public String getStoreId() { return storeId; }
    public void setStoreId(String storeId) { this.storeId = storeId; }
    public String getStoreName() { return storeName; }
    public void setStoreName(String storeName) { this.storeName = storeName == null ? "" : storeName; }
    public String getReportDay() { return reportDay; }
    public void setReportDay(String reportDay) { this.reportDay = reportDay; }
    public String getSku() { return sku; }
    public void setSku(String sku) { this.sku = sku; }
    public String getName() { return name; }
    public void setName(String name) { this.name = name == null ? "" : name; }
    public String getCategory() { return category; }
    public void setCategory(String category) { this.category = category == null ? "" : category; }
    public Double getSellingPrice() { return sellingPrice; }
    public void setSellingPrice(Double sellingPrice) { this.sellingPrice = sellingPrice == null ? 0d : sellingPrice; }
    public Double getCostPrice() { return costPrice; }
    public void setCostPrice(Double costPrice) { this.costPrice = costPrice == null ? 0d : costPrice; }
    public Double getPlatformFeeRate() { return platformFeeRate; }
    public void setPlatformFeeRate(Double platformFeeRate) { this.platformFeeRate = platformFeeRate == null ? 0d : platformFeeRate; }
    public Double getLogisticsFee() { return logisticsFee; }
    public void setLogisticsFee(Double logisticsFee) { this.logisticsFee = logisticsFee == null ? 0d : logisticsFee; }
    public Integer getOfficialStock() { return officialStock; }
    public void setOfficialStock(Integer officialStock) { this.officialStock = officialStock == null ? 0 : officialStock; }
    public Integer getLocalStock() { return localStock; }
    public void setLocalStock(Integer localStock) { this.localStock = localStock == null ? 0 : localStock; }
    public Integer getDaysWithoutSale() { return daysWithoutSale; }
    public void setDaysWithoutSale(Integer daysWithoutSale) { this.daysWithoutSale = daysWithoutSale == null ? 0 : daysWithoutSale; }
    public Integer getDailySales() { return dailySales; }
    public void setDailySales(Integer dailySales) { this.dailySales = dailySales == null ? 0 : dailySales; }
    public String getSalesLast7Days() { return salesLast7Days; }
    public void setSalesLast7Days(String salesLast7Days) { this.salesLast7Days = salesLast7Days == null ? "[]" : salesLast7Days; }
    public String getOwner() { return owner; }
    public void setOwner(String owner) { this.owner = owner == null ? "" : owner; }
}

