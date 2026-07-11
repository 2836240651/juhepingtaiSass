package com.crosshub.aliexpress.repository;

import com.crosshub.aliexpress.entity.AliExpressViolation;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface AliExpressViolationRepository extends JpaRepository<AliExpressViolation, String> {
    List<AliExpressViolation> findByTenantIdOrderByViolatedAtDesc(Long tenantId);

    List<AliExpressViolation> findByTenantIdAndStoreIdOrderByViolatedAtDesc(Long tenantId, String storeId);

    Optional<AliExpressViolation> findByIdAndTenantId(String id, Long tenantId);
}

