package com.vnpt.avplatform.fpe.config;

import org.springframework.context.annotation.Configuration;

/**
 * Fare calculation formula constants and cache key patterns for the FPE service.
 *
 * <p><b>Fare Formula (FR-FPE-001):</b>
 * <pre>
 *   Fare = (BaseFee + DistanceRate × km + TimeRate × minutes)
 *          × SurgeMultiplier × VehicleTierFactor
 *          − PromotionDiscount
 *          + PlatformFeePercentage
 * </pre>
 *
 * <p><b>Surge constraints (BL-002):</b>
 * {@code SurgeMultiplier ∈ [1.0, min(3.0, tenant_surge_cap)]}
 * — tenants may configure a surge cap below the platform maximum.
 *
 * <p><b>Upfront Pricing (FR-FPE-002):</b>
 * Fare is locked at booking time. Route deviations are absorbed by the platform;
 * passengers are never charged retroactively.
 *
 * <p><b>Cache target (FR-FPE-003):</b>
 * Fare estimates must be served in &lt;200 ms via Redis cache (TTL {@value #FARE_CACHE_TTL_SECONDS}s).
 */
@Configuration
public class FareFormulaConfig {

    /** Minimum allowed surge multiplier (no negative surging). */
    public static final double MIN_SURGE_MULTIPLIER = 1.0;

    /** Platform-wide maximum surge multiplier cap (BL-002). */
    public static final double MAX_SURGE_MULTIPLIER = 3.0;

    /** Redis TTL for cached fare estimates in seconds (FR-FPE-003). */
    public static final long FARE_CACHE_TTL_SECONDS = 60L;

    /**
     * Redis key pattern for fare estimate cache entries.
     * <p>Arguments: {@code tenant}, {@code pickupHash}, {@code dropoffHash}, {@code vehicleType}.
     */
    public static final String FARE_CACHE_KEY_FORMAT = "fare:estimate:%s:%s:%s:%s";

    /**
     * Redis key pattern for surge multiplier cache entries per grid cell.
     * <p>Arguments: {@code tenant}, {@code gridCellId}.
     */
    public static final String SURGE_CACHE_KEY_FORMAT = "surge:%s:%s";
}
