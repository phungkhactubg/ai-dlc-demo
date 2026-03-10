package com.vnpt.avplatform.tms.repositories.impl;

import com.vnpt.avplatform.shared.repository.BaseMongoRepository;
import com.vnpt.avplatform.tms.exception.TenantNotFoundException;
import com.vnpt.avplatform.tms.models.entity.Tenant;
import com.vnpt.avplatform.tms.models.entity.TenantBranding;
import com.vnpt.avplatform.tms.models.entity.TenantStatus;
import com.vnpt.avplatform.tms.repositories.TenantRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Sort;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.data.mongodb.core.query.Criteria;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.data.mongodb.core.query.Update;
import org.springframework.stereotype.Repository;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@Slf4j
@Repository
public class TenantRepositoryImpl extends BaseMongoRepository implements TenantRepository {

    public TenantRepositoryImpl(MongoTemplate mongoTemplate) {
        super(mongoTemplate);
    }

    @Override
    public Tenant save(Tenant tenant) {
        // No withTenant() — bootstrap scenario; tenant_id IS the record being created
        Tenant saved = mongoTemplate.save(tenant);
        log.debug("Saved tenant: tenantId={}", saved.getTenantId());
        return saved;
    }

    @Override
    public Optional<Tenant> findByTenantId(String tenantId) {
        Query query = new Query(Criteria.where("tenant_id").is(tenantId));
        return Optional.ofNullable(mongoTemplate.findOne(query, Tenant.class));
    }

    @Override
    public Optional<Tenant> findByCompanyDomain(String domain) {
        Query query = new Query(Criteria.where("company_domain").is(domain));
        return Optional.ofNullable(mongoTemplate.findOne(query, Tenant.class));
    }

    @Override
    public List<Tenant> findAll(int page, int size) {
        Query query = new Query()
                .with(Sort.by(Sort.Direction.DESC, "created_at"))
                .skip((long) page * size)
                .limit(size);
        return mongoTemplate.find(query, Tenant.class);
    }

    @Override
    public long count() {
        return mongoTemplate.count(new Query(), Tenant.class);
    }

    @Override
    public boolean existsByTenantId(String tenantId) {
        Query query = new Query(Criteria.where("tenant_id").is(tenantId));
        return mongoTemplate.exists(query, Tenant.class);
    }

    @Override
    public boolean existsByCompanyDomain(String domain) {
        Query query = new Query(Criteria.where("company_domain").is(domain));
        return mongoTemplate.exists(query, Tenant.class);
    }

    @Override
    public Tenant updateStatus(String tenantId, TenantStatus status) {
        Query query = new Query(Criteria.where("tenant_id").is(tenantId));
        Update update = new Update()
                .set("status", status)
                .set("updated_at", Instant.now());
        mongoTemplate.updateFirst(query, update, Tenant.class);
        return findByTenantId(tenantId)
                .orElseThrow(() -> new TenantNotFoundException("Tenant not found: " + tenantId));
    }

    @Override
    public Tenant updateBranding(String tenantId, TenantBranding branding) {
        Query query = new Query(Criteria.where("tenant_id").is(tenantId));
        Update update = new Update()
                .set("branding", branding)
                .set("updated_at", Instant.now());
        mongoTemplate.updateFirst(query, update, Tenant.class);
        return findByTenantId(tenantId)
                .orElseThrow(() -> new TenantNotFoundException("Tenant not found: " + tenantId));
    }

    @Override
    public Tenant updateFeatureFlags(String tenantId, Map<String, Boolean> flags) {
        Query query = new Query(Criteria.where("tenant_id").is(tenantId));
        Update update = new Update()
                .set("feature_flags", flags)
                .set("updated_at", Instant.now());
        mongoTemplate.updateFirst(query, update, Tenant.class);
        return findByTenantId(tenantId)
                .orElseThrow(() -> new TenantNotFoundException("Tenant not found: " + tenantId));
    }
}
