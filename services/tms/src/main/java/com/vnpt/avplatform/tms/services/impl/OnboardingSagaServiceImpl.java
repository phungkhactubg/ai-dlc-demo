package com.vnpt.avplatform.tms.services.impl;

import com.vnpt.avplatform.tms.adapters.SagaStepAdapter;
import com.vnpt.avplatform.tms.events.publisher.TenantKafkaProducer;
import com.vnpt.avplatform.tms.exception.SagaStepException;
import com.vnpt.avplatform.tms.models.entity.OnboardingSaga;
import com.vnpt.avplatform.tms.models.entity.SagaStatus;
import com.vnpt.avplatform.tms.models.entity.SagaStep;
import com.vnpt.avplatform.tms.models.entity.TenantStatus;
import com.vnpt.avplatform.tms.repositories.OnboardingSagaRepository;
import com.vnpt.avplatform.tms.repositories.TenantRepository;
import com.vnpt.avplatform.tms.services.OnboardingSagaCompensation;
import com.vnpt.avplatform.tms.services.OnboardingSagaService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.function.Function;
import java.util.stream.Collectors;

@Slf4j
@Service
public class OnboardingSagaServiceImpl implements OnboardingSagaService {

    private static final List<String> STEP_ORDER = List.of("SSC", "BMS", "DPE", "VMS");
    private static final int STEP_TIMEOUT_SECONDS = 30;

    private final OnboardingSagaRepository sagaRepository;
    private final TenantRepository tenantRepository;
    private final OnboardingSagaCompensation compensationService;
    private final TenantKafkaProducer kafkaProducer;
    private final Map<String, SagaStepAdapter> adaptersByName;

    public OnboardingSagaServiceImpl(
            OnboardingSagaRepository sagaRepository,
            TenantRepository tenantRepository,
            OnboardingSagaCompensation compensationService,
            TenantKafkaProducer kafkaProducer,
            List<SagaStepAdapter> sagaStepAdapters) {
        this.sagaRepository = Objects.requireNonNull(sagaRepository, "sagaRepository must not be null");
        this.tenantRepository = Objects.requireNonNull(tenantRepository, "tenantRepository must not be null");
        this.compensationService = Objects.requireNonNull(compensationService, "compensationService must not be null");
        this.kafkaProducer = Objects.requireNonNull(kafkaProducer, "kafkaProducer must not be null");
        this.adaptersByName = sagaStepAdapters.stream()
                .collect(Collectors.toMap(SagaStepAdapter::getStepName, Function.identity()));
    }

    @Override
    @Async("sagaExecutor")
    public void startSaga(String tenantId, String planId, Map<String, Object> context) {
        log.info("Starting onboarding saga: tenantId={}, planId={}", tenantId, planId);

        List<SagaStep> steps = new ArrayList<>();
        for (String stepName : STEP_ORDER) {
            steps.add(SagaStep.builder().stepName(stepName).status("PENDING").build());
        }

        OnboardingSaga saga = OnboardingSaga.builder()
                .sagaId(UUID.randomUUID().toString())
                .tenantId(tenantId)
                .status(SagaStatus.IN_PROGRESS)
                .steps(steps)
                .currentStepIndex(0)
                .startedAt(Instant.now())
                .build();

        saga = sagaRepository.save(saga);
        String sagaId = saga.getSagaId();

        int lastCompletedStepIndex = -1;
        for (int i = 0; i < STEP_ORDER.size(); i++) {
            String stepName = STEP_ORDER.get(i);
            SagaStepAdapter adapter = adaptersByName.get(stepName);
            if (adapter == null) {
                log.error("No adapter found for step: {}, sagaId={}", stepName, sagaId);
                handleStepFailure(sagaId, tenantId, i, lastCompletedStepIndex, "No adapter found for step: " + stepName);
                return;
            }

            final int stepIndex = i;
            final Map<String, Object> ctx = context;
            try {
                String externalRef = CompletableFuture
                        .supplyAsync(() -> {
                            try {
                                return adapter.execute(tenantId, ctx);
                            } catch (SagaStepException e) {
                                throw new RuntimeException(e);
                            }
                        })
                        .get(STEP_TIMEOUT_SECONDS, TimeUnit.SECONDS);

                sagaRepository.updateStepStatus(sagaId, stepIndex, "COMPLETED", externalRef);
                lastCompletedStepIndex = stepIndex;
                log.info("Saga step completed: sagaId={}, step={}, externalRef={}", sagaId, stepName, externalRef);

            } catch (TimeoutException e) {
                log.error("Saga step timed out: sagaId={}, step={}", sagaId, stepName);
                handleStepFailure(sagaId, tenantId, stepIndex, lastCompletedStepIndex,
                        "Step timed out after " + STEP_TIMEOUT_SECONDS + "s");
                return;
            } catch (Exception e) {
                log.error("Saga step failed: sagaId={}, step={}, error={}", sagaId, stepName, e.getMessage(), e);
                handleStepFailure(sagaId, tenantId, stepIndex, lastCompletedStepIndex, e.getMessage());
                return;
            }
        }

        sagaRepository.markCompleted(sagaId);
        tenantRepository.updateStatus(tenantId, TenantStatus.ACTIVE);
        log.info("Onboarding saga completed: sagaId={}, tenantId={}", sagaId, tenantId);

        kafkaProducer.publish("tenant.created", tenantId, Map.of(
                "tenantId", tenantId,
                "planId", planId,
                "sagaId", sagaId
        ));
    }

    private void handleStepFailure(String sagaId, String tenantId, int failedStepIndex,
                                   int lastCompletedStepIndex, String reason) {
        try {
            sagaRepository.updateStepStatus(sagaId, failedStepIndex, "FAILED", null);
            sagaRepository.markFailed(sagaId, reason);
        } catch (Exception e) {
            log.error("Failed to mark saga step as failed: sagaId={}", sagaId, e);
        }
        compensationService.compensate(sagaId, tenantId, lastCompletedStepIndex);
    }
}
