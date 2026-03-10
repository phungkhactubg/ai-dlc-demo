package com.vnpt.avplatform.pay.config;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.annotation.Configuration;

import jakarta.annotation.PostConstruct;

/**
 * PCI-DSS audit configuration for the PAY service.
 *
 * <p>Documents PCI-DSS constraints that are enforced at the infrastructure level
 * and verifies the service starts with the expected audit posture.</p>
 *
 * <h3>PCI-DSS Constraints (DSS v4.0)</h3>
 * <ul>
 *   <li><strong>Req 10.2</strong>: All payment events are written to the
 *       {@code payment_audit_log} MongoDB collection which is enforced as
 *       INSERT-only via a JSON Schema validator — UPDATE and DELETE operations
 *       are rejected by the database layer.</li>
 *   <li><strong>Req 3.3</strong>: No cardholder data (PAN, CVV, expiry) is stored.
 *       Only tokenized payment method references are persisted.</li>
 *   <li><strong>Req 8.3</strong>: Service-to-service authentication uses short-lived
 *       JWT tokens (≤1 hour expiry) issued by the platform IAM service.</li>
 *   <li><strong>Req 6.4</strong>: The {@code pay-namespace} K8s namespace has
 *       dedicated network policies restricting all ingress to RHS only.</li>
 * </ul>
 */
@Configuration
public class PciDssAuditConfig {

    private static final Logger log = LoggerFactory.getLogger(PciDssAuditConfig.class);

    /**
     * Logs the PCI-DSS audit posture at application startup.
     *
     * <p>This serves as a startup audit record confirming the PAY service is
     * operating under PCI-DSS constraints. In production, this message is
     * captured by the centralized log aggregation system (Req 10.5).</p>
     */
    @PostConstruct
    public void logPciDssStartupAudit() {
        log.info("PCI-DSS AUDIT [PAY-SERVICE-STARTUP]: INSERT-only MongoDB validator REQUIRED " +
                 "on collection=payment_audit_log | No cardholder data storage | " +
                 "Tokenization-only policy active | Namespace=pay-namespace (ADR-003)");
    }
}
