package com.vnpt.avplatform.tms.repositories;

import com.vnpt.avplatform.tms.models.entity.OnboardingSaga;
import com.vnpt.avplatform.tms.models.entity.SagaStatus;

import java.util.Optional;

public interface OnboardingSagaRepository {
    OnboardingSaga save(OnboardingSaga saga);
    Optional<OnboardingSaga> findBySagaId(String sagaId);
    Optional<OnboardingSaga> findByTenantId(String tenantId);
    OnboardingSaga updateStatus(String sagaId, SagaStatus status);
    OnboardingSaga updateStepStatus(String sagaId, int stepIndex, String stepStatus, String externalRef);
    OnboardingSaga appendCompensationLog(String sagaId, String logEntry);
    OnboardingSaga markCompleted(String sagaId);
    OnboardingSaga markFailed(String sagaId, String reason);
}
