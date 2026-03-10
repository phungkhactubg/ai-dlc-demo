package com.vnpt.avplatform.ncs.config;

import com.vnpt.avplatform.shared.config.SecurityProperties;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;

import java.util.Objects;

/**
 * Spring Security 6 configuration for the NCS service.
 *
 * <p>Security policy:</p>
 * <ul>
 *   <li>Stateless — no HTTP sessions; authentication is JWT-based.</li>
 *   <li>Actuator, OpenAPI docs, and Swagger UI are publicly accessible.</li>
 *   <li>All {@code /api/**} endpoints require a valid JWT Bearer token.</li>
 *   <li>CSRF is disabled (REST API; clients are not browser sessions).</li>
 * </ul>
 */
@Configuration
@EnableWebSecurity
@EnableMethodSecurity
@EnableConfigurationProperties(SecurityProperties.class)
public class SecurityConfig {

    private static final String[] PUBLIC_PATHS = {
            "/actuator/**",
            "/api/v1/api-docs/**",
            "/api/v1/swagger-ui/**",
            "/api/v1/swagger-ui.html",
            "/v3/api-docs/**",
            "/swagger-ui/**",
            "/swagger-ui.html"
    };

    private final JwtAuthenticationFilter jwtAuthenticationFilter;

    public SecurityConfig(JwtAuthenticationFilter jwtAuthenticationFilter) {
        this.jwtAuthenticationFilter = Objects.requireNonNull(jwtAuthenticationFilter,
                "jwtAuthenticationFilter must not be null");
    }

    /**
     * Configures the HTTP security filter chain.
     *
     * @param http the {@link HttpSecurity} builder
     * @return the configured {@link SecurityFilterChain}
     * @throws Exception if configuration fails
     */
    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        return http
                .csrf(AbstractHttpConfigurer::disable)
                .sessionManagement(session ->
                        session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
                .authorizeHttpRequests(auth -> auth
                        .requestMatchers(PUBLIC_PATHS).permitAll()
                        .requestMatchers(HttpMethod.OPTIONS, "/**").permitAll()
                        .anyRequest().authenticated())
                .addFilterBefore(jwtAuthenticationFilter, UsernamePasswordAuthenticationFilter.class)
                .build();
    }
}
