package com.crosshub.temu.repository;

import com.crosshub.temu.entity.UserShopScope;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface UserShopScopeRepository extends JpaRepository<UserShopScope, Long> {
    List<UserShopScope> findByTenantIdAndUserId(Long tenantId, Long userId);

    void deleteByTenantIdAndUserId(Long tenantId, Long userId);
}
