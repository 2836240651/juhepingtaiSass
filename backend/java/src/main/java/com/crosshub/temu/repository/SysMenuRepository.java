package com.crosshub.temu.repository;

import com.crosshub.temu.entity.SysMenu;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface SysMenuRepository extends JpaRepository<SysMenu, String> {
    List<SysMenu> findByPortalOrderBySortOrderAsc(String portal);
}
