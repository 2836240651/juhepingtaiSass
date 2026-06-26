package com.crosshub.temu.repository;

import com.crosshub.temu.entity.AppUser;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface AppUserRepository extends JpaRepository<AppUser, Long> {
    Optional<AppUser> findByUsernameIgnoreCase(String username);

    List<AppUser> findByTenantIdAndRoleOrderByIdAsc(Long tenantId, String role);

    Optional<AppUser> findByIdAndTenantId(Long id, Long tenantId);

    boolean existsByUsernameIgnoreCase(String username);

    boolean existsByUsernameIgnoreCaseAndIdNot(String username, Long id);
}
