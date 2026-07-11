package com.crosshub.amazon.repository;

import com.crosshub.amazon.entity.AmazonAccountMetric;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Collection;
import java.util.List;

public interface AmazonAccountMetricRepository extends JpaRepository<AmazonAccountMetric, String> {
    List<AmazonAccountMetric> findByTenantIdAndPlatformAccountIdInOrderBySyncedAtDesc(Long tenantId, Collection<String> platformAccountIds);
    void deleteByTenantIdAndPlatformAccountId(Long tenantId, String platformAccountId);
}
