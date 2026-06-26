package com.crosshub.temu.entity;

import jakarta.persistence.*;

@Entity
@Table(name = "temu_shop")
public class TemuShop {
    @Id
    @Column(name = "shop_id")
    private String shopId;

    @Column(name = "tenant_id")
    private Long tenantId;

    @Column(name = "shop_name")
    private String shopName;

    @Column(name = "is_upload")
    private Integer isUpload;

    public String getShopId() { return shopId; }
    public void setShopId(String shopId) { this.shopId = shopId; }
    public Long getTenantId() { return tenantId; }
    public void setTenantId(Long tenantId) { this.tenantId = tenantId; }
    public String getShopName() { return shopName; }
    public boolean isUpload() { return isUpload != null && isUpload == 1; }
}
