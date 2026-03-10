package com.vnpt.avplatform.tms.services;

import java.util.Map;

public interface OnboardingSagaService {
    void startSaga(String tenantId, String planId, Map<String, Object> context);
}
