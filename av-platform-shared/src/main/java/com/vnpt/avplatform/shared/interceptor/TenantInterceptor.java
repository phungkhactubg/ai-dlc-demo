package com.vnpt.avplatform.shared.interceptor;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.vnpt.avplatform.shared.TenantContext;
import com.vnpt.avplatform.shared.model.ApiResponse;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

import java.io.IOException;
import java.util.UUID;

/**
 * Spring MVC interceptor that enforces tenant context propagation for every request.
 *
 * <p>This interceptor is the primary gateway for multi-tenancy enforcement. It operates
 * in two phases per HTTP request:</p>
 *
 * <ol>
 *   <li><strong>Pre-handle</strong>: Extracts the {@code X-Tenant-ID} header value and
 *   stores it in {@link TenantContext} so that all downstream components — services,
 *   repositories, and even async tasks started within the same thread — can access the
 *   tenant identifier without explicit parameter passing.
 *   <ul>
 *     <li>If the request is authenticated (Spring Security principal is present) and the
 *     header is missing, the interceptor rejects the request with HTTP {@code 400 Bad Request}
 *     and a structured {@link ApiResponse} error body.</li>
 *     <li>If the request is not yet authenticated (e.g., {@code /auth/login},
 *     {@code /actuator/**}) and the header is absent, the request is allowed through
 *     without a tenant context so that public endpoints remain accessible.</li>
 *   </ul>
 *   </li>
 *   <li><strong>After-completion</strong>: Always clears the {@link TenantContext} to
 *   prevent stale tenant data from leaking to subsequent requests on the same pooled
 *   thread.</li>
 * </ol>
 *
 * <p>Registration is handled by
 * {@link com.vnpt.avplatform.shared.config.SharedAutoConfiguration}, which applies this
 * interceptor to all {@code /api/**} paths.</p>
 */
@Slf4j
@Component
public class TenantInterceptor implements HandlerInterceptor {

    /** HTTP header name used to convey the tenant identifier. */
    public static final String TENANT_HEADER = "X-Tenant-ID";

    private final ObjectMapper objectMapper;

    /**
     * Constructs the interceptor with a Jackson {@link ObjectMapper} for writing
     * structured error responses.
     *
     * @param objectMapper Spring-managed ObjectMapper; must not be {@code null}
     */
    public TenantInterceptor(ObjectMapper objectMapper) {
        if (objectMapper == null) {
            throw new IllegalArgumentException("objectMapper must not be null");
        }
        this.objectMapper = objectMapper;
    }

    /**
     * Extracts the {@code X-Tenant-ID} header and stores it in {@link TenantContext}.
     *
     * <p>If the current request is authenticated and the header is absent, this method
     * writes a {@code 400 Bad Request} JSON error body directly to the response and
     * returns {@code false}, halting further handler processing.</p>
     *
     * @param request  the current HTTP request
     * @param response the current HTTP response
     * @param handler  the chosen handler to execute (not used here)
     * @return {@code true} if tenant context was set or the request is unauthenticated;
     *         {@code false} if the request was rejected due to missing tenant header
     * @throws IOException if writing the error response fails
     */
    @Override
    public boolean preHandle(HttpServletRequest request,
                             HttpServletResponse response,
                             Object handler) throws IOException {

        String tenantId = request.getHeader(TENANT_HEADER);

        if (tenantId != null && !tenantId.isBlank()) {
            TenantContext.setTenantId(tenantId.trim());
            log.debug("Tenant context set: tenantId={}, uri={}", tenantId.trim(), request.getRequestURI());
            return true;
        }

        // Header is absent — check whether the request is authenticated
        if (isAuthenticated()) {
            log.warn("Missing {} header on authenticated request: uri={}, method={}",
                    TENANT_HEADER, request.getRequestURI(), request.getMethod());
            writeErrorResponse(response, request.getRequestURI());
            return false;
        }

        // Unauthenticated request (e.g., login, health-check) — allow through
        log.debug("No tenant header on unauthenticated request: uri={}", request.getRequestURI());
        return true;
    }

    /**
     * Always clears the {@link TenantContext} after the request completes, regardless
     * of whether an exception was thrown. This prevents thread-local leakage in
     * thread-pool environments.
     *
     * @param request   the current HTTP request
     * @param response  the current HTTP response
     * @param handler   the handler (or {@link org.springframework.web.servlet.HandlerExecutionChain})
     *                  that started async execution
     * @param ex        any exception thrown by the handler, or {@code null} on success
     */
    @Override
    public void afterCompletion(HttpServletRequest request,
                                HttpServletResponse response,
                                Object handler,
                                Exception ex) {
        TenantContext.clear();
        log.debug("Tenant context cleared: uri={}", request.getRequestURI());
    }

    // -------------------------------------------------------------------------
    // Private helpers
    // -------------------------------------------------------------------------

    /**
     * Returns {@code true} if there is an authenticated (non-anonymous) principal
     * in the current Spring Security context.
     *
     * @return {@code true} when the request is authenticated
     */
    private boolean isAuthenticated() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        return authentication != null
                && authentication.isAuthenticated()
                && !"anonymousUser".equals(authentication.getPrincipal());
    }

    /**
     * Writes a structured {@code 400 Bad Request} JSON error body directly to
     * {@code response}, bypassing the normal DispatcherServlet response pipeline.
     *
     * @param response   the HTTP response to write to
     * @param requestUri the URI of the rejected request (included in the trace)
     * @throws IOException if writing to the response output stream fails
     */
    private void writeErrorResponse(HttpServletResponse response, String requestUri) throws IOException {
        String traceId = UUID.randomUUID().toString();
        ApiResponse<Void> errorBody = ApiResponse.error(
                "MISSING_TENANT_HEADER",
                "The '" + TENANT_HEADER + "' request header is required for authenticated requests.",
                HttpStatus.BAD_REQUEST.value(),
                traceId
        );

        response.setStatus(HttpStatus.BAD_REQUEST.value());
        response.setContentType(MediaType.APPLICATION_JSON_VALUE);
        response.setCharacterEncoding("UTF-8");
        response.getWriter().write(objectMapper.writeValueAsString(errorBody));
        response.getWriter().flush();
    }
}
