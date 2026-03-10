package com.vnpt.avplatform.bms.config;

import io.swagger.v3.oas.models.Components;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Contact;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.info.License;
import io.swagger.v3.oas.models.parameters.Parameter;
import io.swagger.v3.oas.models.security.SecurityRequirement;
import io.swagger.v3.oas.models.security.SecurityScheme;
import org.springdoc.core.customizers.OperationCustomizer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * OpenAPI / Swagger configuration for the BMS service.
 *
 * <p>Adds:</p>
 * <ul>
 *   <li>Bearer JWT authentication scheme applied globally.</li>
 *   <li>{@code X-Tenant-ID} as a required global header on all operations.</li>
 *   <li>API metadata (title, version, contact, license).</li>
 * </ul>
 */
@Configuration
public class OpenApiConfig {

    private static final String BEARER_SCHEME = "bearerAuth";
    private static final String TENANT_HEADER = "X-Tenant-ID";

    /**
     * Builds the {@link OpenAPI} bean with global security and tenant header.
     *
     * @return configured {@link OpenAPI} instance
     */
    @Bean
    public OpenAPI bmsOpenApi() {
        return new OpenAPI()
                .info(new Info()
                        .title("BMS Service API")
                        .description("Billing & Subscription Management Service — VNPT AV Platform")
                        .version("1.0.0")
                        .contact(new Contact()
                                .name("VNPT AV Platform Team")
                                .email("av-platform@vnpt.vn"))
                        .license(new License()
                                .name("Proprietary")
                                .url("https://vnpt.vn")))
                .addSecurityItem(new SecurityRequirement().addList(BEARER_SCHEME))
                .components(new Components()
                        .addSecuritySchemes(BEARER_SCHEME, new SecurityScheme()
                                .name(BEARER_SCHEME)
                                .type(SecurityScheme.Type.HTTP)
                                .scheme("bearer")
                                .bearerFormat("JWT")
                                .description("Provide a valid JWT access token")));
    }

    /**
     * Operation customizer that injects the {@code X-Tenant-ID} required header
     * into every API operation in the generated Swagger UI.
     *
     * @return {@link OperationCustomizer} bean
     */
    @Bean
    public OperationCustomizer tenantHeaderCustomizer() {
        return (operation, handlerMethod) -> {
            Parameter tenantHeader = new Parameter()
                    .in("header")
                    .name(TENANT_HEADER)
                    .description("Tenant identifier — required for all authenticated API calls")
                    .required(true)
                    .schema(new io.swagger.v3.oas.models.media.StringSchema()
                            .example("tenant-001"));
            operation.addParametersItem(tenantHeader);
            return operation;
        };
    }
}
