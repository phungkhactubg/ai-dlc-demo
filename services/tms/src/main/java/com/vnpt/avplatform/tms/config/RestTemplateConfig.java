package com.vnpt.avplatform.tms.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestTemplate;

/**
 * HTTP client configuration providing a shared {@link RestTemplate} bean
 * used by all external service adapters (Keycloak, Twilio, Saga step adapters).
 */
@Configuration
public class RestTemplateConfig {

    @Bean
    public RestTemplate restTemplate() {
        return new RestTemplate();
    }
}
