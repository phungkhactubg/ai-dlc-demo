package com.vnpt.avplatform.mkp.config;

import org.springframework.context.annotation.Configuration;

/**
 * Partner audit gate configuration (BL-009, FR-MKP-010, FR-MKP-011).
 *
 * <p>Defines the partner/plugin lifecycle state machine and enforcement constants.
 * The partner status progresses through the following states:</p>
 *
 * <pre>
 * Registered → UnderReview → SecurityAudit → PerformanceTest → Approved → Published
 *                                          ↘ Rejected (at SecurityAudit or PerformanceTest)
 *                                                          ↗
 * Published → Suspended (admin action)
 * </pre>
 *
 * <p><strong>BL-009</strong>: A plugin ONLY appears on the Marketplace after passing
 * BOTH security audit AND performance test. {@code status == PUBLISHED} is the only
 * state that makes a plugin visible in the catalog.</p>
 *
 * <p><strong>Approval requirements</strong>: The JWT must contain the
 * {@value #ADMIN_ROLE} claim. Enforced via {@code @PreAuthorize} at the service layer.</p>
 *
 * <p><strong>Rejection requirements</strong>: The rejection reason must be provided
 * and contain at least {@value #MIN_REJECTION_REASON_LENGTH} characters to ensure
 * actionable feedback.</p>
 *
 * <p><strong>Immutable audit log</strong>: ALL status transitions MUST be recorded
 * in the {@code auditLog} array field of the partner document using MongoDB {@code $push}
 * (append-only). No audit log entries may be deleted or modified.</p>
 */
@Configuration
public class PartnerAuditConfig {

    /** Spring Security role required for marketplace admin operations. */
    public static final String ADMIN_ROLE = "ROLE_MARKETPLACE_ADMIN";

    /** Minimum character length for a rejection reason to be considered valid. */
    public static final int MIN_REJECTION_REASON_LENGTH = 10;

    /**
     * Represents the possible states in the partner/plugin lifecycle state machine.
     *
     * <p>State transition rules:</p>
     * <ul>
     *   <li>{@code REGISTERED} → {@code UNDER_REVIEW} (automatic on submission)</li>
     *   <li>{@code UNDER_REVIEW} → {@code SECURITY_AUDIT} (admin action)</li>
     *   <li>{@code SECURITY_AUDIT} → {@code PERFORMANCE_TEST} or {@code REJECTED} (admin action)</li>
     *   <li>{@code PERFORMANCE_TEST} → {@code APPROVED} or {@code REJECTED} (admin action)</li>
     *   <li>{@code APPROVED} → {@code PUBLISHED} (admin action)</li>
     *   <li>{@code PUBLISHED} → {@code SUSPENDED} (admin action)</li>
     *   <li>{@code SUSPENDED} → {@code APPROVED} (admin action, re-activation)</li>
     * </ul>
     */
    public enum PartnerStatus {
        REGISTERED,
        UNDER_REVIEW,
        SECURITY_AUDIT,
        PERFORMANCE_TEST,
        APPROVED,
        PUBLISHED,
        SUSPENDED,
        REJECTED
    }
}
