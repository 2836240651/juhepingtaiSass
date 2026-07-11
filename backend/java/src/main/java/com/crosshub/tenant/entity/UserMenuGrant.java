package com.crosshub.tenant.entity;



import jakarta.persistence.*;



@Entity

@Table(

        name = "user_menu_grant",

        uniqueConstraints = @UniqueConstraint(columnNames = {"tenant_id", "user_id", "menu_code"})

)

public class UserMenuGrant {

    @Id

    @GeneratedValue(strategy = GenerationType.IDENTITY)

    private Long id;



    @Column(name = "tenant_id", nullable = false)

    private Long tenantId;



    @Column(name = "user_id", nullable = false)

    private Long userId;



    @Column(name = "menu_code", nullable = false, length = 128)

    private String menuCode;



    public Long getId() { return id; }

    public Long getTenantId() { return tenantId; }

    public void setTenantId(Long tenantId) { this.tenantId = tenantId; }

    public Long getUserId() { return userId; }

    public void setUserId(Long userId) { this.userId = userId; }

    public String getMenuCode() { return menuCode; }

    public void setMenuCode(String menuCode) { this.menuCode = menuCode; }

}

