package com.vnpt.avplatform.pay.config;

import org.springframework.context.annotation.Configuration;

/**
 * Redis-based idempotency configuration for the PAY service (BL-004).
 *
 * <p>Every payment request must carry an {@code Idempotency-Key} header. The key is
 * stored in Redis with a 24-hour TTL to prevent duplicate payment processing on
 * client retries. If a request arrives with an already-processed idempotency key,
 * the cached response is returned immediately without re-executing the payment.</p>
 *
 * <h3>Redis key format</h3>
 * <pre>
 *   {@value #KEY_PREFIX}{tenantId}:{idempotencyKey}
 * </pre>
 *
 * <h3>TTL</h3>
 * <pre>
 *   {@value #TTL_SECONDS} seconds (24 hours)
 * </pre>
 */
@Configuration
public class IdempotencyConfig {

    /**
     * Prefix for all idempotency keys stored in Redis.
     * Full key: {@code idempotency:pay:{tenantId}:{idempotencyKey}}
     */
    public static final String KEY_PREFIX = "idempotency:pay:";

    /**
     * Time-to-live for idempotency entries in Redis — 86400 seconds (24 hours).
     */
    public static final long TTL_SECONDS = 86400L;
}
