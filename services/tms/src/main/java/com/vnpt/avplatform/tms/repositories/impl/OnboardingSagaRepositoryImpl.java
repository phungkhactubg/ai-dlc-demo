package com.vnpt.avplatform.tms.repositories.impl;

import com.vnpt.avplatform.shared.repository.BaseMongoRepository;
import com.vnpt.avplatform.tms.exception.SagaStepException;
import com.vnpt.avplatform.tms.models.entity.OnboardingSaga;
import com.vnpt.avplatform.tms.models.entity.SagaStatus;
import com.vnpt.avplatform.tms.repositories.OnboardingSagaRepository;
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
public class OnboardingSagaRepositoryImpl extends BaseMongoRepository implements OnboardingSagaRepository {

    public OnboardingSagaRepositoryImpl(MongoTemplate mongoTemplate) {
        super(mongoTemplate);
    }

    @Override
    public OnboardingSaga save(OnboardingSaga saga) {
        // No withTenant() — saga is queried by sagaId/tenantId directly
        OnboardingSaga saved = mongoTemplate.save(saga);
        log.debug("Saved onboarding saga: sagaId={}, tenantId={}", saved.getSagaId(), saved.getTenantId());
        return saved;
    }

    @Override
    public Optional<OnboardingSaga> findBySagaId(String sagaId) {
        Query query = new Query(Criteria.where("saga_id").is(sagaId));
        return Optional.ofNullable(mongoTemplate.findOne(query, OnboardingSaga.class));
    }

    @Override
    public Optional<OnboardingSaga> findByTenantId(String tenantId) {
        Query query = new Query(Criteria.where("tenant_id").is(tenantId));
        return Optional.ofNullable(mongoTemplate.findOne(query, OnboardingSaga.class));
    }

    @Override
    public OnboardingSaga updateStatus(String sagaId, SagaStatus status) {
        Query query = new Query(Criteria.where("saga_id").is(sagaId));
        Update update = new Update().set("status", status);
        mongoTemplate.updateFirst(query, update, OnboardingSaga.class);
        return findBySagaId(sagaId)
                .orElseThrow(() -> new SagaStepException("Saga not found: " + sagaId));
    }

    @Override
    public OnboardingSaga updateStepStatus(String sagaId, int stepIndex, String stepStatus, String externalRef) {
        Query query = new Query(Criteria.where("saga_id").is(sagaId));
        Update update = new Update()
                .set("steps." + stepIndex + ".status", stepStatus)
                .set("steps." + stepIndex + ".completed_at", Instant.now())
                .set("current_step_index", stepIndex);
        if (externalRef != null && !externalRef.isBlank()) {
            update.set("steps." + stepIndex + ".external_ref", externalRef);
        }
        mongoTemplate.updateFirst(query, update, OnboardingSaga.class);
        return findBySagaId(sagaId)
                .orElseThrow(() -> new SagaStepException("Saga not found: " + sagaId));
    }

    @Override
    public OnboardingSaga appendCompensationLog(String sagaId, String logEntry) {
        Query query = new Query(Criteria.where("saga_id").is(sagaId));
        Update update = new Update().push("compensation_log", logEntry);
        mongoTemplate.updateFirst(query, update, OnboardingSaga.class);
        return findBySagaId(sagaId)
                .orElseThrow(() -> new SagaStepException("Saga not found: " + sagaId));
    }

    @Override
    public OnboardingSaga markCompleted(String sagaId) {
        Query query = new Query(Criteria.where("saga_id").is(sagaId));
        Update update = new Update()
                .set("status", SagaStatus.COMPLETED)
                .set("completed_at", Instant.now());
        mongoTemplate.updateFirst(query, update, OnboardingSaga.class);
        return findBySagaId(sagaId)
                .orElseThrow(() -> new SagaStepException("Saga not found: " + sagaId));
    }

    @Override
    public OnboardingSaga markFailed(String sagaId, String reason) {
        Query query = new Query(Criteria.where("saga_id").is(sagaId));
        Update update = new Update()
                .set("status", SagaStatus.FAILED)
                .set("failed_at", Instant.now())
                .push("compensation_log", "FAILED: " + reason);
        mongoTemplate.updateFirst(query, update, OnboardingSaga.class);
        return findBySagaId(sagaId)
                .orElseThrow(() -> new SagaStepException("Saga not found: " + sagaId));
    }
}
