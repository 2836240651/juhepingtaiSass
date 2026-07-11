package com.crosshub.security;

import com.crosshub.agent.entity.IntegrationAgent;
import com.crosshub.agent.repository.IntegrationAgentRepository;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.web.servlet.HandlerInterceptor;

@Component
public class AgentAuthInterceptor implements HandlerInterceptor {
    public static final String HEADER = "X-Agent-Token";

    private final IntegrationAgentRepository agentRepository;
    private final AgentContext agentContext;

    public AgentAuthInterceptor(IntegrationAgentRepository agentRepository, AgentContext agentContext) {
        this.agentRepository = agentRepository;
        this.agentContext = agentContext;
    }

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
        String token = request.getHeader(HEADER);
        if (token == null || token.isBlank()) {
            throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "缺少 Agent Token");
        }
        IntegrationAgent agent = agentRepository.findByAgentToken(token.trim())
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.UNAUTHORIZED, "Agent Token 无效"));
        if (!"active".equalsIgnoreCase(agent.getStatus())) {
            throw new ResponseStatusException(HttpStatus.FORBIDDEN, "Agent 节点已停用");
        }
        agentContext.setAgent(agent);
        return true;
    }
}
