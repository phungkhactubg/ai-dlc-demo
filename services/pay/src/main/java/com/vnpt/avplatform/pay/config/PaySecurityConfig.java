package com.vnpt.avplatform.pay.config;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.annotation.Configuration;

/**
 * PAY service security policy documentation (ADR-003, PCI-DSS).
 *
 * <p><strong>Namespace isolation</strong>: The PAY service runs exclusively in the
 * {@code pay-namespace} Kubernetes namespace. Network policies enforce that only
 * services within the platform mesh (specifically RHS) can reach PAY endpoints.
 * No direct rider-facing or public internet access is permitted.</p>
 *
 * <p><strong>Role requirements</strong>: All PAY API endpoints require the caller's
 * JWT to carry either {@code ROLE_INTERNAL_SERVICE} (service-to-service) or
 * {@code ROLE_PLATFORM_ADMIN} (ops/admin tooling). This is enforced in
 * {@link SecurityConfig#securityFilterChain}.</p>
 *
 * <p><strong>PCI-DSS constraints</strong>:</p>
 * <ul>
 *   <li>No cardholder data is stored — tokenization only.</li>
 *   <li>All audit events are written to an INSERT-only MongoDB collection validated
 *       by {@link PciDssAuditConfig}.</li>
 *   <li>Idempotency keys are enforced via Redis (BL-004) — see {@link IdempotencyConfig}.</li>
 *   <li>TLS 1.2+ is required for all service-to-service communication (enforced at
 *       the Kubernetes Ingress and service mesh level).</li>
 * </ul>
 */
@Configuration
public class PaySecurityConfig {

    private static final Logger log = LoggerFactory.getLogger(PaySecurityConfig.class);

    /**
     * Logs the PCI-DSS isolation confirmation at startup.
     *
     * <p>This constructor acts as a startup audit hook confirming that the PAY service
     * is loaded under its expected security posture.</p>
     */
    public PaySecurityConfig() {
        log.info("PAY service security posture: PCI-DSS isolated namespace=pay-namespace, " +
                 "roles required=[ROLE_INTERNAL_SERVICE, ROLE_PLATFORM_ADMIN], " +
                 "public endpoints=NONE (ADR-003)");
    }
}
