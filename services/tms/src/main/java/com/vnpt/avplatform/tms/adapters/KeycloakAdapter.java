package com.vnpt.avplatform.tms.adapters;

public interface KeycloakAdapter {
    String createRiderUser(String tenantId, String email, String provider);
    void assignRiderRole(String keycloakUserId);
    void deleteRiderUser(String keycloakUserId);
}
