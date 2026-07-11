package com.crosshub.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "crosshub.crawler")
public class CrawlerProperties {
    private String pythonExecutable = "py";
    private String scriptDir = "../backend/python";
    private int timeoutSeconds = 300;
    private boolean allowSeed = false;

    public String getPythonExecutable() { return pythonExecutable; }
    public void setPythonExecutable(String pythonExecutable) { this.pythonExecutable = pythonExecutable; }
    public String getScriptDir() { return scriptDir; }
    public void setScriptDir(String scriptDir) { this.scriptDir = scriptDir; }
    public int getTimeoutSeconds() { return timeoutSeconds; }
    public void setTimeoutSeconds(int timeoutSeconds) { this.timeoutSeconds = timeoutSeconds; }
    public boolean isAllowSeed() { return allowSeed; }
    public void setAllowSeed(boolean allowSeed) { this.allowSeed = allowSeed; }
}
