package com.crosshub.platform.repository;

import com.crosshub.platform.entity.PlatformAccount;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface PlatformAccountRepository extends JpaRepository<PlatformAccount, String> {
    List<PlatformAccount> findByTenantIdOrderByBoundAtDesc(Long tenantId);

    List<PlatformAccount> findByTenantIdAndPlatformOrderByBoundAtDesc(Long tenantId, String platform);

    Optional<PlatformAccount> findByIdAndTenantId(String id, Long tenantId);

    boolean existsByTenantIdAndPlatformIgnoreCaseAndStoreNameIgnoreCaseAndIdNot(
            Long tenantId, String platform, String storeName, String id
    );

    boolean existsByTenantIdAndPlatformIgnoreCaseAndStoreNameIgnoreCase(
            Long tenantId, String platform, String storeName
    );
}
