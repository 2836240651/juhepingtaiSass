package com.crosshub.temu.web;

import com.crosshub.temu.entity.AppUser;
import com.crosshub.temu.repository.AppUserRepository;
import com.crosshub.temu.security.JwtService;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Optional;

@RestController
@RequestMapping("/api/auth")
public class AuthController {
    private final AppUserRepository userRepository;
    private final JwtService jwtService;

    public AuthController(AppUserRepository userRepository, JwtService jwtService) {
        this.userRepository = userRepository;
        this.jwtService = jwtService;
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
        if ("boss".equals(portalRole) && !user.isAdmin()) {
            throw new ResponseStatusException(HttpStatus.FORBIDDEN, "该账号不是企业管理员");
        }
        if ("employee".equals(portalRole) && user.isAdmin()) {
            // 允许 admin 以员工身份浏览（演示）
        }

        String token = jwtService.createToken(user, portalRole);
        Map<String, Object> data = new LinkedHashMap<>();
        data.put("token", token);
        data.put("portal_role", portalRole);
        data.put("role", user.getRole());
        data.put("user_id", user.getId());
        data.put("account", user.getUsername());
        data.put("company", user.getEnterprise());
        data.put("nickname", user.getNickname());

        return Map.of("code", 0, "data", data);
    }

    public record LoginRequest(String account, String password, String portalRole) {}
}
