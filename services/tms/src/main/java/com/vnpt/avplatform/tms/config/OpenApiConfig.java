package com.vnpt.avplatform.tms.config;

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
 * OpenAPI / Swagger UI configuration for the TMS service.
 */
@Configuration
public class OpenApiConfig {

    private static final String JWT_SCHEME = "bearerAuth";

    /**
     * Configures the global OpenAPI descriptor with JWT security and tenant header.
     */
    @Bean
    public OpenAPI tmsOpenApi() {
        return new OpenAPI()
                .info(new Info()
                        .title("TMS Service API")
                        .description("Tenant Management Service — manages tenant lifecycle, onboarding and configuration")
                        .version("1.0.0"))
                .components(new Components()
                        .addSecuritySchemes(JWT_SCHEME, new SecurityScheme()
                                .name(JWT_SCHEME)
                                .type(SecurityScheme.Type.HTTP)
                                .scheme("bearer")
                                .bearerFormat("JWT")
                                .description("JWT Bearer token obtained from the authentication service")))
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
