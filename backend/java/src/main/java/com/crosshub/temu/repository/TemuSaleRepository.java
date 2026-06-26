package com.crosshub.temu.repository;

import com.crosshub.temu.entity.TemuSale;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;

public interface TemuSaleRepository extends JpaRepository<TemuSale, Long> {
    @Query("SELECT MAX(s.reportTime) FROM TemuSale s WHERE s.tenantId = :tenantId")
    String findLatestReportTimeByTenantId(@Param("tenantId") Long tenantId);

    List<TemuSale> findByTenantIdAndReportTime(Long tenantId, String reportTime);

    List<TemuSale> findByTenantIdAndReportTimeAndShopId(Long tenantId, String reportTime, String shopId);

    List<TemuSale> findByTenantIdAndReportTimeAndShopIdIn(Long tenantId, String reportTime, List<String> shopIds);
}
