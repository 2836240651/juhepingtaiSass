package com.crosshub.amazon.repository;

import com.crosshub.amazon.entity.AmazonProductSnapshot;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Collection;
import java.util.List;

public interface AmazonProductSnapshotRepository extends JpaRepository<AmazonProductSnapshot, String> {
    List<AmazonProductSnapshot> findByTenantIdAndPlatformAccountIdInOrderBySyncedAtDesc(Long tenantId, Collection<String> platformAccountIds);
    void deleteByTenantIdAndPlatformAccountId(Long tenantId, String platformAccountId);
}
