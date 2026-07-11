package com.crosshub.tenant.repository;

import com.crosshub.tenant.entity.TenantFeature;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface TenantFeatureRepository extends JpaRepository<TenantFeature, Long> {
    List<TenantFeature> findByTenantIdAndEnabled(Long tenantId, Integer enabled);

    List<TenantFeature> findByTenantId(Long tenantId);

    Optional<TenantFeature> findByTenantIdAndFeatureCode(Long tenantId, String featureCode);
}
