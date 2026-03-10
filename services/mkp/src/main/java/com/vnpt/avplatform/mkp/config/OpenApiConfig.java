package com.vnpt.avplatform.mkp.config;

import io.swagger.v3.oas.models.Components;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Contact;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.info.License;
import io.swagger.v3.oas.models.media.StringSchema;
import io.swagger.v3.oas.models.parameters.Parameter;
import io.swagger.v3.oas.models.security.SecurityRequirement;
import io.swagger.v3.oas.models.security.SecurityScheme;
import org.springdoc.core.customizers.OperationCustomizer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * OpenAPI 3.0 documentation configuration for the MKP (Marketplace) service.
 *
 * <p>Registers global Bearer authentication scheme and a mandatory
 * {@code X-Tenant-ID} header parameter across all operations.</p>
 */
@Configuration
public class OpenApiConfig {

    private static final String SECURITY_SCHEME_NAME = "bearerAuth";
    private static final String TENANT_HEADER = "X-Tenant-ID";

    /**
     * Configures the OpenAPI bean with Marketplace service metadata, Bearer auth scheme,
     * and global security requirement.
     *
     * @return the configured {@link OpenAPI} instance
     */
    @Bean
    public OpenAPI mkpOpenApi() {
        return new OpenAPI()
            .info(new Info()
                .title("MKP Marketplace API")
                .description("Marketplace Service — VNPT AV Platform. "
                    + "Manages plugin/partner listings, security audits (BL-009), and catalog caching.")
                .version("1.0.0")
                .contact(new Contact()
                    .name("VNPT AV Platform Team")
                    .email("avplatform@vnpt.vn"))
                .license(new License()
                    .name("Proprietary")
                    .url("https://vnpt.vn")))
            .addSecurityItem(new SecurityRequirement().addList(SECURITY_SCHEME_NAME))
            .components(new Components()
                .addSecuritySchemes(SECURITY_SCHEME_NAME,
                    new SecurityScheme()
                        .name(SECURITY_SCHEME_NAME)
                        .type(SecurityScheme.Type.HTTP)
                        .scheme("bearer")
                        .bearerFormat("JWT")
                        .description("JWT Bearer token. Must include ROLE_MARKETPLACE_ADMIN claim for admin operations.")));
    }

    /**
     * Adds the mandatory {@code X-Tenant-ID} header parameter to every API operation.
     *
     * @return the operation customizer that injects the tenant header
     */
    @Bean
    public OperationCustomizer tenantHeaderCustomizer() {
        return (operation, handlerMethod) -> {
            operation.addParametersItem(
                new Parameter()
                    .in("header")
                    .name(TENANT_HEADER)
                    .description("Tenant identifier for multi-tenant data isolation (BL-001)")
                    .required(true)
                    .schema(new StringSchema()));
            return operation;
        };
    }
}
