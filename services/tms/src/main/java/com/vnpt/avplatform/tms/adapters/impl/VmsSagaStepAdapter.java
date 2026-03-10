package com.vnpt.avplatform.tms.adapters.impl;

import com.vnpt.avplatform.tms.adapters.SagaStepAdapter;
import com.vnpt.avplatform.tms.exception.SagaCompensationException;
import com.vnpt.avplatform.tms.exception.SagaStepException;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import java.util.Map;
import java.util.Objects;

@Slf4j
@Component
public class VmsSagaStepAdapter implements SagaStepAdapter {

    private final RestTemplate restTemplate;
    private final String executeEndpoint;
    private final String compensateTemplate;

    public VmsSagaStepAdapter(
            RestTemplate restTemplate,
            @Value("${saga.services.vms-url:http://vms-service:8080}") String vmsServiceUrl) {
        this.restTemplate = Objects.requireNonNull(restTemplate, "restTemplate must not be null");
        validateServiceUrl(vmsServiceUrl, "VMS");
        this.executeEndpoint = vmsServiceUrl + "/internal/fleet-allocation";
        this.compensateTemplate = vmsServiceUrl + "/internal/fleet-allocation/{tenantId}";
    }

    @Override
    public String getStepName() {
        return "VMS";
    }

    @Override
    public String execute(String tenantId, Map<String, Object> context) throws SagaStepException {
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            Map<String, Object> payload = Map.of("tenantId", tenantId, "vehicleQuota", context.getOrDefault("vehicleQuota", 0), "context", context);
            var response = restTemplate.exchange(executeEndpoint, HttpMethod.POST, new HttpEntity<>(payload, headers), Map.class);
            Object ref = response.getBody() != null ? response.getBody().get("allocationId") : null;
            String externalRef = ref != null ? ref.toString() : tenantId + "-vms";
            log.info("VMS saga step executed: tenantId={}, externalRef={}", tenantId, externalRef);
            return externalRef;
        } catch (Exception e) {
            log.error("VMS saga step failed for tenantId={}: {}", tenantId, e.getMessage(), e);
            throw new SagaStepException("VMS step failed: " + e.getMessage());
        }
    }

    @Override
    public void compensate(String tenantId, String externalRef) throws SagaCompensationException {
        try {
            restTemplate.exchange(compensateTemplate, HttpMethod.DELETE, HttpEntity.EMPTY, Void.class, tenantId);
            log.info("VMS saga step compensated: tenantId={}", tenantId);
        } catch (Exception e) {
            log.error("VMS compensation failed for tenantId={}: {}", tenantId, e.getMessage(), e);
            throw new SagaCompensationException("VMS compensation failed: " + e.getMessage());
        }
    }

    private static void validateServiceUrl(String url, String serviceName) {
        if (!url.startsWith("http://") && !url.startsWith("https://")) {
            throw new IllegalStateException(
                serviceName + " service URL must start with http:// or https://, got: " + url);
        }
        try {
            java.net.URI uri = java.net.URI.create(url);
            String host = uri.getHost();
            if (host == null || host.isBlank()) {
                throw new IllegalStateException(serviceName + " service URL has no valid host");
            }
        } catch (IllegalArgumentException e) {
            throw new IllegalStateException(serviceName + " service URL is malformed: " + url, e);
        }
    }
}
