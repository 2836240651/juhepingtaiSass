package com.crosshub.aliexpress.repository;

import com.crosshub.aliexpress.entity.AliExpressHotBroadcast;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface AliExpressHotBroadcastRepository extends JpaRepository<AliExpressHotBroadcast, String> {
    List<AliExpressHotBroadcast> findByTenantIdOrderByBroadcastAtDescCreatedAtDesc(Long tenantId);

    List<AliExpressHotBroadcast> findByTenantIdAndStoreIdOrderByBroadcastAtDescCreatedAtDesc(Long tenantId, String storeId);

    Optional<AliExpressHotBroadcast> findByIdAndTenantId(String id, Long tenantId);
}

