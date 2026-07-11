package com.crosshub.security;

import io.jsonwebtoken.Claims;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

@Component
public class JwtAuthInterceptor implements HandlerInterceptor {
    private final JwtService jwtService;
    private final AuthContext authContext;

    public JwtAuthInterceptor(JwtService jwtService, AuthContext authContext) {
        this.jwtService = jwtService;
        this.authContext = authContext;
    }

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
        if ("OPTIONS".equalsIgnoreCase(request.getMethod())) {
            return true;
        }
        String token = authContext.extractToken(request);
        if (token == null || token.isBlank()) {
            response.setStatus(HttpStatus.UNAUTHORIZED.value());
            response.getWriter().write("{\"code\":401,\"msg\":\"未登录\"}");
            return false;
        }
        try {
            Claims claims = jwtService.parse(token);
            authContext.set(claims);
            return true;
        } catch (Exception ex) {
            response.setStatus(HttpStatus.UNAUTHORIZED.value());
            response.getWriter().write("{\"code\":401,\"msg\":\"登录已过期\"}");
            return false;
        }
    }

    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response, Object handler, Exception ex) {
        authContext.clear();
    }
}
