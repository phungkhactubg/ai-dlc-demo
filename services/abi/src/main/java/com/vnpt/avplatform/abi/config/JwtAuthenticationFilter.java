package com.vnpt.avplatform.abi.config;

import com.vnpt.avplatform.shared.config.SecurityProperties;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.ExpiredJwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.MalformedJwtException;
import io.jsonwebtoken.UnsupportedJwtException;
import io.jsonwebtoken.security.Keys;
import io.jsonwebtoken.security.SignatureException;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.extern.slf4j.Slf4j;
import org.slf4j.MDC;
import org.springframework.http.HttpHeaders;
import org.springframework.lang.NonNull;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;
import org.springframework.web.filter.OncePerRequestFilter;

import javax.crypto.SecretKey;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.Collection;
import java.util.Collections;
import java.util.List;
import java.util.Objects;

/**
 * JWT authentication filter for the ABI service.
 *
 * <p>Extracts and validates the Bearer token from the {@code Authorization} header.
 * On success, populates the Spring Security {@link org.springframework.security.core.context.SecurityContext}
 * with a {@link UsernamePasswordAuthenticationToken} so downstream components can
 * access the authenticated principal and its roles.</p>
 *
 * <p>The {@code traceId} claim from the JWT is placed into the SLF4J MDC so that all
 * log messages within a request include a consistent correlation ID.</p>
 */
@Slf4j
@Component
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private static final String BEARER_PREFIX = "Bearer ";
    private static final String CLAIM_ROLES = "roles";
    private static final String CLAIM_TENANT_ID = "tenantId";
    private static final String MDC_TRACE_ID = "traceId";
    private static final String MDC_TENANT_ID = "tenantId";

    private final SecretKey signingKey;
    private final SecurityProperties securityProperties;

    /**
     * Constructs the filter with the JWT signing secret.
     *
     * @param securityProperties centralized security configuration properties
     */
    public JwtAuthenticationFilter(SecurityProperties securityProperties) {
        this.securityProperties = Objects.requireNonNull(securityProperties,
                "securityProperties must not be null");
        String jwtSecret = securityProperties.validate().jwtSecret();
        this.signingKey = Keys.hmacShaKeyFor(jwtSecret.getBytes(StandardCharsets.UTF_8));
    }

    @Override
    protected void doFilterInternal(
            @NonNull HttpServletRequest request,
            @NonNull HttpServletResponse response,
            @NonNull FilterChain filterChain) throws ServletException, IOException {

        String token = extractToken(request);
        try {
            if (token != null) {
                Claims claims = parseToken(token);
                String subject = claims.getSubject();
                String traceId = claims.getId();
                String tenantId = claims.get(CLAIM_TENANT_ID, String.class);

                if (StringUtils.hasText(traceId)) {
                    MDC.put(MDC_TRACE_ID, traceId);
                }
                if (StringUtils.hasText(tenantId)) {
                    MDC.put(MDC_TENANT_ID, tenantId);
                }

                Collection<GrantedAuthority> authorities = extractAuthorities(claims);
                UsernamePasswordAuthenticationToken authentication =
                    new UsernamePasswordAuthenticationToken(subject, null, authorities);
                SecurityContextHolder.getContext().setAuthentication(authentication);

                log.debug("JWT authenticated: subject={}, tenantId={}", subject, tenantId);
            }
        } catch (ExpiredJwtException ex) {
            log.warn("JWT token is expired: {}", ex.getMessage());
        } catch (UnsupportedJwtException ex) {
            log.warn("JWT token is unsupported: {}", ex.getMessage());
        } catch (MalformedJwtException ex) {
            log.warn("JWT token is malformed: {}", ex.getMessage());
        } catch (SignatureException ex) {
            log.warn("JWT signature validation failed: {}", ex.getMessage());
        } catch (IllegalArgumentException ex) {
            log.warn("JWT claims string is empty: {}", ex.getMessage());
        } finally {
            filterChain.doFilter(request, response);
            MDC.remove(MDC_TRACE_ID);
            MDC.remove(MDC_TENANT_ID);
        }
    }

    /**
     * Extracts the Bearer token from the Authorization header.
     *
     * @param request the incoming HTTP request
     * @return the raw JWT string, or {@code null} if no valid Bearer header is present
     */
    private String extractToken(HttpServletRequest request) {
        String authHeader = request.getHeader(HttpHeaders.AUTHORIZATION);
        if (StringUtils.hasText(authHeader) && authHeader.startsWith(BEARER_PREFIX)) {
            return authHeader.substring(BEARER_PREFIX.length());
        }
        return null;
    }

    /**
     * Parses and validates the JWT, returning the claims payload.
     *
     * @param token the raw JWT string
     * @return the parsed {@link Claims}
     */
    private Claims parseToken(String token) {
        return Jwts.parser()
            .verifyWith(signingKey)
            .build()
            .parseSignedClaims(token)
            .getPayload();
    }

    /**
     * Extracts role-based granted authorities from the {@code roles} JWT claim.
     *
     * @param claims the JWT claims payload
     * @return collection of granted authorities; empty if no roles claim is present
     */
    @SuppressWarnings("unchecked")
    private Collection<GrantedAuthority> extractAuthorities(Claims claims) {
        Object rolesObj = claims.get(CLAIM_ROLES);
        if (!(rolesObj instanceof List)) {
            return Collections.emptyList();
        }
        List<String> roles = (List<String>) rolesObj;
        return roles.stream()
            .filter(StringUtils::hasText)
            .map(SimpleGrantedAuthority::new)
            .map(GrantedAuthority.class::cast)
            .toList();
    }
}
