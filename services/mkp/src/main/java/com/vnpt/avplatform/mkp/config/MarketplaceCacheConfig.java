package com.vnpt.avplatform.mkp.config;

import org.springframework.context.annotation.Configuration;

/**
 * Marketplace catalog Redis cache configuration (FR-MKP-001, FR-MKP-003).
 *
 * <p>The marketplace plugin catalog is cached in Redis per tenant for fast retrieval.
 * The cache is invalidated whenever a plugin's status changes to or from
 * {@link PartnerAuditConfig.PartnerStatus#PUBLISHED} or
 * {@link PartnerAuditConfig.PartnerStatus#SUSPENDED}.</p>
 *
 * <p>Cache key format: {@value #CATALOG_CACHE_KEY} where {@code %s} is the tenant ID.
 * This ensures strict tenant isolation in the catalog cache.</p>
 *
 * <p>TTL: {@value #CATALOG_CACHE_TTL_SECONDS} seconds (5 minutes). After expiry, the
 * catalog is re-fetched from MongoDB and re-cached transparently.</p>
 */
@Configuration
public class MarketplaceCacheConfig {

    /**
     * Redis key template for the per-tenant marketplace catalog cache.
     * Usage: {@code String.format(CATALOG_CACHE_KEY, tenantId)}
     */
    public static final String CATALOG_CACHE_KEY = "mkp:catalog:%s";

    /** Time-to-live for the catalog cache in seconds (5 minutes). */
    public static final long CATALOG_CACHE_TTL_SECONDS = 300L;

    /** Redis key prefix for individual plugin detail cache entries. */
    public static final String PLUGIN_DETAIL_CACHE_KEY = "mkp:plugin:%s:%s";

    /** Time-to-live for individual plugin detail cache in seconds (10 minutes). */
    public static final long PLUGIN_DETAIL_CACHE_TTL_SECONDS = 600L;
}
