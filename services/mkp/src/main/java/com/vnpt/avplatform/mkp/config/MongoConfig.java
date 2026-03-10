package com.vnpt.avplatform.mkp.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.mongodb.MongoDatabaseFactory;
import org.springframework.data.mongodb.MongoTransactionManager;

/**
 * MongoDB configuration for the MKP service.
 *
 * <p>Registers a {@link MongoTransactionManager} to support multi-document ACID transactions.
 * This is required for atomic partner status transitions — the audit log entry and the
 * partner document update must succeed or fail together (BL-009).</p>
 *
 * <p>Requires a MongoDB replica set configured via {@code MONGODB_URI} with
 * {@code replicaSet=rs0}.</p>
 */
@Configuration
public class MongoConfig {

    /**
     * Creates a {@link MongoTransactionManager} backed by the auto-configured
     * {@link MongoDatabaseFactory}.
     *
     * @param dbFactory the auto-configured MongoDB database factory
     * @return a transaction manager enabling multi-document ACID transactions
     */
    @Bean
    public MongoTransactionManager transactionManager(MongoDatabaseFactory dbFactory) {
        return new MongoTransactionManager(dbFactory);
    }
}
