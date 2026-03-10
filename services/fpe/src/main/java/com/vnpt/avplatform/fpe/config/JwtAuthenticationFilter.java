package com.vnpt.avplatform.fpe.config;

import com.vnpt.avplatform.shared.config.SecurityProperties;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.ExpiredJwtException;
import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;
import org.springframework.web.filter.OncePerRequestFilter;

import javax.crypto.SecretKey;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.Collections;
import java.util.List;
import java.util.Objects;
import java.util.stream.Collectors;

/**
 * Stateless JWT authentication filter executed once per HTTP request.
 *
 * <p>Extracts the Bearer token from the {@code Authorization} header, validates its
 * signature and expiry against the configured HMAC-SHA256 secret, and populates the
 * Spring Security context with the authenticated principal and granted authorities.
 *
 * <p>Invalid or missing tokens are silently skipped here; downstream
 * {@link SecurityConfig} rejects unauthenticated requests on protected paths.
 */
@Slf4j
@Component
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private static final String AUTHORIZATION_HEADER = "Authorization";
    private static final String BEARER_PREFIX = "Bearer ";
    private static final String ROLES_CLAIM = "roles";

    private final SecretKey signingKey;
    private final SecurityProperties securityProperties;

    public JwtAuthenticationFilter(SecurityProperties securityProperties) {
        this.securityProperties = Objects.requireNonNull(securityProperties,
                "securityProperties must not be null");
        String jwtSecret = securityProperties.validate().jwtSecret();
        this.signingKey = Keys.hmacShaKeyFor(jwtSecret.getBytes(StandardCharsets.UTF_8));
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain filterChain) throws ServletException, IOException {
        String token = extractBearerToken(request);
        if (token != null) {
            try {
                Claims claims = parseAndValidateToken(token);
                populateSecurityContext(claims);
            } catch (ExpiredJwtException e) {
                log.warn("Expired JWT token on URI={}: {}", request.getRequestURI(), e.getMessage());
            } catch (JwtException e) {
                log.warn("Invalid JWT token on URI={}: {}", request.getRequestURI(), e.getMessage());
            }
        }
        filterChain.doFilter(request, response);
    }

    private String extractBearerToken(HttpServletRequest request) {
        String header = request.getHeader(AUTHORIZATION_HEADER);
        if (StringUtils.hasText(header) && header.startsWith(BEARER_PREFIX)) {
            return header.substring(BEARER_PREFIX.length());
        }
        return null;
    }

    private Claims parseAndValidateToken(String token) {
        return Jwts.parser()
                .verifyWith(signingKey)
                .build()
                .parseSignedClaims(token)
                .getPayload();
    }

    @SuppressWarnings("unchecked")
    private void populateSecurityContext(Claims claims) {
        String subject = claims.getSubject();
        List<String> rawRoles = claims.get(ROLES_CLAIM, List.class);
        List<SimpleGrantedAuthority> authorities = (rawRoles == null ? Collections.<String>emptyList() : rawRoles)
                .stream()
                .map(role -> new SimpleGrantedAuthority("ROLE_" + role))
                .collect(Collectors.toList());

        UsernamePasswordAuthenticationToken authentication =
                new UsernamePasswordAuthenticationToken(subject, null, authorities);
        SecurityContextHolder.getContext().setAuthentication(authentication);
        log.debug("Authenticated JWT subject={} roles={}", subject, rawRoles);
    }
}
