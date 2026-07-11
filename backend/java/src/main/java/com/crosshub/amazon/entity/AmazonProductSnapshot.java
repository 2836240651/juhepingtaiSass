package com.crosshub.amazon.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "amazon_product_snapshot")
public class AmazonProductSnapshot {
    @Id
    private String id;

    @Column(name = "tenant_id", nullable = false)
    private Long tenantId;

    @Column(name = "platform_account_id", nullable = false)
    private String platformAccountId;

    @Column(nullable = false)
    private String asin = "";

    @Column(nullable = false)
    private String sku = "";

    @Column(name = "product_name", nullable = false)
    private String productName = "";

    @Column(name = "orders_30d", nullable = false)
    private Integer orders30d = 0;

    @Column(name = "revenue_30d", nullable = false)
    private String revenue30d = "";

    @Column(name = "page_views", nullable = false)
    private Integer pageViews = 0;

    @Column(nullable = false)
    private Integer inventory = 0;

    @Column(nullable = false)
    private Double acos = 0.0;

    @Column(name = "ad_spend_30d", nullable = false)
    private String adSpend30d = "";

    @Column(name = "rank_no", nullable = false)
    private Integer rankNo = 0;

    @Column(nullable = false)
    private String currency = "USD";

    @Column(name = "synced_at", nullable = false)
    private String syncedAt;

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    public Long getTenantId() { return tenantId; }
    public void setTenantId(Long tenantId) { this.tenantId = tenantId; }
    public String getPlatformAccountId() { return platformAccountId; }
    public void setPlatformAccountId(String platformAccountId) { this.platformAccountId = platformAccountId; }
    public String getAsin() { return asin; }
    public void setAsin(String asin) { this.asin = asin; }
    public String getSku() { return sku; }
    public void setSku(String sku) { this.sku = sku; }
    public String getProductName() { return productName; }
    public void setProductName(String productName) { this.productName = productName; }
    public Integer getOrders30d() { return orders30d; }
    public void setOrders30d(Integer orders30d) { this.orders30d = orders30d; }
    public String getRevenue30d() { return revenue30d; }
    public void setRevenue30d(String revenue30d) { this.revenue30d = revenue30d; }
    public Integer getPageViews() { return pageViews; }
    public void setPageViews(Integer pageViews) { this.pageViews = pageViews; }
    public Integer getInventory() { return inventory; }
    public void setInventory(Integer inventory) { this.inventory = inventory; }
    public Double getAcos() { return acos; }
    public void setAcos(Double acos) { this.acos = acos; }
    public String getAdSpend30d() { return adSpend30d; }
    public void setAdSpend30d(String adSpend30d) { this.adSpend30d = adSpend30d; }
    public Integer getRankNo() { return rankNo; }
    public void setRankNo(Integer rankNo) { this.rankNo = rankNo; }
    public String getCurrency() { return currency; }
    public void setCurrency(String currency) { this.currency = currency; }
    public String getSyncedAt() { return syncedAt; }
    public void setSyncedAt(String syncedAt) { this.syncedAt = syncedAt; }
}
