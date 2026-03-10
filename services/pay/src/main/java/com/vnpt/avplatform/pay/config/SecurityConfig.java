package com.vnpt.avplatform.pay.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.vnpt.avplatform.shared.model.ApiResponse;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.web.AuthenticationEntryPoint;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.access.AccessDeniedHandler;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;

import java.io.IOException;
import java.util.UUID;

/**
 * Spring Security configuration for the PAY service.
 *
 * <p><strong>ADR-003 / PCI-DSS</strong>: The PAY service runs in a dedicated
 * {@code pay-namespace} Kubernetes namespace and is accessible only via
 * service-to-service calls from RHS. No rider-facing endpoints are exposed.
 * All requests must carry a valid JWT issued to an internal service principal.</p>
 *
 * @see PaySecurityConfig for PAY-specific role enforcement
 */
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    private static final Logger log = LoggerFactory.getLogger(SecurityConfig.class);

    private static final String[] PUBLIC_PATHS = {
            "/actuator/health",
            "/actuator/info",
            "/api/v1/api-docs/**",
            "/api/v1/swagger-ui/**",
            "/api/v1/swagger-ui.html"
    };

    private final JwtAuthenticationFilter jwtAuthenticationFilter;
    private final ObjectMapper objectMapper;

    public SecurityConfig(JwtAuthenticationFilter jwtAuthenticationFilter,
                          ObjectMapper objectMapper) {
        this.jwtAuthenticationFilter = jwtAuthenticationFilter;
        this.objectMapper = objectMapper;
    }

    /**
     * Configures the base security filter chain for the PAY service.
     * Role-level authorization is further restricted by {@link PaySecurityConfig}.
     *
     * @param http the {@link HttpSecurity} builder
     * @return the configured {@link SecurityFilterChain}
     * @throws Exception if the configuration fails
     */
    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
            .csrf(AbstractHttpConfigurer::disable)
            .sessionManagement(session ->
                session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .authorizeHttpRequests(auth -> auth
                .requestMatchers(PUBLIC_PATHS).permitAll()
                .anyRequest().hasAnyRole("INTERNAL_SERVICE", "PLATFORM_ADMIN"))
            .addFilterBefore(jwtAuthenticationFilter, UsernamePasswordAuthenticationFilter.class)
            .exceptionHandling(ex -> ex
                .authenticationEntryPoint(unauthorizedEntryPoint())
                .accessDeniedHandler(forbiddenHandler()));

        return http.build();
    }

    /**
     * Returns a 401 JSON response when authentication is missing or invalid.
     */
    @Bean
    public AuthenticationEntryPoint unauthorizedEntryPoint() {
        return (HttpServletRequest request, HttpServletResponse response,
                AuthenticationException authException) -> {
            log.warn("PAY: unauthorized access attempt on [{}]: {}",
                    request.getRequestURI(), authException.getMessage());
            writeJsonError(response, HttpStatus.UNAUTHORIZED, "UNAUTHORIZED",
                    "Authentication is required — PAY service accepts only internal service calls");
        };
    }

    /**
     * Returns a 403 JSON response when the principal lacks the required internal service role.
     */
    @Bean
    public AccessDeniedHandler forbiddenHandler() {
        return (request, response, accessDeniedException) -> {
            log.warn("PAY: forbidden access attempt on [{}] by principal [{}]",
                    request.getRequestURI(),
                    request.getUserPrincipal() != null ? request.getUserPrincipal().getName() : "unknown");
            writeJsonError(response, HttpStatus.FORBIDDEN, "FORBIDDEN",
                    "Access denied — PAY endpoints require ROLE_INTERNAL_SERVICE or ROLE_PLATFORM_ADMIN");
        };
    }

    private void writeJsonError(HttpServletResponse response, HttpStatus status,
                                String errorCode, String message) throws IOException {
        response.setStatus(status.value());
        response.setContentType(MediaType.APPLICATION_JSON_VALUE);
        ApiResponse<Void> body = ApiResponse.error(errorCode, message, status.value(),
                UUID.randomUUID().toString());
        objectMapper.writeValue(response.getWriter(), body);
    }
}
