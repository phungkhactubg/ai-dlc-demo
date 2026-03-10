package com.vnpt.avplatform.pay.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.mongodb.MongoDatabaseFactory;
import org.springframework.data.mongodb.MongoTransactionManager;

/**
 * MongoDB configuration for the PAY service.
 *
 * <p><strong>Architectural contract</strong>: All PAY repository queries MUST
 * extend {@code BaseMongoRepository} and call {@code withTenant()} to enforce
 * per-tenant data isolation (BL-001).</p>
 *
 * <p><strong>PCI-DSS</strong>: The PAY audit collection ({@code payment_audit_log})
 * is enforced as INSERT-only via a MongoDB JSON Schema validator. No UPDATE or
 * DELETE operations are permitted on this collection. This is validated at startup
 * by {@link PciDssAuditConfig}.</p>
 */
@Configuration
public class MongoConfig {

    /**
     * Registers a MongoDB transaction manager for atomic saga steps.
     *
     * @param factory the auto-configured {@link MongoDatabaseFactory}
     * @return the {@link MongoTransactionManager} bean
     */
    @Bean
    public MongoTransactionManager transactionManager(MongoDatabaseFactory factory) {
        return new MongoTransactionManager(factory);
    }
}
