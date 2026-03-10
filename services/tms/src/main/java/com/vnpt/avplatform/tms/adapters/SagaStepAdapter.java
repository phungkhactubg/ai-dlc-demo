package com.vnpt.avplatform.tms.adapters;

import com.vnpt.avplatform.tms.exception.SagaCompensationException;
import com.vnpt.avplatform.tms.exception.SagaStepException;

import java.util.Map;

public interface SagaStepAdapter {
    String getStepName();
    String execute(String tenantId, Map<String, Object> context) throws SagaStepException;
    void compensate(String tenantId, String externalRef) throws SagaCompensationException;
}
