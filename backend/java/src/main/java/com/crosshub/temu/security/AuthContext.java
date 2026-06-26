package com.crosshub.temu.security;

import io.jsonwebtoken.Claims;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.HttpHeaders;
import org.springframework.stereotype.Component;

import java.util.Collections;
import java.util.List;
import java.util.Objects;

@Component
public class AuthContext {
    private static final ThreadLocal<Claims> CURRENT = new ThreadLocal<>();

    public void set(Claims claims) {
        CURRENT.set(claims);
    }

    public void clear() {
        CURRENT.remove();
    }

    public Claims get() {
        return CURRENT.get();
    }

    public boolean isAdmin() {
        Claims claims = CURRENT.get();
        return claims != null && "admin".equalsIgnoreCase(String.valueOf(claims.get("role")));
    }

    public boolean isBossPortal() {
        Claims claims = CURRENT.get();
        return claims != null && "boss".equalsIgnoreCase(String.valueOf(claims.get("portal_role")));
    }

    public Long tenantId() {
        Claims claims = CURRENT.get();
        if (claims == null) return null;
        return asLong(claims.get("tid"));
    }

    public Long userId() {
        Claims claims = CURRENT.get();
        if (claims == null) return null;
        return asLong(claims.get("uid"));
    }

    public String portalRole() {
        Claims claims = CURRENT.get();
        if (claims == null) return null;
        Object value = claims.get("portal_role");
        return value == null ? null : String.valueOf(value);
    }

    @SuppressWarnings("unchecked")
    public List<String> platforms() {
        Claims claims = CURRENT.get();
        if (claims == null) return List.of();
        Object raw = claims.get("platforms");
        if (raw instanceof List<?> list) {
            return list.stream().map(String::valueOf).toList();
        }
        return List.of();
    }

    @SuppressWarnings("unchecked")
    public List<String> shopScope() {
        Claims claims = CURRENT.get();
        if (claims == null) return List.of();
        Object raw = claims.get("shop_scope");
        if (raw instanceof List<?> list) {
            return list.stream().map(String::valueOf).toList();
        }
        return List.of();
    }

    public String extractToken(HttpServletRequest request) {
        String header = request.getHeader(HttpHeaders.AUTHORIZATION);
        if (header != null && header.startsWith("Bearer ")) {
            return header.substring(7);
        }
        return null;
    }

    private Long asLong(Object value) {
        if (value == null) return null;
        if (value instanceof Integer i) return i.longValue();
        if (value instanceof Long l) return l;
        return Long.parseLong(String.valueOf(value));
    }
}
