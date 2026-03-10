package com.vnpt.avplatform.mkp.config;

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
 * JWT authentication filter for the MKP service.
 *
 * <p>Extracts and validates the Bearer token from the {@code Authorization} header.
 * On success, populates the Spring Security context with the authenticated principal
 * and its roles. The {@code ROLE_MARKETPLACE_ADMIN} role extracted from JWT claims
 * is used for admin-level operations (BL-009, FR-MKP-010, FR-MKP-011).</p>
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

                log.debug("JWT authenticated: subject={}, tenantId={}, roles={}",
                    subject, tenantId, authorities.size());
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

    private String extractToken(HttpServletRequest request) {
        String authHeader = request.getHeader(HttpHeaders.AUTHORIZATION);
        if (StringUtils.hasText(authHeader) && authHeader.startsWith(BEARER_PREFIX)) {
            return authHeader.substring(BEARER_PREFIX.length());
        }
        return null;
    }

    private Claims parseToken(String token) {
        return Jwts.parser()
            .verifyWith(signingKey)
            .build()
            .parseSignedClaims(token)
            .getPayload();
    }

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
