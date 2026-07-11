package com.crosshub.tenant.repository;

import com.crosshub.tenant.entity.UserPlatformScope;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface UserPlatformScopeRepository extends JpaRepository<UserPlatformScope, Long> {
    List<UserPlatformScope> findByTenantIdAndUserId(Long tenantId, Long userId);

    void deleteByTenantIdAndUserId(Long tenantId, Long userId);
}
