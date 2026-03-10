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
public class DpeSagaStepAdapter implements SagaStepAdapter {

    private final RestTemplate restTemplate;
    private final String executeEndpoint;
    private final String compensateTemplate;

    public DpeSagaStepAdapter(
            RestTemplate restTemplate,
            @Value("${saga.services.dpe-url:http://dpe-service:8080}") String dpeServiceUrl) {
        this.restTemplate = Objects.requireNonNull(restTemplate, "restTemplate must not be null");
        validateServiceUrl(dpeServiceUrl, "DPE");
        this.executeEndpoint = dpeServiceUrl + "/internal/api-keys";
        this.compensateTemplate = dpeServiceUrl + "/internal/api-keys/{tenantId}";
    }

    @Override
    public String getStepName() {
        return "DPE";
    }

    @Override
    public String execute(String tenantId, Map<String, Object> context) throws SagaStepException {
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            Map<String, Object> payload = Map.of("tenantId", tenantId, "context", context);
            var response = restTemplate.exchange(executeEndpoint, HttpMethod.POST, new HttpEntity<>(payload, headers), Map.class);
            Object ref = response.getBody() != null ? response.getBody().get("apiKeyReference") : null;
            String externalRef = ref != null ? ref.toString() : tenantId + "-dpe";
            log.info("DPE saga step executed: tenantId={}, externalRef={}", tenantId, externalRef);
            return externalRef;
        } catch (Exception e) {
            log.error("DPE saga step failed for tenantId={}: {}", tenantId, e.getMessage(), e);
            throw new SagaStepException("DPE step failed: " + e.getMessage());
        }
    }

    @Override
    public void compensate(String tenantId, String externalRef) throws SagaCompensationException {
        try {
            restTemplate.exchange(compensateTemplate, HttpMethod.DELETE, HttpEntity.EMPTY, Void.class, tenantId);
            log.info("DPE saga step compensated: tenantId={}", tenantId);
        } catch (Exception e) {
            log.error("DPE compensation failed for tenantId={}: {}", tenantId, e.getMessage(), e);
            throw new SagaCompensationException("DPE compensation failed: " + e.getMessage());
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
