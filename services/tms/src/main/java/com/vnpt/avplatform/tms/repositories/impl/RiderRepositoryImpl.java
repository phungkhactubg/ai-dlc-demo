package com.vnpt.avplatform.tms.repositories.impl;

import com.vnpt.avplatform.shared.TenantContext;
import com.vnpt.avplatform.shared.repository.BaseMongoRepository;
import com.vnpt.avplatform.tms.exception.RiderNotFoundException;
import com.vnpt.avplatform.tms.models.entity.Rider;
import com.vnpt.avplatform.tms.models.entity.RiderStatus;
import com.vnpt.avplatform.tms.repositories.RiderRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.data.mongodb.core.query.Criteria;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.data.mongodb.core.query.Update;
import org.springframework.stereotype.Repository;

import java.time.Instant;
import java.util.Optional;

@Slf4j
@Repository
public class RiderRepositoryImpl extends BaseMongoRepository implements RiderRepository {

    public RiderRepositoryImpl(MongoTemplate mongoTemplate) {
        super(mongoTemplate);
    }

    @Override
    public Rider save(Rider rider) {
        // No withTenant() — rider entity carries its own tenantId field
        Rider saved = mongoTemplate.save(rider);
        log.debug("Saved rider: riderId={}, tenantId={}", saved.getRiderId(), saved.getTenantId());
        return saved;
    }

    @Override
    public Optional<Rider> findByRiderId(String riderId) {
        String tenantId = TenantContext.getTenantId();
        Criteria criteria = Criteria.where("rider_id").is(riderId);
        if (tenantId != null && !tenantId.isBlank()) {
            criteria = criteria.and("tenant_id").is(tenantId);
        }
        return Optional.ofNullable(mongoTemplate.findOne(new Query(criteria), Rider.class));
    }

    @Override
    public Optional<Rider> findByEmailAndTenantId(String email, String tenantId) {
        Query query = new Query(
                Criteria.where("email").is(email).and("tenant_id").is(tenantId));
        return Optional.ofNullable(mongoTemplate.findOne(query, Rider.class));
    }

    @Override
    public Optional<Rider> findByPhoneNumberAndTenantId(String phone, String tenantId) {
        Query query = new Query(
                Criteria.where("phone_number").is(phone).and("tenant_id").is(tenantId));
        return Optional.ofNullable(mongoTemplate.findOne(query, Rider.class));
    }

    @Override
    public Optional<Rider> findByKeycloakSub(String sub) {
        // No tenant filter — keycloak_sub is globally unique across tenants
        Query query = new Query(Criteria.where("keycloak_sub").is(sub));
        return Optional.ofNullable(mongoTemplate.findOne(query, Rider.class));
    }

    @Override
    public Rider updateStatus(String riderId, RiderStatus status) {
        String tenantId = TenantContext.getTenantId();
        Criteria criteria = Criteria.where("rider_id").is(riderId);
        if (tenantId != null && !tenantId.isBlank()) {
            criteria = criteria.and("tenant_id").is(tenantId);
        }
        Update update = new Update()
                .set("status", status)
                .set("updated_at", Instant.now());
        mongoTemplate.updateFirst(new Query(criteria), update, Rider.class);
        return findByRiderId(riderId)
                .orElseThrow(() -> new RiderNotFoundException("Rider not found: " + riderId));
    }

    @Override
    public boolean existsByEmailAndTenantId(String email, String tenantId) {
        Query query = new Query(
                Criteria.where("email").is(email).and("tenant_id").is(tenantId));
        return mongoTemplate.exists(query, Rider.class);
    }
}
