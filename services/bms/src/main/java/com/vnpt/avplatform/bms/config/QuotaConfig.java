package com.vnpt.avplatform.bms.config;

/**
 * Quota enforcement configuration (BL-006, FR-BMS-010 through FR-BMS-013).
 *
 * <p>Redis key format: {@code quota:{tenantId}:{resourceType}:{YYYY-MM}}</p>
 *
 * <p>Quota thresholds:</p>
 * <ul>
 *   <li>80% usage → publish {@code QuotaWarningEvent} to Kafka → NCS sends alert to tenant admin</li>
 *   <li>100% usage → return HTTP 429 Too Many Requests</li>
 * </ul>
 *
 * <p>Sync interval: Redis counters are synced to MongoDB every 5 minutes for persistence
 * and audit trail.</p>
 */
public final class QuotaConfig {

    /**
     * Redis key format for quota counters.
     * Parameters: tenantId, resourceType (enum name), YYYY-MM month string.
     */
    public static final String QUOTA_KEY_FORMAT = "quota:%s:%s:%s";

    /**
     * Percentage threshold at which a {@code QuotaWarningEvent} is emitted.
     * Value 0.80 corresponds to 80% of the plan limit.
     */
    public static final double WARNING_THRESHOLD = 0.80;

    /**
     * Interval in seconds at which Redis quota counters are flushed to MongoDB.
     * Default: 300 seconds (5 minutes).
     */
    public static final long REDIS_SYNC_INTERVAL_SECONDS = 300L;

    /**
     * Resource types tracked for quota enforcement.
     */
    public enum QuotaResourceType {
        /** Number of trips executed in the billing period. */
        TRIP,
        /** Number of API calls made in the billing period. */
        API_CALL,
        /** Number of vehicles registered on the platform. */
        VEHICLE_REGISTRATION,
        /** Storage consumed in gigabytes. */
        STORAGE_GB
    }

    private QuotaConfig() {
        throw new UnsupportedOperationException("QuotaConfig is a constants class");
    }
}
