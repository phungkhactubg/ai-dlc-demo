package com.vnpt.avplatform.ncs.config;

/**
 * HMAC webhook security configuration (FR-NCS-041, ARCHITECTURE_SPEC Section 16.4).
 *
 * <p>Signature scheme:</p>
 * <ul>
 *   <li>Header: {@code X-VNPT-Signature: sha256={HMAC-SHA256(payload, secret)}}</li>
 *   <li>Timestamp tolerance: ±5 minutes (requires {@code X-VNPT-Timestamp} header)</li>
 *   <li>Secret rotation: old secret valid 30 minutes after rotation</li>
 * </ul>
 *
 * <p>Signature verification algorithm:</p>
 * <ol>
 *   <li>Read {@code X-VNPT-Timestamp} — reject if absent or outside tolerance window.</li>
 *   <li>Compute {@code HMAC-SHA256(requestBody, webhookSecret)} using the current secret.</li>
 *   <li>Compare computed signature against {@code X-VNPT-Signature} header value
 *       using constant-time comparison to prevent timing attacks.</li>
 *   <li>During grace period after rotation, also verify against the previous secret.</li>
 * </ol>
 */
public final class WebhookSecurityConfig {

    /** HTTP header carrying the HMAC-SHA256 signature of the request payload. */
    public static final String SIGNATURE_HEADER = "X-VNPT-Signature";

    /** HTTP header carrying the Unix epoch timestamp of the webhook delivery. */
    public static final String TIMESTAMP_HEADER = "X-VNPT-Timestamp";

    /**
     * Maximum allowed difference in seconds between the webhook timestamp and the server clock.
     * Default: 300 seconds (±5 minutes).
     */
    public static final long TIMESTAMP_TOLERANCE_SECONDS = 300L;

    /**
     * Duration in seconds for which the previous webhook secret remains valid after rotation.
     * Default: 1800 seconds (30 minutes).
     */
    public static final long SECRET_ROTATION_GRACE_SECONDS = 1800L;

    /** HMAC algorithm used for webhook payload signing. */
    public static final String HMAC_ALGORITHM = "HmacSHA256";

    /** Signature prefix included in the {@code X-VNPT-Signature} header value. */
    public static final String SIGNATURE_PREFIX = "sha256=";

    private WebhookSecurityConfig() {
        throw new UnsupportedOperationException("WebhookSecurityConfig is a constants class");
    }
}
