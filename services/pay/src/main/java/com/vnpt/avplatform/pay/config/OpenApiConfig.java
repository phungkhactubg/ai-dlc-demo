package com.vnpt.avplatform.pay.config;

import io.swagger.v3.oas.models.Components;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.parameters.HeaderParameter;
import io.swagger.v3.oas.models.security.SecurityRequirement;
import io.swagger.v3.oas.models.security.SecurityScheme;
import org.springdoc.core.customizers.OpenApiCustomizer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * OpenAPI / Swagger UI configuration for the PAY service.
 */
@Configuration
public class OpenApiConfig {

    private static final String JWT_SCHEME = "bearerAuth";

    /**
     * Configures the global OpenAPI descriptor with JWT security and tenant header.
     */
    @Bean
    public OpenAPI payOpenApi() {
        return new OpenAPI()
                .info(new Info()
                        .title("PAY Service API")
                        .description("Payment Service — PCI-DSS compliant, internal-only " +
                                     "(pay-namespace K8s, ADR-003). Accessible only from RHS.")
                        .version("1.0.0"))
                .components(new Components()
                        .addSecuritySchemes(JWT_SCHEME, new SecurityScheme()
                                .name(JWT_SCHEME)
                                .type(SecurityScheme.Type.HTTP)
                                .scheme("bearer")
                                .bearerFormat("JWT")
                                .description("JWT Bearer token with ROLE_INTERNAL_SERVICE or ROLE_PLATFORM_ADMIN")))
                .addSecurityItem(new SecurityRequirement().addList(JWT_SCHEME));
    }

    /**
     * Adds the mandatory {@code X-Tenant-ID} header parameter to every operation.
     */
    @Bean
    public OpenApiCustomizer tenantHeaderCustomizer() {
        return openApi -> openApi.getPaths().values().forEach(pathItem ->
            pathItem.readOperations().forEach(operation ->
                operation.addParametersItem(
                    new HeaderParameter()
                        .name("X-Tenant-ID")
                        .description("Tenant identifier — mandatory on all authenticated endpoints")
                        .required(true)
                        .schema(new io.swagger.v3.oas.models.media.StringSchema()))));
    }
}
