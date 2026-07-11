package com.crosshub.amazon.repository;

import com.crosshub.amazon.entity.AmazonOperationalItem;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Collection;
import java.util.List;

public interface AmazonOperationalItemRepository extends JpaRepository<AmazonOperationalItem, String> {
    List<AmazonOperationalItem> findByTenantIdAndPlatformAccountIdInAndItemTypeInOrderBySyncedAtDesc(
            Long tenantId,
            Collection<String> platformAccountIds,
            Collection<String> itemTypes
    );
    void deleteByTenantIdAndPlatformAccountIdAndItemType(Long tenantId, String platformAccountId, String itemType);
}
