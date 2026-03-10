package com.vnpt.avplatform.ncs.config;

/**
 * Notification channel configuration (FR-NCS-001, FR-NCS-002).
 *
 * <p>Channel routing by priority (BL-007 — Critical must deliver in &lt;5 seconds):</p>
 * <ul>
 *   <li>{@code CRITICAL} → Push (FCM/APNs) + SMS (Twilio) simultaneously</li>
 *   <li>{@code HIGH}     → Push only</li>
 *   <li>{@code MEDIUM}   → Email (SendGrid) + Push</li>
 *   <li>{@code LOW}      → Email or In-app</li>
 * </ul>
 *
 * <p>DLQ retry strategy (FR-NCS-031):</p>
 * <ul>
 *   <li>Attempt 1: immediate</li>
 *   <li>Retry 1: 1s backoff</li>
 *   <li>Retry 2: 2s backoff</li>
 *   <li>Retry 3: 4s backoff</li>
 *   <li>Exhausted → publish to {@code notification-dlq} Kafka topic</li>
 * </ul>
 *
 * <p>Adapter timeouts (BL-007):</p>
 * <ul>
 *   <li>FCM: 2s</li>
 *   <li>Twilio: 3s</li>
 *   <li>SendGrid: 3s</li>
 *   <li>Webhook: 4s</li>
 * </ul>
 */
public final class NotificationChannelConfig {

    /** Notification urgency level — determines which channels are activated. */
    public enum Priority {
        /** Life-safety or mission-critical alerts; triggers Push + SMS simultaneously. */
        CRITICAL,
        /** High-importance alerts; triggers Push only. */
        HIGH,
        /** Standard operational alerts; triggers Email + Push. */
        MEDIUM,
        /** Informational updates; triggers Email or In-App. */
        LOW
    }

    /** Available delivery channels for notifications. */
    public enum Channel {
        /** Firebase Cloud Messaging / APNs push notifications. */
        PUSH,
        /** SMS delivery via Twilio. */
        SMS,
        /** Email delivery via SendGrid. */
        EMAIL,
        /** In-application notification stored for retrieval by the frontend. */
        IN_APP,
        /** HTTP webhook delivery to a tenant-registered URL. */
        WEBHOOK
    }

    /** FCM adapter timeout in milliseconds (BL-007). */
    public static final int FCM_TIMEOUT_MS = 2000;

    /** Twilio SMS adapter timeout in milliseconds (BL-007). */
    public static final int TWILIO_TIMEOUT_MS = 3000;

    /** SendGrid email adapter timeout in milliseconds (BL-007). */
    public static final int SENDGRID_TIMEOUT_MS = 3000;

    /** Webhook HTTP adapter timeout in milliseconds (BL-007). */
    public static final int WEBHOOK_TIMEOUT_MS = 4000;

    /**
     * Maximum end-to-end delivery SLA for CRITICAL notifications in milliseconds (BL-007).
     * Delivery must complete within 5 seconds of event receipt.
     */
    public static final long NOTIFICATION_SLA_MS = 5000L;

    /** Kafka Dead-Letter Queue topic for exhausted notification retries. */
    public static final String NOTIFICATION_DLQ_TOPIC = "notification-dlq";

    private NotificationChannelConfig() {
        throw new UnsupportedOperationException("NotificationChannelConfig is a constants class");
    }
}
