package com.crosshub.tenant.repository;



import com.crosshub.tenant.entity.UserMenuGrant;

import org.springframework.data.jpa.repository.JpaRepository;



import java.util.List;



public interface UserMenuGrantRepository extends JpaRepository<UserMenuGrant, Long> {

    List<UserMenuGrant> findByTenantIdAndUserId(Long tenantId, Long userId);



    void deleteByTenantIdAndUserId(Long tenantId, Long userId);

}

