package com.crosshub.temu.web;



import com.crosshub.temu.service.TenantMemberService;

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

    public Map<String, Object> updateScopes(@PathVariable("id") Long id, @RequestBody ScopeRequest request) {

        return Map.of(

                "code", 0,

                "data", memberService.updateScopes(id, new TenantMemberService.ScopePayload(

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



    private TenantMemberService.MemberPayload toMemberPayload(MemberRequest request) {

        return new TenantMemberService.MemberPayload(

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



    public record MemberRequest(

            String name,

            String account,

            String password,

            String phone,

            String role,

            List<String> platforms,

            @com.fasterxml.jackson.annotation.JsonProperty("shop_ids") List<String> shopIds,

            @com.fasterxml.jackson.annotation.JsonProperty("menu_codes") List<String> menuCodes,

            Boolean status

    ) {}



    public record ScopeRequest(

            List<String> platforms,

            @com.fasterxml.jackson.annotation.JsonProperty("shop_ids") List<String> shopIds,

            @com.fasterxml.jackson.annotation.JsonProperty("menu_codes") List<String> menuCodes

    ) {}



    public record StatusRequest(boolean status) {}

}

