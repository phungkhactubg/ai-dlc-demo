package com.vnpt.avplatform.rhs.config;

import io.swagger.v3.oas.models.Components;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Contact;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.media.StringSchema;
import io.swagger.v3.oas.models.parameters.Parameter;
import io.swagger.v3.oas.models.security.SecurityRequirement;
import io.swagger.v3.oas.models.security.SecurityScheme;
import org.springdoc.core.customizers.OpenApiCustomizer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * OpenAPI / Swagger UI configuration for the RHS service.
 *
 * <p>Registers Bearer JWT as the global security scheme and injects the mandatory
 * {@code X-Tenant-ID} header into every operation via an {@link OpenApiCustomizer}.
 */
@Configuration
public class OpenApiConfig {

    private static final String BEARER_AUTH = "bearerAuth";
    private static final String TENANT_HEADER = "X-Tenant-ID";

    @Bean
    public OpenAPI openAPI() {
        return new OpenAPI()
                .info(new Info()
                        .title("RHS Service API")
                        .description("Ride Hailing Service — manages trip lifecycle, driver matching, "
                                + "and real-time vehicle tracking for the VNPT AV Platform.")
                        .version("1.0.0")
                        .contact(new Contact()
                                .name("VNPT AV Platform Team")
                                .email("avplatform@vnpt.vn")))
                .addSecurityItem(new SecurityRequirement().addList(BEARER_AUTH))
                .components(new Components()
                        .addSecuritySchemes(BEARER_AUTH, new SecurityScheme()
                                .name(BEARER_AUTH)
                                .type(SecurityScheme.Type.HTTP)
                                .scheme("bearer")
                                .bearerFormat("JWT")
                                .description("JWT Bearer token — obtain from the Auth service.")));
    }

    /**
     * Injects the {@code X-Tenant-ID} header as a required parameter on every
     * API operation, enforcing multi-tenant isolation at the documentation level.
     */
    @Bean
    public OpenApiCustomizer tenantHeaderCustomizer() {
        return openApi -> openApi.getPaths().values().forEach(pathItem ->
                pathItem.readOperations().forEach(operation ->
                        operation.addParametersItem(new Parameter()
                                .in("header")
                                .name(TENANT_HEADER)
                                .required(true)
                                .schema(new StringSchema())
                                .description("Tenant identifier for multi-tenant data isolation")
                                .example("tenant-001"))));
    }
}
