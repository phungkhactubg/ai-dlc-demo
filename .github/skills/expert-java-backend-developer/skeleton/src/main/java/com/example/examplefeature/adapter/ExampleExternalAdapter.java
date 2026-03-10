package com.example.examplefeature.adapter;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import java.time.Duration;

/**
 * ExampleExternalAdapter wraps an external service integration.
 *
 * Architectural Notes:
 * - Uses @Component to mark as Spring bean
 * - Uses constructor injection with final fields
 * - Wraps external service calls (REST, SOAP, etc.)
 * - Handles external service errors and translates to domain exceptions
 * - Logs all external calls for observability
 * - Implements circuit breaker pattern for resilience (can add Hystrix/Resilience4j)
 *
 * Best Practices:
 * - Never expose external service exceptions directly to clients
 * - Always translate to domain-specific exceptions
 * - Log all requests and responses (sanitized)
 * - Implement timeout and retry logic
 * - Use connection pooling for HTTP clients
 */
@Component
@RequiredArgsConstructor
@Slf4j
public class ExampleExternalAdapter {

    private final RestTemplate restTemplate;

    @Value("${external.service.url}")
    private String serviceUrl;

    @Value("${external.service.timeout:5000}")
    private int timeoutMs;

    /**
     * Example method that calls an external service.
     *
     * @param request The request payload
     * @return The response from the external service
     * @throws ExternalServiceException if the call fails
     */
    public String callExternalService(String request) {
        log.debug("Calling external service: url={}, timeout={}ms", serviceUrl, timeoutMs);

        try {
            // Simulate external service call
            String response = restTemplate.getForObject(
                serviceUrl + "/endpoint",
                String.class
            );

            log.debug("External service call successful: responseLength={}",
                response != null ? response.length() : 0);

            return response;

        } catch (Exception e) {
            log.error("External service call failed: url={}, error={}",
                serviceUrl, e.getMessage(), e);

            throw new ExternalServiceException(
                "Failed to call external service: " + e.getMessage(), e
            );
        }
    }

    /**
     * Example method with circuit breaker pattern.
     * This would typically use Resilience4j or Hystrix.
     */
    public String callWithCircuitBreaker(String request) {
        // Circuit breaker logic would go here
        // For now, just call the service directly
        return callExternalService(request);
    }

    /**
     * Example method with retry logic.
     * This would typically use Spring Retry.
     */
    public String callWithRetry(String request, int maxRetries) {
        Exception lastException = null;

        for (int attempt = 0; attempt <= maxRetries; attempt++) {
            try {
                return callExternalService(request);
            } catch (Exception e) {
                lastException = e;
                if (attempt < maxRetries) {
                    log.warn("External service call failed, retrying: attempt={}/{}",
                        attempt + 1, maxRetries);

                    try {
                        Thread.sleep(1000L * (attempt + 1));  // Exponential backoff
                    } catch (InterruptedException ie) {
                        Thread.currentThread().interrupt();
                        throw new ExternalServiceException("Retry interrupted", ie);
                    }
                }
            }
        }

        throw new ExternalServiceException(
            "External service call failed after " + maxRetries + " retries",
            lastException
        );
    }

    /**
     * Health check for the external service.
     * Useful for health endpoints and readiness probes.
     */
    public boolean isHealthy() {
        try {
            String response = restTemplate.getForObject(
                serviceUrl + "/health",
                String.class
            );
            return "OK".equals(response);
        } catch (Exception e) {
            log.warn("External service health check failed: {}", e.getMessage());
            return false;
        }
    }
}

/**
 * Custom exception for external service failures.
 */
class ExternalServiceException extends RuntimeException {

    public ExternalServiceException(String message) {
        super(message);
    }

    public ExternalServiceException(String message, Throwable cause) {
        super(message, cause);
    }
}
