package com.crosshub.agent.repository;

import com.crosshub.agent.entity.AgentTask;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface AgentTaskRepository extends JpaRepository<AgentTask, String> {
    List<AgentTask> findByTenantIdAndStatusOrderByCreatedAtAsc(Long tenantId, String status);

    Optional<AgentTask> findByIdAndTenantId(String id, Long tenantId);
}
