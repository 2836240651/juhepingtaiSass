package com.crosshub.temu.entity;

import jakarta.persistence.*;

@Entity
@Table(
        name = "user_shop_scope",
        uniqueConstraints = @UniqueConstraint(columnNames = {"tenant_id", "user_id", "platform", "shop_id"})
)
public class UserShopScope {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "tenant_id", nullable = false)
    private Long tenantId;

    @Column(name = "user_id", nullable = false)
    private Long userId;

    @Column(nullable = false, length = 32)
    private String platform;

    @Column(name = "shop_id", nullable = false, length = 128)
    private String shopId;

    public Long getId() { return id; }
    public Long getTenantId() { return tenantId; }
    public void setTenantId(Long tenantId) { this.tenantId = tenantId; }
    public Long getUserId() { return userId; }
    public void setUserId(Long userId) { this.userId = userId; }
    public String getPlatform() { return platform; }
    public void setPlatform(String platform) { this.platform = platform; }
    public String getShopId() { return shopId; }
    public void setShopId(String shopId) { this.shopId = shopId; }
}
