package com.vnpt.avplatform.tms.services;

import com.vnpt.avplatform.tms.events.publisher.TenantKafkaProducer;
import com.vnpt.avplatform.tms.exception.DomainAlreadyExistsException;
import com.vnpt.avplatform.tms.exception.InvalidStatusTransitionException;
import com.vnpt.avplatform.tms.exception.TenantNotFoundException;
import com.vnpt.avplatform.tms.models.entity.Tenant;
import com.vnpt.avplatform.tms.models.entity.TenantStatus;
import com.vnpt.avplatform.tms.models.request.CreateTenantRequest;
import com.vnpt.avplatform.tms.models.response.PageResult;
import com.vnpt.avplatform.tms.models.response.TenantDTO;
import com.vnpt.avplatform.tms.repositories.TenantRepository;
import com.vnpt.avplatform.tms.services.impl.TenantServiceImpl;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class TenantServiceTest {

    @Mock
    private TenantRepository tenantRepository;

    @Mock
    private OnboardingSagaService onboardingSagaService;

    @Mock
    private TenantKafkaProducer kafkaProducer;

    private TenantServiceImpl tenantService;

    @BeforeEach
    void setUp() {
        tenantService = new TenantServiceImpl(tenantRepository, onboardingSagaService, kafkaProducer);
    }

    private CreateTenantRequest buildRequest() {
        CreateTenantRequest req = new CreateTenantRequest();
        req.setCompanyName("Test Corp");
        req.setCompanyDomain("testcorp.com");
        req.setCountryCode("VN");
        req.setTimezone("Asia/Ho_Chi_Minh");
        req.setPlanId("plan-basic");
        req.setAdminEmail("admin@testcorp.com");
        req.setAdminName("Admin User");
        return req;
    }

    private Tenant buildActiveTenant() {
        return Tenant.builder()
                .tenantId("tenant-001")
                .companyName("Test Corp")
                .companyDomain("testcorp.com")
                .status(TenantStatus.ACTIVE)
                .planId("plan-basic")
                .surgeCap(new BigDecimal("3.0"))
                .featureFlags(new HashMap<>())
                .createdAt(Instant.now())
                .build();
    }

    @Test
    void createTenant_success_returnsDTO() {
        CreateTenantRequest request = buildRequest();
        when(tenantRepository.existsByCompanyDomain("testcorp.com")).thenReturn(false);
        when(tenantRepository.save(any(Tenant.class))).thenAnswer(inv -> inv.getArgument(0));

        TenantDTO result = tenantService.createTenant(request);

        assertThat(result).isNotNull();
        assertThat(result.getCompanyDomain()).isEqualTo("testcorp.com");
        assertThat(result.getStatus()).isEqualTo(TenantStatus.ONBOARDING);
        verify(tenantRepository).save(any(Tenant.class));
        verify(onboardingSagaService).startSaga(anyString(), eq("plan-basic"), any(Map.class));
    }

    @Test
    void createTenant_domainExists_throwsConflict() {
        CreateTenantRequest request = buildRequest();
        when(tenantRepository.existsByCompanyDomain("testcorp.com")).thenReturn(true);

        assertThatThrownBy(() -> tenantService.createTenant(request))
                .isInstanceOf(DomainAlreadyExistsException.class)
                .hasMessageContaining("testcorp.com");

        verify(tenantRepository, never()).save(any());
    }

    @Test
    void getTenant_found_returnsDTO() {
        when(tenantRepository.findByTenantId("tenant-001")).thenReturn(Optional.of(buildActiveTenant()));

        TenantDTO result = tenantService.getTenant("tenant-001");

        assertThat(result.getTenantId()).isEqualTo("tenant-001");
        assertThat(result.getStatus()).isEqualTo(TenantStatus.ACTIVE);
    }

    @Test
    void getTenant_notFound_throwsException() {
        when(tenantRepository.findByTenantId("missing")).thenReturn(Optional.empty());

        assertThatThrownBy(() -> tenantService.getTenant("missing"))
                .isInstanceOf(TenantNotFoundException.class);
    }

    @Test
    void listTenants_returnsPageResult() {
        Tenant t = buildActiveTenant();
        when(tenantRepository.findAll(0, 10)).thenReturn(List.of(t));
        when(tenantRepository.count()).thenReturn(1L);

        PageResult<TenantDTO> result = tenantService.listTenants(0, 10);

        assertThat(result.getContent()).hasSize(1);
        assertThat(result.getTotalElements()).isEqualTo(1L);
        assertThat(result.getTotalPages()).isEqualTo(1);
    }

    @Test
    void suspendTenant_activeStatus_success() {
        Tenant tenant = buildActiveTenant();
        Tenant suspended = buildActiveTenant();
        suspended.setStatus(TenantStatus.SUSPENDED);
        when(tenantRepository.findByTenantId("tenant-001")).thenReturn(Optional.of(tenant));
        when(tenantRepository.updateStatus("tenant-001", TenantStatus.SUSPENDED)).thenReturn(suspended);

        TenantDTO result = tenantService.suspendTenant("tenant-001", "Overdue payment");

        assertThat(result.getStatus()).isEqualTo(TenantStatus.SUSPENDED);
        verify(kafkaProducer).publish(eq("tenant.suspended"), eq("tenant-001"), any(Map.class));
    }

    @Test
    void suspendTenant_alreadySuspended_throwsConflict() {
        Tenant tenant = buildActiveTenant();
        tenant.setStatus(TenantStatus.SUSPENDED);
        when(tenantRepository.findByTenantId("tenant-001")).thenReturn(Optional.of(tenant));

        assertThatThrownBy(() -> tenantService.suspendTenant("tenant-001", "reason"))
                .isInstanceOf(InvalidStatusTransitionException.class);
    }

    @Test
    void reactivateTenant_suspendedStatus_success() {
        Tenant suspended = buildActiveTenant();
        suspended.setStatus(TenantStatus.SUSPENDED);
        Tenant active = buildActiveTenant();
        when(tenantRepository.findByTenantId("tenant-001")).thenReturn(Optional.of(suspended));
        when(tenantRepository.updateStatus("tenant-001", TenantStatus.ACTIVE)).thenReturn(active);

        TenantDTO result = tenantService.reactivateTenant("tenant-001");

        assertThat(result.getStatus()).isEqualTo(TenantStatus.ACTIVE);
        verify(kafkaProducer).publish(eq("tenant.reactivated"), eq("tenant-001"), any(Map.class));
    }

    @Test
    void reactivateTenant_notSuspended_throwsConflict() {
        Tenant tenant = buildActiveTenant(); // ACTIVE status
        when(tenantRepository.findByTenantId("tenant-001")).thenReturn(Optional.of(tenant));

        assertThatThrownBy(() -> tenantService.reactivateTenant("tenant-001"))
                .isInstanceOf(InvalidStatusTransitionException.class);
    }
}
