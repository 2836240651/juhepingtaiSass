package com.crosshub.tenant.repository;

import com.crosshub.tenant.entity.SysMenu;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface SysMenuRepository extends JpaRepository<SysMenu, String> {
    List<SysMenu> findByPortalOrderBySortOrderAsc(String portal);
}
