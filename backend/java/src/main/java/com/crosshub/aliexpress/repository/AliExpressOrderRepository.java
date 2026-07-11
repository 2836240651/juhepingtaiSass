package com.crosshub.aliexpress.repository;

import com.crosshub.aliexpress.entity.AliExpressOrder;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface AliExpressOrderRepository extends JpaRepository<AliExpressOrder, String> {
    List<AliExpressOrder> findByTenantIdAndReportDayOrderByOrderedAtDesc(Long tenantId, String reportDay);

    List<AliExpressOrder> findByTenantIdAndReportDayAndStoreIdOrderByOrderedAtDesc(Long tenantId, String reportDay, String storeId);
}

