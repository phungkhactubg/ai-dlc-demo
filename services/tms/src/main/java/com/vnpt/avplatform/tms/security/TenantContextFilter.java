package com.vnpt.avplatform.tms.security;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.vnpt.avplatform.shared.TenantContext;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
import java.util.Map;
import java.util.Set;

@Slf4j
@Component
@Order(1)
public class TenantContextFilter extends OncePerRequestFilter {

    private static final String X_TENANT_ID = "X-Tenant-ID";
    private static final String AUTHORIZATION_HEADER = "Authorization";
    private static final String BEARER_PREFIX = "Bearer ";

    private static final Set<String> PUBLIC_PATH_PREFIXES = Set.of(
            "/actuator/health",
            "/actuator/info",
            "/api/v1/api-docs",
            "/api/v1/swagger-ui",
            "/api/v1/riders/register"
    );

    private static final String CONFIRM_OTP_PATTERN = "/api/v1/riders/";
    private static final String CONFIRM_OTP_SUFFIX = "/confirm-otp";

    private final ObjectMapper objectMapper;

    public TenantContextFilter(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain filterChain) throws ServletException, IOException {
        try {
            String path = request.getRequestURI();
            if (!requiresTenant(path)) {
                filterChain.doFilter(request, response);
                return;
            }

            String tenantId = extractTenantId(request);
            if (tenantId != null && !tenantId.isBlank()) {
                TenantContext.setTenantId(tenantId);
                log.debug("TenantContext set: tenantId={}, path={}", tenantId, path);
            }
            filterChain.doFilter(request, response);
        } finally {
            TenantContext.clear();
        }
    }

    private boolean requiresTenant(String path) {
        for (String prefix : PUBLIC_PATH_PREFIXES) {
            if (path.startsWith(prefix)) {
                return false;
            }
        }
        // /api/v1/riders/{riderId}/confirm-otp is public
        if (path.startsWith(CONFIRM_OTP_PATTERN) && path.endsWith(CONFIRM_OTP_SUFFIX)) {
            return false;
        }
        return true;
    }

    private String extractTenantId(HttpServletRequest request) {
        // Primary: extract tenant_id claim from JWT payload
        String tenantId = extractFromJwt(request);
        if (tenantId != null && !tenantId.isBlank()) {
            return tenantId;
        }
        // Fallback: X-Tenant-ID header
        String header = request.getHeader(X_TENANT_ID);
        if (StringUtils.hasText(header)) {
            return header.trim();
        }
        return null;
    }

    @SuppressWarnings("unchecked")
    private String extractFromJwt(HttpServletRequest request) {
        String authHeader = request.getHeader(AUTHORIZATION_HEADER);
        if (!StringUtils.hasText(authHeader) || !authHeader.startsWith(BEARER_PREFIX)) {
            return null;
        }
        try {
            String token = authHeader.substring(BEARER_PREFIX.length());
            String[] parts = token.split("\\.");
            if (parts.length < 2) {
                return null;
            }
            // Decode the payload (part index 1) - signature already validated by JwtAuthenticationFilter
            byte[] payloadBytes = Base64.getUrlDecoder().decode(padBase64(parts[1]));
            String payloadJson = new String(payloadBytes, StandardCharsets.UTF_8);
            Map<String, Object> claims = objectMapper.readValue(payloadJson, Map.class);
            Object tenantId = claims.get("tenant_id");
            if (tenantId instanceof String s) {
                return s;
            }
            return null;
        } catch (Exception e) {
            log.debug("Could not extract tenant_id from JWT: {}", e.getMessage());
            return null;
        }
    }

    private String padBase64(String base64) {
        int padding = base64.length() % 4;
        if (padding == 2) {
            return base64 + "==";
        } else if (padding == 3) {
            return base64 + "=";
        }
        return base64;
    }
}
