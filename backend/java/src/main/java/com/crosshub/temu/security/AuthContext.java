package com.crosshub.temu.security;

import io.jsonwebtoken.Claims;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.HttpHeaders;
import org.springframework.stereotype.Component;

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

    public Long userId() {
        Claims claims = CURRENT.get();
        if (claims == null) return null;
        Object uid = claims.get("uid");
        if (uid instanceof Integer i) return i.longValue();
        if (uid instanceof Long l) return l;
        return Long.parseLong(String.valueOf(uid));
    }

    public String extractToken(HttpServletRequest request) {
        String header = request.getHeader(HttpHeaders.AUTHORIZATION);
        if (header != null && header.startsWith("Bearer ")) {
            return header.substring(7);
        }
        return null;
    }
}
