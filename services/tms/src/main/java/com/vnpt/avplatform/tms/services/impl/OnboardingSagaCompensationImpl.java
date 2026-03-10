package com.vnpt.avplatform.tms.services.impl;

import com.vnpt.avplatform.tms.adapters.SagaStepAdapter;
import com.vnpt.avplatform.tms.exception.SagaCompensationException;
import com.vnpt.avplatform.tms.models.entity.OnboardingSaga;
import com.vnpt.avplatform.tms.models.entity.SagaStatus;
import com.vnpt.avplatform.tms.models.entity.SagaStep;
import com.vnpt.avplatform.tms.models.entity.TenantStatus;
import com.vnpt.avplatform.tms.repositories.OnboardingSagaRepository;
import com.vnpt.avplatform.tms.repositories.TenantRepository;
import com.vnpt.avplatform.tms.services.OnboardingSagaCompensation;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.function.Function;
import java.util.stream.Collectors;

@Slf4j
@Service
public class OnboardingSagaCompensationImpl implements OnboardingSagaCompensation {

    private final OnboardingSagaRepository sagaRepository;
    private final TenantRepository tenantRepository;
    private final Map<String, SagaStepAdapter> adaptersByName;

    public OnboardingSagaCompensationImpl(
            OnboardingSagaRepository sagaRepository,
            TenantRepository tenantRepository,
            List<SagaStepAdapter> sagaStepAdapters) {
        this.sagaRepository = Objects.requireNonNull(sagaRepository, "sagaRepository must not be null");
        this.tenantRepository = Objects.requireNonNull(tenantRepository, "tenantRepository must not be null");
        this.adaptersByName = sagaStepAdapters.stream()
                .collect(Collectors.toMap(SagaStepAdapter::getStepName, Function.identity()));
    }

    @Override
    public void compensate(String sagaId, String tenantId, int lastCompletedStepIndex) {
        log.info("Starting compensation: sagaId={}, tenantId={}, lastCompletedStepIndex={}", sagaId, tenantId, lastCompletedStepIndex);

        OnboardingSaga saga = sagaRepository.findBySagaId(sagaId).orElse(null);
        if (saga == null) {
            log.warn("Saga not found for compensation: sagaId={}", sagaId);
            return;
        }

        // Compensate in reverse order: VMS, DPE, BMS, SSC
        List<String> reverseOrder = List.of("VMS", "DPE", "BMS", "SSC");
        List<SagaStep> steps = saga.getSteps();

        for (String stepName : reverseOrder) {
            int stepIndex = findStepIndex(steps, stepName);
            if (stepIndex < 0 || stepIndex > lastCompletedStepIndex) {
                continue;
            }

            SagaStep step = steps.get(stepIndex);
            if (!"COMPLETED".equals(step.getStatus())) {
                continue;
            }

            SagaStepAdapter adapter = adaptersByName.get(stepName);
            if (adapter == null) {
                log.warn("No adapter found for step: {}", stepName);
                continue;
            }

            try {
                adapter.compensate(tenantId, step.getExternalRef());
                sagaRepository.updateStepStatus(sagaId, stepIndex, "COMPENSATED", step.getExternalRef());
                String logEntry = String.format("Compensated step %s at %s", stepName, Instant.now());
                sagaRepository.appendCompensationLog(sagaId, logEntry);
                log.info("Step compensated: sagaId={}, step={}", sagaId, stepName);
            } catch (SagaCompensationException e) {
                log.error("Compensation failed for step={}, sagaId={}: {}", stepName, sagaId, e.getMessage(), e);
                String errorLog = String.format("COMPENSATION_FAILED: step=%s, error=%s", stepName, e.getMessage());
                try {
                    sagaRepository.appendCompensationLog(sagaId, errorLog);
                } catch (Exception logEx) {
                    log.warn("Could not append compensation error log: {}", logEx.getMessage());
                }
            } catch (Exception e) {
                log.error("Unexpected error during compensation for step={}, sagaId={}: {}", stepName, sagaId, e.getMessage(), e);
            }
        }

        try {
            tenantRepository.findByTenantId(tenantId).ifPresent(tenant -> {
                tenantRepository.updateStatus(tenantId, TenantStatus.TERMINATED);
                log.info("Tenant marked as TERMINATED after saga compensation: tenantId={}", tenantId);
            });
        } catch (Exception e) {
            log.error("Failed to update tenant status to TERMINATED after compensation: tenantId={}, error={}", tenantId, e.getMessage(), e);
        }

        try {
            sagaRepository.updateStatus(sagaId, SagaStatus.COMPENSATED);
        } catch (Exception e) {
            log.error("Failed to mark saga as COMPENSATED: sagaId={}", sagaId, e);
        }

        log.info("Compensation complete: sagaId={}, tenantId={}", sagaId, tenantId);
    }

    private int findStepIndex(List<SagaStep> steps, String stepName) {
        for (int i = 0; i < steps.size(); i++) {
            if (stepName.equals(steps.get(i).getStepName())) {
                return i;
            }
        }
        return -1;
    }
}
