package com.crosshub.temu.web;

import com.crosshub.temu.entity.AppUser;
import com.crosshub.temu.repository.AppUserRepository;
import com.crosshub.temu.security.AuthContext;
import com.crosshub.temu.security.JwtService;
import com.crosshub.temu.service.DataScopeService;
import com.crosshub.temu.service.MenuService;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@RestController
@RequestMapping("/api/auth")
public class AuthController {
    private final AppUserRepository userRepository;
    private final JwtService jwtService;
    private final MenuService menuService;
    private final DataScopeService dataScopeService;
    private final AuthContext authContext;

    public AuthController(
            AppUserRepository userRepository,
            JwtService jwtService,
            MenuService menuService,
            DataScopeService dataScopeService,
            AuthContext authContext
    ) {
        this.userRepository = userRepository;
        this.jwtService = jwtService;
        this.menuService = menuService;
        this.dataScopeService = dataScopeService;
        this.authContext = authContext;
    }

    @PostMapping("/login")
    public Map<String, Object> login(@RequestBody LoginRequest request) {
        String account = request.account() == null ? "" : request.account().trim();
        String password = request.password() == null ? "" : request.password();
        String portalRole = request.portalRole() == null ? "boss" : request.portalRole();

        Optional<AppUser> userOpt = userRepository.findByUsernameIgnoreCase(account);
        if (userOpt.isEmpty() || !userOpt.get().getPassword().equals(password)) {
            throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "账号或密码错误");
        }

        AppUser user = userOpt.get();
        if (user.getTenantId() == null) {
            throw new ResponseStatusException(HttpStatus.FORBIDDEN, "账号未绑定租户");
        }
        if (!user.isActive()) {
            throw new ResponseStatusException(HttpStatus.FORBIDDEN, "账号已停用");
        }
        if ("boss".equals(portalRole) && !user.isAdmin()) {
            throw new ResponseStatusException(HttpStatus.FORBIDDEN, "该账号不是企业管理员");
        }

        boolean bossPortal = "boss".equalsIgnoreCase(portalRole);
        List<String> platforms = dataScopeService.resolvePlatformsForLogin(user.getTenantId(), user.getId(), bossPortal);
        List<String> shopScope = dataScopeService.resolveScopeForLogin(user.getTenantId(), user.getId(), bossPortal);
        String token = jwtService.createToken(user, portalRole, platforms, shopScope);
        List<Map<String, Object>> menus = menuService.menusForUser(user, portalRole);

        Map<String, Object> data = new LinkedHashMap<>();
        data.put("token", token);
        data.put("portal_role", portalRole);
        data.put("role", user.getRole());
        data.put("tenant_id", user.getTenantId());
        data.put("user_id", user.getId());
        data.put("account", user.getUsername());
        data.put("company", user.getEnterprise());
        data.put("nickname", user.getNickname());
        data.put("job_title", user.getJobTitle());
        data.put("platforms", platforms);
        data.put("shop_scope", shopScope);
        data.put("menus", menus);

        return Map.of("code", 0, "data", data);
    }

    @GetMapping("/menus")
    public Map<String, Object> menus() {
        Long userId = authContext.userId();
        Long tenantId = authContext.tenantId();
        String portalRole = authContext.portalRole();
        if (userId == null || tenantId == null || portalRole == null) {
            throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "未登录");
        }

        AppUser user = userRepository.findById(userId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.UNAUTHORIZED, "用户不存在"));
        if (!tenantId.equals(user.getTenantId())) {
            throw new ResponseStatusException(HttpStatus.FORBIDDEN, "租户不匹配");
        }

        return Map.of(
                "code", 0,
                "data", menuService.menusForUser(user, portalRole)
        );
    }

    @GetMapping("/session")
    public Map<String, Object> session() {
        Long userId = authContext.userId();
        if (userId == null) {
            throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "未登录");
        }
        AppUser user = userRepository.findById(userId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.UNAUTHORIZED, "用户不存在"));

        String portalRole = authContext.portalRole();
        Map<String, Object> data = new LinkedHashMap<>();
        data.put("tenant_id", authContext.tenantId());
        data.put("user_id", userId);
        data.put("portal_role", portalRole);
        data.put("role", user.getRole());
        data.put("account", user.getUsername());
        data.put("company", user.getEnterprise());
        data.put("nickname", user.getNickname());
        data.put("platforms", authContext.platforms());
        data.put("shop_scope", authContext.shopScope());
        data.put("menus", menuService.menusForUser(user, portalRole));
        return Map.of("code", 0, "data", data);
    }

    public record LoginRequest(String account, String password, String portalRole) {}
}
