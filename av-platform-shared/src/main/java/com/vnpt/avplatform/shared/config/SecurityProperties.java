package com.vnpt.avplatform.shared.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.bind.DefaultValue;
import org.springframework.stereotype.Component;

/**
 * Security configuration properties bound from {@code app.security.*} in application.yml.
 *
 * <p>This centralized configuration class provides JWT and security-related properties
 * for all AV Platform services. It should be used instead of direct {@code @Value} annotations
 * for better type safety, validation, and consistency across services.</p>
 *
 * <p>Usage in service-specific configuration:</p>
 * <pre>{@code
 * @EnableConfigurationProperties(SecurityProperties.class)
 * public class JwtAuthenticationFilter {
 *
 *     private final SecurityProperties securityProperties;
 *
 *     public JwtAuthenticationFilter(SecurityProperties securityProperties) {
 *         this.securityProperties = Objects.requireNonNull(securityProperties,
 *             "securityProperties must not be null");
 *     }
 * }
 * }</pre>
 */
@Component
@ConfigurationProperties(prefix = "app.security")
public record SecurityProperties(

        /**
         * JWT signing secret key for HMAC-SHA256 algorithm.
         *
         * <p><strong>SECURITY WARNING:</strong> This MUST be overridden in production
         * with a cryptographically secure random string of at least 256 bits (32 bytes).
         * Never use the default value in production environments.</p>
         *
         * <p>Generate a secure key with:</p>
         * <pre>{@code
         * openssl rand -base64 32
         * }</pre>
         */
        @DefaultValue("change-me-in-production-must-be-at-least-32-characters-long")
        String jwtSecret,

        /**
         * JWT access token expiration time in milliseconds.
         *
         * <p>Default: 15 minutes (900,000 ms)</p>
         */
        @DefaultValue("900000")
        long accessTokenExpirationMs,

        /**
         * JWT refresh token expiration time in milliseconds.
         *
         * <p>Default: 7 days (604,800,000 ms)</p>
         */
        @DefaultValue("604800000")
        long refreshTokenExpirationMs,

        /**
         * Issuer claim value for JWT tokens.
         *
         * <p>This identifies the principal that issued the JWT.
         * Default: "vnpt-av-platform"</p>
         */
        @DefaultValue("vnpt-av-platform")
        String issuer
) {
    /**
     * Validates that the JWT secret meets minimum security requirements.
     *
     * @return this SecurityProperties instance for method chaining
     * @throws IllegalStateException if jwtSecret is less than 32 characters
     */
    public SecurityProperties validate() {
        if (jwtSecret == null || jwtSecret.length() < 32) {
            throw new IllegalStateException(
                "JWT secret must be at least 32 characters long for security. " +
                "Current length: " + (jwtSecret == null ? 0 : jwtSecret.length())
            );
        }
        if (accessTokenExpirationMs <= 0) {
            throw new IllegalStateException(
                "Access token expiration must be positive. Current value: " + accessTokenExpirationMs
            );
        }
        if (refreshTokenExpirationMs <= 0) {
            throw new IllegalStateException(
                "Refresh token expiration must be positive. Current value: " + refreshTokenExpirationMs
            );
        }
        return this;
    }
}
