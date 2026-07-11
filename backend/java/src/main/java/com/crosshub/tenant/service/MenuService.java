package com.crosshub.tenant.service;

import com.crosshub.auth.entity.AppUser;
import java.util.List;
import java.util.Map;

public interface MenuService {
    public List<Map<String, Object>> menusForUser(AppUser user, String portalRole);
}
