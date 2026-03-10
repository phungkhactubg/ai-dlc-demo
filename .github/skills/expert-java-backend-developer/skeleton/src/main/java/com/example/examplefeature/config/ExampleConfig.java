package com.example.examplefeature.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.data.jpa.repository.config.EnableJpaAuditing;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.transaction.annotation.EnableTransactionManagement;

/**
 * Example configuration class for the feature module.
 *
 * Architectural Notes:
 * - Uses @Configuration to mark as Spring configuration class
 * - Enables JPA auditing for automatic timestamp management
 * - Enables transaction management
 * - Enables async processing support
 * - Packages to scan are specified explicitly for clarity
 *
 * Common annotations to use in config classes:
 * - @Bean: Define a Spring bean
 * - @ConditionalOnProperty: Enable based on configuration
 * - @Profile: Enable for specific profiles (dev, prod, etc.)
 * - @Import: Import other configuration classes
 * - @ComponentScan: Specify packages to scan for components
 */
@Configuration
@EnableJpaAuditing
@EnableJpaRepositories(basePackages = "com.example.examplefeature.repository")
@EnableTransactionManagement
@EnableAsync
public class ExampleConfig {

    // Additional beans can be defined here as needed

    /*
     * Example bean definitions (commented out for reference):

    @Bean
    public ExampleExternalService exampleExternalService(
            @Value("${external.service.url}") String serviceUrl,
            @Value("${external.service.timeout:5000}") int timeout) {
        return new ExampleExternalService(serviceUrl, timeout);
    }

    @Bean
    @ConditionalOnProperty(name = "feature.cache.enabled", havingValue = "true")
    public CacheManager exampleCacheManager() {
        return new CaffeineCacheManager("examples", "exampleStatistics");
    }

    @Bean
    @Profile("development")
    public DevDataInitializer devDataInitializer(ExampleRepository repository) {
        return new DevDataInitializer(repository);
    }

    */
}

/**
 * Example external service adapter configuration.
 *
 * This demonstrates how to configure external service integrations.
 */
@Configuration
class ExternalServiceConfig {

    /*
    @Bean
    public RestTemplate restTemplate() {
        return new RestTemplateBuilder()
            .setConnectTimeout(Duration.ofSeconds(5))
            .setReadTimeout(Duration.ofSeconds(10))
            .build();
    }

    @Bean
    public WebClient webClient() {
        return WebClient.builder()
            .clientConnector(new ReactorClientConnector(
                HttpClient.create()
                    .option(ChannelOption.CONNECT_TIMEOUT_MILLIS, 5000)
                    .responseTimeout(Duration.ofSeconds(10))
            ))
            .build();
    }
    */
}
