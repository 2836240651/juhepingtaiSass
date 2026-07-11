package com.crosshub.tenant.service;

import java.util.Map;

public interface TenantRegistrationService {
    public Map<String, Object> registerCompany(String companyName, String account, String password);
}
