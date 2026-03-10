package com.vnpt.avplatform.bms.config;

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
import org.springframework.lang.NonNull;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.web.authentication.WebAuthenticationDetailsSource;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;
import org.springframework.web.filter.OncePerRequestFilter;

import javax.crypto.SecretKey;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Objects;
import java.util.stream.Collectors;

/**
 * JWT authentication filter that validates Bearer tokens on every incoming request.
 *
 * <p>This filter:</p>
 * <ol>
 *   <li>Extracts the Bearer token from the {@code Authorization} header.</li>
 *   <li>Validates the token signature and expiry using JJWT.</li>
 *   <li>Populates {@link SecurityContextHolder} with the authenticated principal
 *       so downstream components can access user identity and roles.</li>
 * </ol>
 *
 * <p>Requests with missing or invalid tokens pass through unauthenticated;
 * access control is enforced by {@link SecurityConfig}.</p>
 */
@Slf4j
@Component
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private static final String BEARER_PREFIX = "Bearer ";
    private static final String AUTHORIZATION_HEADER = "Authorization";
    private static final String CLAIM_ROLES = "roles";
    private static final String CLAIM_TENANT_ID = "tenantId";

    private final SecretKey signingKey;
    private final SecurityProperties securityProperties;

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

        String token = extractBearerToken(request);

        if (StringUtils.hasText(token) && SecurityContextHolder.getContext().getAuthentication() == null) {
            authenticateWithToken(token, request);
        }

        filterChain.doFilter(request, response);
    }

    private void authenticateWithToken(String token, HttpServletRequest request) {
        try {
            Claims claims = parseToken(token);
            String subject = claims.getSubject();

            if (!StringUtils.hasText(subject)) {
                log.warn("JWT token has no subject; skipping authentication");
                return;
            }

            List<SimpleGrantedAuthority> authorities = extractAuthorities(claims);

            UsernamePasswordAuthenticationToken authentication =
                    new UsernamePasswordAuthenticationToken(subject, null, authorities);
            authentication.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));

            SecurityContextHolder.getContext().setAuthentication(authentication);
            log.debug("Authenticated principal '{}' with {} role(s) via JWT", subject, authorities.size());

        } catch (ExpiredJwtException e) {
            log.warn("JWT token expired: {}", e.getMessage());
        } catch (UnsupportedJwtException | MalformedJwtException e) {
            log.warn("Malformed or unsupported JWT token: {}", e.getMessage());
        } catch (SignatureException e) {
            log.warn("JWT signature validation failed: {}", e.getMessage());
        } catch (IllegalArgumentException e) {
            log.warn("JWT token compact is invalid: {}", e.getMessage());
        }
    }

    private Claims parseToken(String token) {
        return Jwts.parser()
                .verifyWith(signingKey)
                .build()
                .parseSignedClaims(token)
                .getPayload();
    }

    @SuppressWarnings("unchecked")
    private List<SimpleGrantedAuthority> extractAuthorities(Claims claims) {
        Object rolesClaim = claims.get(CLAIM_ROLES);
        if (rolesClaim instanceof List<?> roleList) {
            return roleList.stream()
                    .filter(String.class::isInstance)
                    .map(role -> new SimpleGrantedAuthority((String) role))
                    .collect(Collectors.toList());
        }
        return List.of();
    }

    private String extractBearerToken(HttpServletRequest request) {
        String header = request.getHeader(AUTHORIZATION_HEADER);
        if (StringUtils.hasText(header) && header.startsWith(BEARER_PREFIX)) {
            return header.substring(BEARER_PREFIX.length()).trim();
        }
        return null;
    }
}
