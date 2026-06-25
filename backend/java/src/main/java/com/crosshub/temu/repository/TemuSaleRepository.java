package com.crosshub.temu.repository;

import com.crosshub.temu.entity.TemuSale;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;

public interface TemuSaleRepository extends JpaRepository<TemuSale, Long> {
    @Query("SELECT MAX(s.reportTime) FROM TemuSale s")
    String findLatestReportTime();

    List<TemuSale> findByReportTime(String reportTime);

    List<TemuSale> findByReportTimeAndShopId(String reportTime, String shopId);

    List<TemuSale> findByReportTimeAndUserId(String reportTime, Long userId);

    List<TemuSale> findByReportTimeAndShopIdAndUserId(String reportTime, String shopId, Long userId);

    @Query("SELECT s FROM TemuSale s WHERE s.reportTime = :reportTime ORDER BY s.sonSalesSevenDays DESC")
    List<TemuSale> findByReportTimeOrderBySevenDays(@Param("reportTime") String reportTime);
}
