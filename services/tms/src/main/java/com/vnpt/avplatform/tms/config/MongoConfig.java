package com.vnpt.avplatform.tms.config;

import com.vnpt.avplatform.tms.models.entity.OnboardingSaga;
import com.vnpt.avplatform.tms.models.entity.Rider;
import com.vnpt.avplatform.tms.models.entity.Tenant;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.event.EventListener;
import org.springframework.data.domain.Sort;
import org.springframework.data.mongodb.MongoDatabaseFactory;
import org.springframework.data.mongodb.MongoTransactionManager;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.data.mongodb.core.index.Index;
import org.springframework.data.mongodb.core.index.IndexOperations;

import java.util.Objects;

@Slf4j
@Configuration
public class MongoConfig {

    private final MongoTemplate mongoTemplate;

    public MongoConfig(MongoTemplate mongoTemplate) {
        this.mongoTemplate = Objects.requireNonNull(mongoTemplate, "mongoTemplate must not be null");
    }

    @Bean
    public MongoTransactionManager transactionManager(MongoDatabaseFactory factory) {
        return new MongoTransactionManager(factory);
    }

    @EventListener(ApplicationReadyEvent.class)
    public void createIndexes() {
        log.info("Creating MongoDB indexes for TMS collections...");

        // tenants collection
        IndexOperations tenantIdx = mongoTemplate.indexOps(Tenant.class);
        tenantIdx.ensureIndex(new Index().on("tenant_id", Sort.Direction.ASC).unique().named("idx_tenant_id_unique"));
        tenantIdx.ensureIndex(new Index().on("company_domain", Sort.Direction.ASC).unique().named("idx_company_domain_unique"));

        // riders collection
        IndexOperations riderIdx = mongoTemplate.indexOps(Rider.class);
        riderIdx.ensureIndex(new Index().on("tenant_id", Sort.Direction.ASC).named("idx_rider_tenant_id"));
        riderIdx.ensureIndex(new Index().on("email", Sort.Direction.ASC).named("idx_rider_email"));
        riderIdx.ensureIndex(new Index().on("keycloak_sub", Sort.Direction.ASC).sparse().named("idx_rider_keycloak_sub"));

        // onboarding_sagas collection
        IndexOperations sagaIdx = mongoTemplate.indexOps(OnboardingSaga.class);
        sagaIdx.ensureIndex(new Index().on("saga_id", Sort.Direction.ASC).unique().named("idx_saga_id_unique"));
        sagaIdx.ensureIndex(new Index().on("tenant_id", Sort.Direction.ASC).unique().named("idx_saga_tenant_id_unique"));

        log.info("MongoDB indexes created successfully.");
    }
}
