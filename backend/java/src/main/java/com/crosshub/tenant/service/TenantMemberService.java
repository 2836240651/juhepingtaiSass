package com.crosshub.tenant.service;

import com.crosshub.tenant.dto.MemberPayload;
import com.crosshub.tenant.dto.ScopePayload;

import java.util.List;
import java.util.Map;

public interface TenantMemberService {
    List<Map<String, Object>> listMembers();

    List<Map<String, Object>> assignableMenus();

    Map<String, Object> createMember(MemberPayload payload);

    Map<String, Object> updateMember(Long memberId, MemberPayload payload);

    Map<String, Object> updateScopes(Long memberId, ScopePayload payload);

    void deleteMember(Long memberId);

    Map<String, Object> updateStatus(Long memberId, boolean active);
}
