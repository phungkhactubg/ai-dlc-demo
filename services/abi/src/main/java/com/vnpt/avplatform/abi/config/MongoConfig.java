package com.vnpt.avplatform.abi.config;

import com.mongodb.client.MongoClient;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.mongodb.MongoDatabaseFactory;
import org.springframework.data.mongodb.MongoTransactionManager;

/**
 * MongoDB configuration for the ABI service.
 *
 * <p>Registers a {@link MongoTransactionManager} to support multi-document ACID transactions
 * when storing analytics facts atomically across multiple collections. Requires a MongoDB
 * replica set (configured via {@code MONGODB_URI} with {@code replicaSet=rs0}).</p>
 */
@Configuration
public class MongoConfig {

    /**
     * Creates a {@link MongoTransactionManager} backed by the auto-configured
     * {@link MongoDatabaseFactory}.
     *
     * @param dbFactory the auto-configured MongoDB database factory
     * @return a transaction manager that enables multi-document ACID transactions
     */
    @Bean
    public MongoTransactionManager transactionManager(MongoDatabaseFactory dbFactory) {
        return new MongoTransactionManager(dbFactory);
    }
}
