package com.vnpt.avplatform.tms.services.impl;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.vnpt.avplatform.shared.TenantContext;
import com.vnpt.avplatform.tms.adapters.KeycloakAdapter;
import com.vnpt.avplatform.tms.exception.AccessDeniedException;
import com.vnpt.avplatform.tms.exception.RiderAlreadyExistsException;
import com.vnpt.avplatform.tms.exception.RiderNotFoundException;
import com.vnpt.avplatform.tms.models.entity.AuthProvider;
import com.vnpt.avplatform.tms.models.entity.Rider;
import com.vnpt.avplatform.tms.models.entity.RiderStatus;
import com.vnpt.avplatform.tms.models.request.RegisterRiderRequest;
import com.vnpt.avplatform.tms.models.request.UpdateRiderRequest;
import com.vnpt.avplatform.tms.models.response.RiderDTO;
import com.vnpt.avplatform.tms.repositories.RiderRepository;
import com.vnpt.avplatform.tms.services.RiderIdentityService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;

import java.time.Instant;
import java.util.Objects;
import java.util.Optional;
import java.util.UUID;

@Slf4j
@Service
public class RiderIdentityServiceImpl implements RiderIdentityService {

    private final RiderRepository riderRepository;
    private final KeycloakAdapter keycloakAdapter;
    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;
    private final String keycloakUrl;
    private final String realm;
    private final String clientId;
    private final String clientSecret;

    public RiderIdentityServiceImpl(
            RiderRepository riderRepository,
            KeycloakAdapter keycloakAdapter,
            RestTemplate restTemplate,
            ObjectMapper objectMapper,
            @Value("${keycloak.admin.url}") String keycloakUrl,
            @Value("${keycloak.realm}") String realm,
            @Value("${keycloak.client-id}") String clientId,
            @Value("${keycloak.client-secret}") String clientSecret) {
        this.riderRepository = Objects.requireNonNull(riderRepository, "riderRepository must not be null");
        this.keycloakAdapter = Objects.requireNonNull(keycloakAdapter, "keycloakAdapter must not be null");
        this.restTemplate = Objects.requireNonNull(restTemplate, "restTemplate must not be null");
        this.objectMapper = Objects.requireNonNull(objectMapper, "objectMapper must not be null");
        this.keycloakUrl = keycloakUrl;
        this.realm = realm;
        this.clientId = clientId;
        this.clientSecret = clientSecret;
    }

    @Override
    public RiderDTO registerRider(String tenantId, RegisterRiderRequest request) {
        if (riderRepository.existsByEmailAndTenantId(request.getEmail(), tenantId)) {
            throw new RiderAlreadyExistsException(
                    "A rider with email '" + request.getEmail() + "' already exists in this tenant");
        }

        Instant now = Instant.now();
        Rider rider = Rider.builder()
                .riderId(UUID.randomUUID().toString())
                .tenantId(tenantId)
                .email(request.getEmail())
                .emailVerified(false)
                .fullName(request.getFullName())
                .authProvider(request.getAuthProvider())
                .phoneNumber(request.getPhoneNumber())
                .phoneVerified(false)
                .status(RiderStatus.PENDING_VERIFICATION)
                .createdAt(now)
                .updatedAt(now)
                .build();

        String keycloakSub = keycloakAdapter.createRiderUser(
                tenantId, request.getEmail(), request.getAuthProvider().name());
        rider.setKeycloakSub(keycloakSub);

        Rider saved = riderRepository.save(rider);
        log.info("Rider registered: riderId={}, tenantId={}", saved.getRiderId(), tenantId);
        return mapToDTO(saved);
    }

