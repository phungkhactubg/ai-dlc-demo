package com.vnpt.avplatform.tms.adapters.impl;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.vnpt.avplatform.tms.adapters.KeycloakAdapter;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.RestTemplate;

import java.util.List;
import java.util.Map;
import java.util.Objects;

@Slf4j
@Component
public class KeycloakAdapterImpl implements KeycloakAdapter {

    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;
    private final String keycloakUrl;
    private final String realm;
    private final String clientId;
    private final String clientSecret;

    public KeycloakAdapterImpl(
            RestTemplate restTemplate,
            ObjectMapper objectMapper,
            @Value("${keycloak.admin.url}") String keycloakUrl,
            @Value("${keycloak.realm}") String realm,
            @Value("${keycloak.client-id}") String clientId,
            @Value("${keycloak.client-secret}") String clientSecret) {
        this.restTemplate = Objects.requireNonNull(restTemplate, "restTemplate must not be null");
        this.objectMapper = Objects.requireNonNull(objectMapper, "objectMapper must not be null");
        this.keycloakUrl = Objects.requireNonNull(keycloakUrl, "keycloakUrl must not be null");
        this.realm = Objects.requireNonNull(realm, "realm must not be null");
        this.clientId = Objects.requireNonNull(clientId, "clientId must not be null");
        this.clientSecret = Objects.requireNonNull(clientSecret, "clientSecret must not be null");
    }

    @Override
    public String createRiderUser(String tenantId, String email, String provider) {
        String adminToken = getAdminToken();
        HttpHeaders headers = buildBearerHeaders(adminToken);
        headers.setContentType(MediaType.APPLICATION_JSON);

        Map<String, Object> userRepresentation = Map.of(
                "username", email,
                "email", email,
                "emailVerified", false,
                "enabled", true,
                "attributes", Map.of(
                        "tenant_id", List.of(tenantId),
                        "auth_provider", List.of(provider)
                )
        );

        String url = keycloakUrl + "/admin/realms/" + realm + "/users";
        try {
            ResponseEntity<Void> response = restTemplate.exchange(
                    url, HttpMethod.POST,
                    new HttpEntity<>(userRepresentation, headers),
                    Void.class);

            String locationHeader = response.getHeaders().getFirst("Location");
            if (locationHeader == null || locationHeader.isBlank()) {
                throw new IllegalStateException("Keycloak did not return Location header after user creation");
            }
            String keycloakUserId = locationHeader.substring(locationHeader.lastIndexOf('/') + 1);
            log.info("Created Keycloak user: keycloakUserId={}, email={}, tenantId={}", keycloakUserId, email, tenantId);
            return keycloakUserId;

        } catch (HttpClientErrorException.Conflict e) {
            log.warn("Keycloak user already exists for email={}, fetching existing user id", email);
            return findExistingUserId(adminToken, email);
        }
    }

    @Override
    public void assignRiderRole(String keycloakUserId) {
        String adminToken = getAdminToken();
        HttpHeaders headers = buildBearerHeaders(adminToken);
        headers.setContentType(MediaType.APPLICATION_JSON);

        String rolesUrl = keycloakUrl + "/admin/realms/" + realm + "/roles/RIDER";
        try {
            ResponseEntity<String> roleResponse = restTemplate.exchange(
                    rolesUrl, HttpMethod.GET,
                    new HttpEntity<>(headers), String.class);

            JsonNode roleNode = objectMapper.readTree(roleResponse.getBody());
            Map<String, Object> role = Map.of(
                    "id", roleNode.get("id").asText(),
                    "name", "RIDER"
            );

            String assignUrl = keycloakUrl + "/admin/realms/" + realm + "/users/" + keycloakUserId + "/role-mappings/realm";
            restTemplate.exchange(
                    assignUrl, HttpMethod.POST,
                    new HttpEntity<>(List.of(role), headers), Void.class);

            log.info("Assigned RIDER role to keycloakUserId={}", keycloakUserId);
        } catch (Exception e) {
            log.error("Failed to assign RIDER role to keycloakUserId={}: {}", keycloakUserId, e.getMessage(), e);
            throw new RuntimeException("Failed to assign RIDER role: " + e.getMessage(), e);
        }
    }

    @Override
    public void deleteRiderUser(String keycloakUserId) {
        String adminToken = getAdminToken();
        HttpHeaders headers = buildBearerHeaders(adminToken);
        String url = keycloakUrl + "/admin/realms/" + realm + "/users/" + keycloakUserId;

        try {
            restTemplate.exchange(url, HttpMethod.DELETE, new HttpEntity<>(headers), Void.class);
            log.info("Deleted Keycloak user: keycloakUserId={}", keycloakUserId);
        } catch (HttpClientErrorException.NotFound e) {
            log.warn("Keycloak user not found for deletion: keycloakUserId={}", keycloakUserId);
        } catch (Exception e) {
            log.error("Failed to delete Keycloak user: keycloakUserId={}", keycloakUserId, e);
            throw new RuntimeException("Failed to delete Keycloak user: " + e.getMessage(), e);
        }
    }

    private String getAdminToken() {
        String tokenUrl = keycloakUrl + "/realms/master/protocol/openid-connect/token";
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_FORM_URLENCODED);

        MultiValueMap<String, String> formData = new LinkedMultiValueMap<>();
        formData.add("grant_type", "client_credentials");
        formData.add("client_id", clientId);
        formData.add("client_secret", clientSecret);

        try {
            ResponseEntity<String> response = restTemplate.exchange(
                    tokenUrl, HttpMethod.POST,
                    new HttpEntity<>(formData, headers), String.class);

            JsonNode tokenNode = objectMapper.readTree(response.getBody());
            return tokenNode.get("access_token").asText();
        } catch (Exception e) {
            log.error("Failed to obtain Keycloak admin token: {}", e.getMessage(), e);
            throw new RuntimeException("Failed to obtain Keycloak admin token: " + e.getMessage(), e);
        }
    }

    private String findExistingUserId(String adminToken, String email) {
        HttpHeaders headers = buildBearerHeaders(adminToken);
        String url = keycloakUrl + "/admin/realms/" + realm + "/users?email=" + email + "&exact=true";
        try {
            ResponseEntity<String> response = restTemplate.exchange(
                    url, HttpMethod.GET, new HttpEntity<>(headers), String.class);
            JsonNode users = objectMapper.readTree(response.getBody());
            if (users.isArray() && users.size() > 0) {
                return users.get(0).get("id").asText();
            }
            throw new RuntimeException("Could not find existing Keycloak user for email: " + email);
        } catch (Exception e) {
            log.error("Failed to find existing Keycloak user for email={}: {}", email, e.getMessage(), e);
            throw new RuntimeException("Failed to find existing Keycloak user: " + e.getMessage(), e);
        }
    }

    private HttpHeaders buildBearerHeaders(String token) {
        HttpHeaders headers = new HttpHeaders();
        headers.setBearerAuth(token);
        return headers;
    }
}
