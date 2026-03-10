package com.vnpt.avplatform.shared.config;

import com.vnpt.avplatform.shared.interceptor.TenantInterceptor;
import org.springframework.boot.autoconfigure.AutoConfiguration;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

/**
 * Spring Boot auto-configuration for the {@code av-platform-shared} library.
 *
 * <p>This class is loaded automatically by Spring Boot's auto-configuration mechanism
 * via the entry in
 * {@code META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports}.
 * Importing services do not need to reference this class explicitly — it activates as
 * soon as the shared JAR is on the classpath.</p>
 *
 * <p>Responsibilities:</p>
 * <ul>
 *   <li>Registers {@link TenantInterceptor} as an MVC interceptor applied to all
 *   {@code /api/**} request paths, ensuring multi-tenancy enforcement on every
 *   authenticated API call.</li>
 * </ul>
 */
@AutoConfiguration
@Configuration
@EnableConfigurationProperties(SecurityProperties.class)
public class SharedAutoConfiguration implements WebMvcConfigurer {

    private final TenantInterceptor tenantInterceptor;

    /**
     * Constructs the auto-configuration with the required {@link TenantInterceptor}.
     * Spring will inject the bean created by component scanning.
     *
     * @param tenantInterceptor the tenant interceptor bean; must not be {@code null}
     */
    public SharedAutoConfiguration(TenantInterceptor tenantInterceptor) {
        if (tenantInterceptor == null) {
            throw new IllegalArgumentException("tenantInterceptor must not be null");
        }
        this.tenantInterceptor = tenantInterceptor;
    }

    /**
     * Registers {@link TenantInterceptor} for all {@code /api/**} path patterns.
     *
     * <p>Public paths such as {@code /actuator/**}, {@code /auth/**}, and
     * {@code /swagger-ui/**} are intentionally excluded so that health-checks,
     * authentication endpoints, and API documentation remain accessible without
     * a tenant header.</p>
     *
     * @param registry the MVC interceptor registry
     */
    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(tenantInterceptor)
                .addPathPatterns("/api/**");
    }
}
