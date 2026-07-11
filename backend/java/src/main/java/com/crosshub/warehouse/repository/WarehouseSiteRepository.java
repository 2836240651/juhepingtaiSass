package com.crosshub.warehouse.repository;

import com.crosshub.warehouse.entity.WarehouseSite;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface WarehouseSiteRepository extends JpaRepository<WarehouseSite, String> {
    List<WarehouseSite> findByTenantIdOrderBySortOrderAscNameAsc(Long tenantId);

    List<WarehouseSite> findByTenantIdAndStatusOrderBySortOrderAscNameAsc(Long tenantId, String status);

    Optional<WarehouseSite> findByIdAndTenantId(String id, Long tenantId);

    boolean existsByTenantIdAndCodeIgnoreCase(Long tenantId, String code);

    boolean existsByTenantIdAndCodeIgnoreCaseAndIdNot(Long tenantId, String code, String id);
}
