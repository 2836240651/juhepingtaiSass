package com.crosshub.temu.entity;

import jakarta.persistence.*;

@Entity
@Table(name = "app_user")
public class AppUser {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String username;
    private String password;
    private String nickname;
    private String enterprise;
    private String role;

    public Long getId() { return id; }
    public String getUsername() { return username; }
    public String getPassword() { return password; }
    public String getNickname() { return nickname; }
    public String getEnterprise() { return enterprise; }
    public String getRole() { return role; }
    public boolean isAdmin() { return "admin".equalsIgnoreCase(role); }
}
