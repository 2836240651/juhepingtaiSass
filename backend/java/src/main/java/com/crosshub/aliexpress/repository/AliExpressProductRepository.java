package com.crosshub.aliexpress.repository;

import com.crosshub.aliexpress.entity.AliExpressProduct;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface AliExpressProductRepository extends JpaRepository<AliExpressProduct, Long> {
    List<AliExpressProduct> findByTenantIdAndReportDayOrderByDailySalesDesc(Long tenantId, String reportDay);

    List<AliExpressProduct> findByTenantIdAndReportDayAndStoreIdOrderByDailySalesDesc(Long tenantId, String reportDay, String storeId);
}

