package com.vnpt.avplatform.tms.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.vnpt.avplatform.shared.model.ApiResponse;
import com.vnpt.avplatform.tms.security.TenantContextFilter;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
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

@Configuration
@EnableWebSecurity
@EnableMethodSecurity
public class SecurityConfig {

    private static final Logger log = LoggerFactory.getLogger(SecurityConfig.class);

    private static final String[] PUBLIC_PATHS = {
            "/actuator/health",
            "/actuator/info",
            "/api/v1/api-docs/**",
            "/api/v1/swagger-ui/**",
            "/api/v1/swagger-ui.html",
            "/api/v1/riders/register",
            "/api/v1/riders/*/confirm-otp"
    };

    private final JwtAuthenticationFilter jwtAuthenticationFilter;
    private final TenantContextFilter tenantContextFilter;
    private final ObjectMapper objectMapper;

    public SecurityConfig(
            JwtAuthenticationFilter jwtAuthenticationFilter,
            TenantContextFilter tenantContextFilter,
            ObjectMapper objectMapper) {
        this.jwtAuthenticationFilter = jwtAuthenticationFilter;
        this.tenantContextFilter = tenantContextFilter;
        this.objectMapper = objectMapper;
    }

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
            .csrf(AbstractHttpConfigurer::disable)
            .sessionManagement(session ->
                session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .authorizeHttpRequests(auth -> auth
                .requestMatchers(PUBLIC_PATHS).permitAll()
                .anyRequest().authenticated())
            .addFilterBefore(jwtAuthenticationFilter, UsernamePasswordAuthenticationFilter.class)
            .addFilterAfter(tenantContextFilter, JwtAuthenticationFilter.class)
            .exceptionHandling(ex -> ex
                .authenticationEntryPoint(unauthorizedEntryPoint())
                .accessDeniedHandler(forbiddenHandler()));

        return http.build();
    }

    @Bean
    public AuthenticationEntryPoint unauthorizedEntryPoint() {
        return (HttpServletRequest request, HttpServletResponse response, AuthenticationException authException) -> {
            log.warn("Unauthorized access attempt on [{}]: {}", request.getRequestURI(), authException.getMessage());
            writeJsonError(response, HttpStatus.UNAUTHORIZED, "UNAUTHORIZED",
                    "Authentication is required to access this resource");
        };
    }

    @Bean
    public AccessDeniedHandler forbiddenHandler() {
        return (request, response, accessDeniedException) -> {
            log.warn("Forbidden access attempt on [{}] by principal [{}]",
                    request.getRequestURI(),
                    request.getUserPrincipal() != null ? request.getUserPrincipal().getName() : "unknown");
            writeJsonError(response, HttpStatus.FORBIDDEN, "FORBIDDEN",
                    "You do not have permission to access this resource");
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
