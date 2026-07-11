package com.crosshub.tenant.entity;

import jakarta.persistence.*;

@Entity
@Table(
        name = "tenant_feature",
        uniqueConstraints = @UniqueConstraint(columnNames = {"tenant_id", "feature_code"})
)
public class TenantFeature {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "tenant_id", nullable = false)
    private Long tenantId;

    @Column(name = "feature_code", nullable = false, length = 64)
    private String featureCode;

    @Column(nullable = false)
    private Integer enabled = 1;

    public Long getId() { return id; }
    public Long getTenantId() { return tenantId; }
    public void setTenantId(Long tenantId) { this.tenantId = tenantId; }
    public String getFeatureCode() { return featureCode; }
    public void setFeatureCode(String featureCode) { this.featureCode = featureCode; }
    public boolean isEnabled() { return enabled != null && enabled == 1; }
    public void setEnabled(boolean enabled) { this.enabled = enabled ? 1 : 0; }
}
