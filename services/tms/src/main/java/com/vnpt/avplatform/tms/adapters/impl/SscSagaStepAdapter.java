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
public class SscSagaStepAdapter implements SagaStepAdapter {

    private final RestTemplate restTemplate;
    private final String sscServiceUrl;

    public SscSagaStepAdapter(
            RestTemplate restTemplate,
            @Value("${saga.services.ssc-url:http://ssc-service:8080}") String sscServiceUrl) {
        this.restTemplate = Objects.requireNonNull(restTemplate, "restTemplate must not be null");
        this.sscServiceUrl = Objects.requireNonNull(sscServiceUrl, "sscServiceUrl must not be null");
    }

    @Override
    public String getStepName() {
        return "SSC";
    }

    @Override
    public String execute(String tenantId, Map<String, Object> context) throws SagaStepException {
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            String url = sscServiceUrl + "/internal/tenants/" + tenantId + "/admin-account";
            var response = restTemplate.exchange(url, HttpMethod.POST, new HttpEntity<>(context, headers), Map.class);
            Object ref = response.getBody() != null ? response.getBody().get("adminUserId") : null;
            String externalRef = ref != null ? ref.toString() : tenantId + "-ssc";
            log.info("SSC saga step executed: tenantId={}, externalRef={}", tenantId, externalRef);
            return externalRef;
        } catch (Exception e) {
            log.error("SSC saga step failed for tenantId={}: {}", tenantId, e.getMessage(), e);
            throw new SagaStepException("SSC step failed: " + e.getMessage());
        }
    }

    @Override
    public void compensate(String tenantId, String externalRef) throws SagaCompensationException {
        try {
            String url = sscServiceUrl + "/internal/tenants/" + tenantId + "/admin-account";
            restTemplate.exchange(url, HttpMethod.DELETE, HttpEntity.EMPTY, Void.class);
            log.info("SSC saga step compensated: tenantId={}", tenantId);
        } catch (Exception e) {
            log.error("SSC compensation failed for tenantId={}: {}", tenantId, e.getMessage(), e);
            throw new SagaCompensationException("SSC compensation failed: " + e.getMessage());
        }
    }
}
