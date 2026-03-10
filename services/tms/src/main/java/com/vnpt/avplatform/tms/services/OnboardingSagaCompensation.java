package com.vnpt.avplatform.tms.services;

public interface OnboardingSagaCompensation {
    void compensate(String sagaId, String tenantId, int lastCompletedStepIndex);
}