    @Override
    public RiderDTO handleOAuthCallback(String tenantId, String provider, String idToken) {
        try {
            String introspectUrl = keycloakUrl + "/realms/" + realm + "/protocol/openid-connect/token/introspect";
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_FORM_URLENCODED);
            headers.setBasicAuth(clientId, clientSecret);

            MultiValueMap<String, String> formData = new LinkedMultiValueMap<>();
            formData.add("token", idToken);

            var response = restTemplate.exchange(
                    introspectUrl, HttpMethod.POST,
                    new HttpEntity<>(formData, headers), String.class);

            JsonNode introspection = objectMapper.readTree(response.getBody());
            if (!introspection.path("active").asBoolean(false)) {
                throw new AccessDeniedException("OAuth token is not active");
            }

            String email = introspection.path("email").asText(null);
            String sub = introspection.path("sub").asText(null);
            if (email == null || sub == null) {
                throw new AccessDeniedException("OAuth token missing required claims: email, sub");
            }

            Optional<Rider> existing = riderRepository.findByKeycloakSub(sub);
            if (existing.isPresent()) {
                log.info("OAuth login - existing rider: riderId={}, tenantId={}", existing.get().getRiderId(), tenantId);
                return mapToDTO(existing.get());
            }

            Instant now = Instant.now();
            Rider newRider = Rider.builder()
                    .riderId(UUID.randomUUID().toString())
                    .tenantId(tenantId)
                    .email(email)
                    .emailVerified(true)
                    .keycloakSub(sub)
                    .authProvider(parseProvider(provider))
                    .status(RiderStatus.ACTIVE)
                    .createdAt(now)
                    .updatedAt(now)
                    .build();

            Rider saved = riderRepository.save(newRider);
            log.info("OAuth rider created: riderId={}, tenantId={}", saved.getRiderId(), tenantId);
            return mapToDTO(saved);

        } catch (AccessDeniedException e) {
            throw e;
        } catch (Exception e) {
            log.error("OAuth callback handling failed: provider={}, tenantId={}: {}", provider, tenantId, e.getMessage(), e);
            throw new RuntimeException("OAuth callback handling failed: " + e.getMessage(), e);
        }
    }

    @Override
    public RiderDTO getRider(String riderId) {
        String contextTenantId = TenantContext.getTenantId();
        Rider rider = riderRepository.findByRiderId(riderId)
                .orElseThrow(() -> new RiderNotFoundException("Rider not found: " + riderId));

        if (contextTenantId != null && !contextTenantId.equals(rider.getTenantId())) {
            throw new AccessDeniedException("Access denied: rider does not belong to your tenant");
        }
        return mapToDTO(rider);
    }

    @Override
    @Transactional
    public RiderDTO updateRider(String riderId, UpdateRiderRequest request) {
        String contextTenantId = TenantContext.getTenantId();
        Rider rider = riderRepository.findByRiderId(riderId)
                .orElseThrow(() -> new RiderNotFoundException("Rider not found: " + riderId));

        if (contextTenantId != null && !contextTenantId.equals(rider.getTenantId())) {
            throw new AccessDeniedException("Access denied: rider does not belong to your tenant");
        }

        if (request.getFullName() != null) {
            rider.setFullName(request.getFullName());
        }
        if (request.getPreferredLanguage() != null) {
            rider.setPreferredLanguage(request.getPreferredLanguage());
        }
        if (request.getProfilePhotoUrl() != null) {
            rider.setProfilePhotoUrl(request.getProfilePhotoUrl());
        }
        rider.setUpdatedAt(Instant.now());

        Rider updated = riderRepository.save(rider);
        log.info("Rider updated: riderId={}", riderId);
        return mapToDTO(updated);
    }

    private AuthProvider parseProvider(String provider) {
        try {
            return AuthProvider.valueOf(provider.toUpperCase());
        } catch (IllegalArgumentException e) {
            log.warn("Unknown OAuth provider '{}', defaulting to EMAIL", provider);
            return AuthProvider.EMAIL;
        }
    }

    private RiderDTO mapToDTO(Rider rider) {
        return RiderDTO.builder()
                .riderId(rider.getRiderId())
                .tenantId(rider.getTenantId())
                .email(rider.getEmail())
                .emailVerified(rider.isEmailVerified())
                .phoneNumber(rider.getPhoneNumber())
                .phoneVerified(rider.isPhoneVerified())
                .fullName(rider.getFullName())
                .preferredLanguage(rider.getPreferredLanguage())
                .authProvider(rider.getAuthProvider())
                .profilePhotoUrl(rider.getProfilePhotoUrl())
                .status(rider.getStatus())
                .createdAt(rider.getCreatedAt())
                .build();
    }
}
