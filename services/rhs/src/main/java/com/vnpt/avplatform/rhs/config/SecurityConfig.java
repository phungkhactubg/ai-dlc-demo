package com.vnpt.avplatform.rhs.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.vnpt.avplatform.shared.model.ApiResponse;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;

import java.io.IOException;
import java.util.UUID;

/**
 * Spring Security configuration for the RHS service.
 *
 * <p>Enforces stateless JWT-based authentication. All requests to actuator and
 * OpenAPI documentation paths are permitted without authentication; all other
 * paths require a valid Bearer token processed by {@link JwtAuthenticationFilter}.
 */
@Configuration
@EnableWebSecurity
@RequiredArgsConstructor
public class SecurityConfig {

    private final JwtAuthenticationFilter jwtAuthenticationFilter;
    private final ObjectMapper objectMapper;

    /** Paths that do not require authentication. */
    private static final String[] PUBLIC_PATHS = {
            "/actuator/**",
            "/api/v1/api-docs/**",
            "/api/v1/swagger-ui/**",
            "/api/v1/swagger-ui.html"
    };

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
                .csrf(AbstractHttpConfigurer::disable)
                .sessionManagement(session ->
                        session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
                .authorizeHttpRequests(auth -> auth
                        .requestMatchers(PUBLIC_PATHS).permitAll()
                        .anyRequest().authenticated())
                .exceptionHandling(ex -> ex
                        .authenticationEntryPoint(this::handleAuthenticationException)
                        .accessDeniedHandler(this::handleAccessDeniedException))
                .addFilterBefore(jwtAuthenticationFilter, UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }

    private void handleAuthenticationException(HttpServletRequest request,
                                               HttpServletResponse response,
                                               AuthenticationException ex) throws IOException {
        writeErrorResponse(response, HttpStatus.UNAUTHORIZED, "UNAUTHORIZED", ex.getMessage());
    }

    private void handleAccessDeniedException(HttpServletRequest request,
                                             HttpServletResponse response,
                                             AccessDeniedException ex) throws IOException {
        writeErrorResponse(response, HttpStatus.FORBIDDEN, "FORBIDDEN", ex.getMessage());
    }

    private void writeErrorResponse(HttpServletResponse response,
                                    HttpStatus status,
                                    String code,
                                    String message) throws IOException {
        String traceId = UUID.randomUUID().toString();
        ApiResponse<Void> body = ApiResponse.error(code, message, status.value(), traceId);
        response.setStatus(status.value());
        response.setContentType(MediaType.APPLICATION_JSON_VALUE);
        response.setCharacterEncoding("UTF-8");
        objectMapper.writeValue(response.getWriter(), body);
    }
}
