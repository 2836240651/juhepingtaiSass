package com.crosshub.temu.repository;

import com.crosshub.temu.entity.TemuShop;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface TemuShopRepository extends JpaRepository<TemuShop, String> {
    List<TemuShop> findByTenantId(Long tenantId);

    List<TemuShop> findByTenantIdAndShopIdIn(Long tenantId, List<String> shopIds);
}
