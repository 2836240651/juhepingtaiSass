package com.crosshub.auth.dto;

public record LoginRequest(String account, String password, String portalRole) {}
