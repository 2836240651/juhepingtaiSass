package com.crosshub.warehouse.repository;

import com.crosshub.warehouse.entity.UserWarehouseScope;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface UserWarehouseScopeRepository extends JpaRepository<UserWarehouseScope, Long> {
    List<UserWarehouseScope> findByTenantIdAndUserId(Long tenantId, Long userId);

    void deleteByTenantIdAndUserId(Long tenantId, Long userId);
}
