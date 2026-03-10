package com.vnpt.avplatform.rhs.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.mongodb.MongoDatabaseFactory;
import org.springframework.data.mongodb.MongoTransactionManager;

/**
 * MongoDB configuration for the RHS service.
 *
 * <p>Registers a {@link MongoTransactionManager} to enable multi-document ACID
 * transactions. Requires a MongoDB replica set (configured via {@code MONGODB_URI}).
 */
@Configuration
public class MongoConfig {

    @Bean
    public MongoTransactionManager mongoTransactionManager(MongoDatabaseFactory dbFactory) {
        return new MongoTransactionManager(dbFactory);
    }
}
