package com.vnpt.avplatform.ncs;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.kafka.annotation.EnableKafka;

/**
 * Entry point for the Notification &amp; Communication Service (NCS).
 *
 * <p>Responsibilities:</p>
 * <ul>
 *   <li>Multi-channel notification delivery: Push (FCM/APNs), SMS (Twilio), Email (SendGrid),
 *       In-App, and Webhook (FR-NCS-001, FR-NCS-002)</li>
 *   <li>Priority-based channel routing with SLA enforcement (BL-007: &lt;5 seconds for CRITICAL)</li>
 *   <li>DLQ retry strategy with exponential backoff (FR-NCS-031)</li>
 *   <li>HMAC-secured webhook delivery (FR-NCS-041)</li>
 * </ul>
 */
@SpringBootApplication
@EnableKafka
public class NcsApplication {

    public static void main(String[] args) {
        SpringApplication.run(NcsApplication.class, args);
    }
}
