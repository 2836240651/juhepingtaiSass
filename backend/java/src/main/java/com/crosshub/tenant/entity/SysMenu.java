package com.crosshub.tenant.entity;

import jakarta.persistence.*;

@Entity
@Table(name = "sys_menu")
public class SysMenu {
    @Id
    @Column(length = 64)
    private String code;

    @Column(name = "parent_code", length = 64)
    private String parentCode;

    @Column(nullable = false, length = 16)
    private String portal;

    @Column(length = 32)
    private String platform;

    @Column(nullable = false, length = 128)
    private String path;

    @Column(nullable = false, length = 64)
    private String label;

    @Column(name = "menu_type", nullable = false, length = 16)
    private String menuType;

    @Column(name = "sort_order", nullable = false)
    private Integer sortOrder = 0;

    public String getCode() { return code; }
    public void setCode(String code) { this.code = code; }
    public String getParentCode() { return parentCode; }
    public void setParentCode(String parentCode) { this.parentCode = parentCode; }
    public String getPortal() { return portal; }
    public void setPortal(String portal) { this.portal = portal; }
    public String getPlatform() { return platform; }
    public void setPlatform(String platform) { this.platform = platform; }
    public String getPath() { return path; }
    public void setPath(String path) { this.path = path; }
    public String getLabel() { return label; }
    public void setLabel(String label) { this.label = label; }
    public String getMenuType() { return menuType; }
    public void setMenuType(String menuType) { this.menuType = menuType; }
    public Integer getSortOrder() { return sortOrder; }
    public void setSortOrder(Integer sortOrder) { this.sortOrder = sortOrder; }
}
