package com.vnpt.avplatform.shared;

/**
 * Thread-local storage for the current tenant context.
 *
 * <p>Each incoming HTTP request is associated with a specific tenant, identified
 * by a tenant ID extracted from the {@code X-Tenant-ID} request header by
 * {@link com.vnpt.avplatform.shared.interceptor.TenantInterceptor}. The tenant ID
 * is stored here so that downstream components (services, repositories) can access
 * it without explicit parameter passing.</p>
 *
 * <p><strong>Memory-leak warning:</strong> {@link #clear()} MUST be called after
 * each request (guaranteed by {@code TenantInterceptor#afterCompletion}) to prevent
 * thread-local values from leaking across requests in thread-pool based servers.</p>
 *
 * <p>Usage example:</p>
 * <pre>{@code
 * // Set by TenantInterceptor on request entry
 * TenantContext.setTenantId("tenant-abc");
 *
 * // Read anywhere in the call stack
 * String tenantId = TenantContext.getTenantId();
 *
 * // Cleared by TenantInterceptor in afterCompletion
 * TenantContext.clear();
 * }</pre>
 */
public final class TenantContext {

    private static final ThreadLocal<String> TENANT_ID = new ThreadLocal<>();

    /** Utility class — do not instantiate. */
    private TenantContext() {
        throw new UnsupportedOperationException("TenantContext is a utility class");
    }

    /**
     * Stores the given tenant ID in the current thread's context.
     *
     * @param tenantId the tenant identifier; must not be {@code null} or blank
     */
    public static void setTenantId(String tenantId) {
        TENANT_ID.set(tenantId);
    }

    /**
     * Returns the tenant ID associated with the current thread, or {@code null}
     * if no tenant has been set (e.g., unauthenticated or non-tenant request).
     *
     * @return the current tenant ID, or {@code null}
     */
    public static String getTenantId() {
        return TENANT_ID.get();
    }

    /**
     * Removes the tenant ID from the current thread's context.
     *
     * <p>This method MUST be called at the end of every request cycle to prevent
     * stale tenant data from leaking to subsequent requests handled by the same
     * thread (common in application-server thread pools).</p>
     */
    public static void clear() {
        TENANT_ID.remove();
    }
}
