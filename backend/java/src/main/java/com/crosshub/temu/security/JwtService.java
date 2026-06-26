package com.crosshub.temu.security;

import com.crosshub.temu.entity.AppUser;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class JwtService {
    private final SecretKey key;
    private final long ttlSeconds = 86400;

    public JwtService(@Value("${crosshub.jwt-secret}") String secret) {
        this.key = Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8));
    }

    public String createToken(AppUser user, String portalRole, List<String> platforms, List<String> shopScope) {
        Instant now = Instant.now();
        Map<String, Object> claims = new HashMap<>();
        claims.put("uid", user.getId());
        claims.put("tid", user.getTenantId());
        claims.put("role", user.getRole());
        claims.put("portal_role", portalRole);
        claims.put("username", user.getUsername());
        claims.put("platforms", platforms == null ? List.of() : platforms);
        claims.put("shop_scope", shopScope == null ? List.of() : shopScope);

        return Jwts.builder()
                .claims(claims)
                .subject(user.getUsername())
                .issuedAt(Date.from(now))
                .expiration(Date.from(now.plusSeconds(ttlSeconds)))
                .signWith(key)
                .compact();
    }

    public Claims parse(String token) {
        return Jwts.parser()
                .verifyWith(key)
                .build()
                .parseSignedClaims(token)
                .getPayload();
    }
}
