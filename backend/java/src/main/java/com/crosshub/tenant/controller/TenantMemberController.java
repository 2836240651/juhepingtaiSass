package com.crosshub.tenant.controller;



import com.crosshub.tenant.service.TenantMemberService;

import com.crosshub.common.StatusRequest;
import com.crosshub.tenant.dto.MemberPayload;
import com.crosshub.tenant.dto.MemberRequest;
import com.crosshub.tenant.dto.MemberScopeRequest;
import com.crosshub.tenant.dto.ScopePayload;
import org.springframework.web.bind.annotation.*;



import java.util.List;

import java.util.Map;



@RestController

@RequestMapping("/api/tenant")

public class TenantMemberController {

    private final TenantMemberService memberService;



    public TenantMemberController(TenantMemberService memberService) {

        this.memberService = memberService;

    }



    @GetMapping("/members")

    public Map<String, Object> listMembers() {

        return Map.of("code", 0, "data", memberService.listMembers());

    }



    @GetMapping("/assignable-menus")

    public Map<String, Object> assignableMenus() {

        return Map.of("code", 0, "data", memberService.assignableMenus());

    }



    @PostMapping("/members")

    public Map<String, Object> createMember(@RequestBody MemberRequest request) {

        return Map.of(

                "code", 0,

                "data", memberService.createMember(toMemberPayload(request))

        );

    }



    @PutMapping("/members/{id}")

    public Map<String, Object> updateMember(@PathVariable("id") Long id, @RequestBody MemberRequest request) {

        return Map.of(

                "code", 0,

                "data", memberService.updateMember(id, toMemberPayload(request))

        );

    }



    @PutMapping("/members/{id}/scopes")

    public Map<String, Object> updateScopes(@PathVariable("id") Long id, @RequestBody MemberScopeRequest request) {

        return Map.of(

                "code", 0,

                "data", memberService.updateScopes(id, new ScopePayload(

                        request.platforms(),

                        request.shopIds(),

                        request.menuCodes()

                ))

        );

    }



    @PatchMapping("/members/{id}/status")

    public Map<String, Object> updateStatus(@PathVariable("id") Long id, @RequestBody StatusRequest request) {

        return Map.of(

                "code", 0,

                "data", memberService.updateStatus(id, request.status())

        );

    }



    @DeleteMapping("/members/{id}")

    public Map<String, Object> deleteMember(@PathVariable("id") Long id) {

        memberService.deleteMember(id);

        return Map.of("code", 0, "data", true);

    }



    private MemberPayload toMemberPayload(MemberRequest request) {

        return new MemberPayload(

                request.name(),

                request.account(),

                request.password(),

                request.phone(),

                request.role(),

                request.platforms(),

                request.shopIds(),

                request.menuCodes(),

                request.status()
        );
    }
}