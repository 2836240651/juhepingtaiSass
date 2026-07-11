package com.crosshub.aliexpress.repository;

import com.crosshub.aliexpress.entity.AliExpressHotBroadcastRead;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Collection;
import java.util.List;

public interface AliExpressHotBroadcastReadRepository extends JpaRepository<AliExpressHotBroadcastRead, String> {
    List<AliExpressHotBroadcastRead> findByTenantIdAndBroadcastIdInOrderByReadAtDesc(Long tenantId, Collection<String> broadcastIds);
}

