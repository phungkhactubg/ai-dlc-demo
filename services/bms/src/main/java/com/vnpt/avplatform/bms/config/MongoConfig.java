package com.vnpt.avplatform.bms.config;

import com.mongodb.client.MongoClient;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.mongodb.MongoDatabaseFactory;
import org.springframework.data.mongodb.MongoTransactionManager;

import java.util.Objects;

/**
 * MongoDB configuration for the BMS service.
 *
 * <p>Provides a {@link MongoTransactionManager} bean to support multi-document
 * ACID transactions via {@code @Transactional} in service methods. Requires a
 * MongoDB replica set (configured via {@code MONGODB_URI}).</p>
 */
@Configuration
public class MongoConfig {

    private final MongoDatabaseFactory mongoDatabaseFactory;

    public MongoConfig(MongoDatabaseFactory mongoDatabaseFactory) {
        this.mongoDatabaseFactory = Objects.requireNonNull(mongoDatabaseFactory,
                "mongoDatabaseFactory must not be null");
    }

    /**
     * Registers the MongoDB transaction manager to enable {@code @Transactional}
     * support for multi-document MongoDB operations.
     *
     * @return the {@link MongoTransactionManager} bean
     */
    @Bean
    public MongoTransactionManager transactionManager() {
        return new MongoTransactionManager(mongoDatabaseFactory);
    }
}
