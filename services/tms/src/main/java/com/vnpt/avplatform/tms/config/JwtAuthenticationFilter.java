package com.vnpt.avplatform.tms.config;

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
import java.util.List;
import java.util.Objects;
import java.util.stream.Collectors;

/**
 * JWT authentication filter that extracts and validates a Bearer token from the
 * {@code Authorization} HTTP header on every incoming request.
 *
 * <p>On successful validation the authenticated principal is stored in the
 * {@link SecurityContextHolder}. On failure the filter continues the chain
 * and Spring Security's {@code AuthenticationEntryPoint} rejects the request.</p>
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

        if (token != null && SecurityContextHolder.getContext().getAuthentication() == null) {
            try {
                Claims claims = parseAndValidateClaims(token);
                UsernamePasswordAuthenticationToken authentication = buildAuthentication(claims);
                SecurityContextHolder.getContext().setAuthentication(authentication);
                log.debug("JWT authentication successful for subject: {}", claims.getSubject());
            } catch (ExpiredJwtException e) {
                log.warn("JWT token expired for request [{}]: {}", request.getRequestURI(), e.getMessage());
            } catch (JwtException e) {
                log.warn("Invalid JWT token for request [{}]: {}", request.getRequestURI(), e.getMessage());
            }
        }

        filterChain.doFilter(request, response);
    }

    private String extractBearerToken(HttpServletRequest request) {
        String authHeader = request.getHeader(AUTHORIZATION_HEADER);
        if (StringUtils.hasText(authHeader) && authHeader.startsWith(BEARER_PREFIX)) {
            return authHeader.substring(BEARER_PREFIX.length());
        }
        return null;
    }

    private Claims parseAndValidateClaims(String token) {
        return Jwts.parser()
                .verifyWith(signingKey)
                .build()
                .parseSignedClaims(token)
                .getPayload();
    }

    @SuppressWarnings("unchecked")
    private UsernamePasswordAuthenticationToken buildAuthentication(Claims claims) {
        String subject = claims.getSubject();
        List<String> rawRoles = claims.get(ROLES_CLAIM, List.class);
        List<SimpleGrantedAuthority> authorities = rawRoles == null
                ? List.of()
                : rawRoles.stream()
                    .map(SimpleGrantedAuthority::new)
                    .collect(Collectors.toList());
        return new UsernamePasswordAuthenticationToken(subject, null, authorities);
    }
}
