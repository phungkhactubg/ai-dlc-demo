package com.vnpt.avplatform.tms.services;

import java.util.Map;

public interface FeatureFlagService {
    boolean isEnabled(String tenantId, String flagKey);
    Map<String, Boolean> getAllFlags(String tenantId);
    Map<String, Boolean> updateFlags(String tenantId, Map<String, Boolean> flags);
}
