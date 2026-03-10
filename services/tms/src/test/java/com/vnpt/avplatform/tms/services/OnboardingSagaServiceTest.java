package com.vnpt.avplatform.tms.services;

import com.vnpt.avplatform.tms.adapters.SagaStepAdapter;
import com.vnpt.avplatform.tms.events.publisher.TenantKafkaProducer;
import com.vnpt.avplatform.tms.exception.SagaStepException;
import com.vnpt.avplatform.tms.models.entity.OnboardingSaga;
import com.vnpt.avplatform.tms.models.entity.SagaStatus;
import com.vnpt.avplatform.tms.models.entity.SagaStep;
import com.vnpt.avplatform.tms.models.entity.TenantStatus;
import com.vnpt.avplatform.tms.repositories.OnboardingSagaRepository;
import com.vnpt.avplatform.tms.repositories.TenantRepository;
import com.vnpt.avplatform.tms.services.impl.OnboardingSagaServiceImpl;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.doNothing;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class OnboardingSagaServiceTest {

    @Mock
    private OnboardingSagaRepository sagaRepository;

    @Mock
    private TenantRepository tenantRepository;

    @Mock
    private OnboardingSagaCompensation compensationService;

    @Mock
    private TenantKafkaProducer kafkaProducer;

    @Mock
    private SagaStepAdapter sscAdapter;

    @Mock
    private SagaStepAdapter bmsAdapter;

    @Mock
    private SagaStepAdapter dpeAdapter;

    @Mock
    private SagaStepAdapter vmsAdapter;

    private OnboardingSagaServiceImpl sagaService;

    @BeforeEach
    void setUp() {
        when(sscAdapter.getStepName()).thenReturn("SSC");
        when(bmsAdapter.getStepName()).thenReturn("BMS");
        when(dpeAdapter.getStepName()).thenReturn("DPE");
        when(vmsAdapter.getStepName()).thenReturn("VMS");

        sagaService = new OnboardingSagaServiceImpl(
                sagaRepository, tenantRepository, compensationService, kafkaProducer,
                List.of(sscAdapter, bmsAdapter, dpeAdapter, vmsAdapter));
    }

    private OnboardingSaga buildSaga() {
        List<SagaStep> steps = new ArrayList<>();
        for (String name : List.of("SSC", "BMS", "DPE", "VMS")) {
            steps.add(SagaStep.builder().stepName(name).status("PENDING").build());
        }
        return OnboardingSaga.builder()
                .sagaId("saga-001")
                .tenantId("tenant-001")
                .status(SagaStatus.IN_PROGRESS)
                .steps(steps)
                .build();
    }

    @Test
    void startSaga_allStepsSucceed_marksCompletedAndPublishesEvent() throws Exception {
        OnboardingSaga saga = buildSaga();
        when(sagaRepository.save(any(OnboardingSaga.class))).thenReturn(saga);
        when(sagaRepository.updateStepStatus(anyString(), anyInt(), anyString(), anyString())).thenReturn(saga);
        when(sagaRepository.markCompleted(anyString())).thenReturn(saga);
        when(sscAdapter.execute(anyString(), any())).thenReturn("ssc-ref");
        when(bmsAdapter.execute(anyString(), any())).thenReturn("bms-ref");
        when(dpeAdapter.execute(anyString(), any())).thenReturn("dpe-ref");
        when(vmsAdapter.execute(anyString(), any())).thenReturn("vms-ref");
        when(tenantRepository.updateStatus(anyString(), any())).thenReturn(null);

        sagaService.startSaga("tenant-001", "plan-basic", Map.of());

        verify(sagaRepository).markCompleted("saga-001");
        verify(tenantRepository).updateStatus("tenant-001", TenantStatus.ACTIVE);
        verify(kafkaProducer).publish(eq("tenant.created"), eq("tenant-001"), any());
    }

    @Test
    void startSaga_sscFails_triggersCompensationAndNoFurtherSteps() throws Exception {
        OnboardingSaga saga = buildSaga();
        when(sagaRepository.save(any(OnboardingSaga.class))).thenReturn(saga);
        when(sagaRepository.updateStepStatus(anyString(), anyInt(), anyString(), any())).thenReturn(saga);
        when(sagaRepository.markFailed(anyString(), anyString())).thenReturn(saga);
        when(sscAdapter.execute(anyString(), any())).thenThrow(new SagaStepException("SSC connection refused"));
        doNothing().when(compensationService).compensate(anyString(), anyString(), anyInt());

        sagaService.startSaga("tenant-001", "plan-basic", Map.of());

        verify(bmsAdapter, never()).execute(anyString(), any());
        verify(compensationService).compensate(eq("saga-001"), eq("tenant-001"), eq(-1));
        verify(kafkaProducer, never()).publish(eq("tenant.created"), anyString(), any());
    }

    @Test
    void startSaga_bmsFails_compensatesSSCOnly() throws Exception {
        OnboardingSaga saga = buildSaga();
        when(sagaRepository.save(any(OnboardingSaga.class))).thenReturn(saga);
        when(sagaRepository.updateStepStatus(anyString(), anyInt(), anyString(), anyString())).thenReturn(saga);
        when(sagaRepository.markFailed(anyString(), anyString())).thenReturn(saga);
        when(sscAdapter.execute(anyString(), any())).thenReturn("ssc-ref");
        when(bmsAdapter.execute(anyString(), any())).thenThrow(new SagaStepException("BMS timeout"));
        doNothing().when(compensationService).compensate(anyString(), anyString(), anyInt());

        sagaService.startSaga("tenant-001", "plan-basic", Map.of());

        verify(dpeAdapter, never()).execute(anyString(), any());
        verify(compensationService).compensate(eq("saga-001"), eq("tenant-001"), eq(0));
    }

    @Test
    void startSaga_vmsFails_compensatesSSCBMSDPE() throws Exception {
        OnboardingSaga saga = buildSaga();
        when(sagaRepository.save(any(OnboardingSaga.class))).thenReturn(saga);
        when(sagaRepository.updateStepStatus(anyString(), anyInt(), anyString(), anyString())).thenReturn(saga);
        when(sagaRepository.markFailed(anyString(), anyString())).thenReturn(saga);
        when(sscAdapter.execute(anyString(), any())).thenReturn("ssc-ref");
        when(bmsAdapter.execute(anyString(), any())).thenReturn("bms-ref");
        when(dpeAdapter.execute(anyString(), any())).thenReturn("dpe-ref");
        when(vmsAdapter.execute(anyString(), any())).thenThrow(new SagaStepException("VMS unavailable"));
        doNothing().when(compensationService).compensate(anyString(), anyString(), anyInt());

        sagaService.startSaga("tenant-001", "plan-basic", Map.of());

        verify(compensationService).compensate(eq("saga-001"), eq("tenant-001"), eq(2));
    }

    @Test
    void startSaga_sagaIsSavedWithFourSteps() throws Exception {
        OnboardingSaga saga = buildSaga();
        when(sagaRepository.save(any(OnboardingSaga.class))).thenReturn(saga);
        when(sagaRepository.updateStepStatus(anyString(), anyInt(), anyString(), anyString())).thenReturn(saga);
        when(sagaRepository.markCompleted(anyString())).thenReturn(saga);
        when(sscAdapter.execute(anyString(), any())).thenReturn("ssc-ref");
        when(bmsAdapter.execute(anyString(), any())).thenReturn("bms-ref");
        when(dpeAdapter.execute(anyString(), any())).thenReturn("dpe-ref");
        when(vmsAdapter.execute(anyString(), any())).thenReturn("vms-ref");
        when(tenantRepository.updateStatus(anyString(), any())).thenReturn(null);

        sagaService.startSaga("tenant-001", "plan-basic", Map.of("planId", "plan-basic"));

        verify(sagaRepository).save(any(OnboardingSaga.class));
    }
}
