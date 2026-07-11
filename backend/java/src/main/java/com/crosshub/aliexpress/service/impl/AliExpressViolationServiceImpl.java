package com.crosshub.aliexpress.service.impl;

import com.crosshub.aliexpress.dto.AliExpressViolationPatchRequest;
import com.crosshub.aliexpress.entity.AliExpressViolation;
import com.crosshub.aliexpress.repository.AliExpressViolationRepository;
import com.crosshub.aliexpress.service.AliExpressViolationService;
import com.crosshub.common.AppErrorCode;
import com.crosshub.tenant.service.DataScopeService;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.util.LinkedHashMap;
import java.util.Map;

@Service
public class AliExpressViolationServiceImpl implements AliExpressViolationService {
    private final AliExpressViolationRepository violationRepository;
    private final DataScopeService dataScopeService;

    public AliExpressViolationServiceImpl(AliExpressViolationRepository violationRepository, DataScopeService dataScopeService) {
        this.violationRepository = violationRepository;
        this.dataScopeService = dataScopeService;
    }

    @Override
    @Transactional
    public Map<String, Object> patch(String id, AliExpressViolationPatchRequest request) {
        Long tenantId = dataScopeService.requireTenantId();
        AliExpressViolation row = violationRepository.findByIdAndTenantId(id, tenantId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, AppErrorCode.NOT_FOUND.getUserMessage()));
        row.setAppealStatus(request == null ? null : request.appealStatus());
        row.setAppealResult(request == null ? null : request.appealResult());
        if (request != null && request.appealResult() != null && !request.appealResult().isBlank()) {
            row.setConfirmed(1);
        }
        violationRepository.save(row);
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("id", row.getId());
        out.put("appealStatus", row.getAppealStatus());
        out.put("appealResult", row.getAppealResult());
        out.put("confirmed", row.getConfirmed());
        return out;
    }
}

