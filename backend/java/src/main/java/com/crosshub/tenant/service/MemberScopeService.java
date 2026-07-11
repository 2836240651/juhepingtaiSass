package com.crosshub.tenant.service;

import java.util.List;
import java.util.Set;

public interface MemberScopeService {
    List<String> platformsForMember(Long tenantId, Long userId);

    List<String> shopIdsForMember(Long tenantId, Long userId);

    List<String> menuCodesForMember(Long tenantId, Long userId);

    void deleteAllScopes(Long tenantId, Long userId);

    void replaceScopes(
            Long tenantId,
            Long userId,
            List<String> platforms,
            List<String> shopIds,
            List<String> menuCodes,
            boolean updateMenuCodes
    );

    void replaceMenuGrants(Long tenantId, Long userId, List<String> menuCodes);

    Set<String> assignableEmployeeMenuCodes();
}
