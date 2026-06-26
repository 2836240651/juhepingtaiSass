package com.crosshub.temu.repository;

import com.crosshub.temu.entity.TenantFeature;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface TenantFeatureRepository extends JpaRepository<TenantFeature, Long> {
    List<TenantFeature> findByTenantIdAndEnabled(Long tenantId, Integer enabled);
}
