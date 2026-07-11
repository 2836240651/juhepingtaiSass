package com.crosshub.security;

import com.crosshub.agent.entity.IntegrationAgent;
import org.springframework.stereotype.Component;
import org.springframework.web.context.annotation.RequestScope;

@Component
@RequestScope
public class AgentContext {
    private IntegrationAgent agent;

    public IntegrationAgent agent() {
        return agent;
    }

    public void setAgent(IntegrationAgent agent) {
        this.agent = agent;
    }

    public Long tenantId() {
        return agent == null ? null : agent.getTenantId();
    }
}
