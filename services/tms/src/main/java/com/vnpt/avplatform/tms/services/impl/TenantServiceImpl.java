package com.vnpt.avplatform.tms.services.impl;

import com.vnpt.avplatform.tms.events.publisher.TenantKafkaProducer;
import com.vnpt.avplatform.tms.exception.DomainAlreadyExistsException;
import com.vnpt.avplatform.tms.exception.InvalidStatusTransitionException;
import com.vnpt.avplatform.tms.exception.TenantNotFoundException;
import com.vnpt.avplatform.tms.models.entity.Tenant;
import com.vnpt.avplatform.tms.models.entity.TenantBranding;
import com.vnpt.avplatform.tms.models.entity.TenantStatus;
import com.vnpt.avplatform.tms.models.request.CreateTenantRequest;
import com.vnpt.avplatform.tms.models.response.PageResult;
import com.vnpt.avplatform.tms.models.response.TenantDTO;
import com.vnpt.avplatform.tms.repositories.TenantRepository;
import com.vnpt.avplatform.tms.services.OnboardingSagaService;
import com.vnpt.avplatform.tms.services.TenantService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;

@Slf4j
@Service
public class TenantServiceImpl implements TenantService {

    private final TenantRepository tenantRepository;
    private final OnboardingSagaService onboardingSagaService;
    private final TenantKafkaProducer kafkaProducer;

    public TenantServiceImpl(
            TenantRepository tenantRepository,
            OnboardingSagaService onboardingSagaService,
            TenantKafkaProducer kafkaProducer) {
        this.tenantRepository = Objects.requireNonNull(tenantRepository, "tenantRepository must not be null");
        this.onboardingSagaService = Objects.requireNonNull(onboardingSagaService, "onboardingSagaService must not be null");
        this.kafkaProducer = Objects.requireNonNull(kafkaProducer, "kafkaProducer must not be null");
    }

    @Override
    @Transactional
    public TenantDTO createTenant(CreateTenantRequest request) {
        if (tenantRepository.existsByCompanyDomain(request.getCompanyDomain())) {
            throw new DomainAlreadyExistsException(
                    "A tenant with domain '" + request.getCompanyDomain() + "' already exists");
        }

        Instant now = Instant.now();
        Tenant tenant = Tenant.builder()
                .tenantId(UUID.randomUUID().toString())
                .companyName(request.getCompanyName())
                .companyDomain(request.getCompanyDomain())
                .countryCode(request.getCountryCode())
                .timezone(request.getTimezone())
                .planId(request.getPlanId())
                .status(TenantStatus.ONBOARDING)
                .vehicleQuota(request.getVehicleQuota() != null ? request.getVehicleQuota() : 0)
                .surgeCap(request.getSurgeCapOverride() != null ? request.getSurgeCapOverride() : new BigDecimal("3.0"))
                .branding(TenantBranding.builder().build())
                .featureFlags(new HashMap<>())
                .config(new HashMap<>())
                .createdAt(now)
                .updatedAt(now)
                .build();

        Tenant saved = tenantRepository.save(tenant);
        log.info("Tenant created: tenantId={}, domain={}", saved.getTenantId(), saved.getCompanyDomain());

        Map<String, Object> sagaContext = new HashMap<>();
        sagaContext.put("adminEmail", request.getAdminEmail());
        sagaContext.put("adminName", request.getAdminName());
        sagaContext.put("planId", request.getPlanId());
        sagaContext.put("vehicleQuota", saved.getVehicleQuota());
        onboardingSagaService.startSaga(saved.getTenantId(), request.getPlanId(), sagaContext);

        return mapToDTO(saved);
    }

    @Override
    public TenantDTO getTenant(String tenantId) {
        Tenant tenant = tenantRepository.findByTenantId(tenantId)
                .orElseThrow(() -> new TenantNotFoundException("Tenant not found: " + tenantId));
        return mapToDTO(tenant);
    }

    @Override
    public PageResult<TenantDTO> listTenants(int page, int size) {
        List<Tenant> tenants = tenantRepository.findAll(page, size);
        long totalElements = tenantRepository.count();
        int totalPages = (int) Math.ceil((double) totalElements / size);

        List<TenantDTO> content = tenants.stream().map(this::mapToDTO).toList();
        return PageResult.<TenantDTO>builder()
                .content(content)
                .page(page)
                .size(size)
                .totalElements(totalElements)
                .totalPages(totalPages)
                .build();
    }

    @Override
    public TenantDTO suspendTenant(String tenantId, String reason) {
        Tenant tenant = tenantRepository.findByTenantId(tenantId)
                .orElseThrow(() -> new TenantNotFoundException("Tenant not found: " + tenantId));

        if (tenant.getStatus() != TenantStatus.ACTIVE) {
            throw new InvalidStatusTransitionException(
                    "Cannot suspend tenant in status " + tenant.getStatus() + ". Only ACTIVE tenants can be suspended.");
        }

        Tenant updated = tenantRepository.updateStatus(tenantId, TenantStatus.SUSPENDED);
        log.info("Tenant suspended: tenantId={}, reason={}", tenantId, reason);

        kafkaProducer.publish("tenant.suspended", tenantId, Map.of(
                "tenantId", tenantId,
                "reason", reason != null ? reason : "",
                "previousStatus", TenantStatus.ACTIVE.name()
        ));

        return mapToDTO(updated);
    }

    @Override
    public TenantDTO reactivateTenant(String tenantId) {
        Tenant tenant = tenantRepository.findByTenantId(tenantId)
                .orElseThrow(() -> new TenantNotFoundException("Tenant not found: " + tenantId));

        if (tenant.getStatus() != TenantStatus.SUSPENDED) {
            throw new InvalidStatusTransitionException(
                    "Cannot reactivate tenant in status " + tenant.getStatus() + ". Only SUSPENDED tenants can be reactivated.");
        }

        Tenant updated = tenantRepository.updateStatus(tenantId, TenantStatus.ACTIVE);
        log.info("Tenant reactivated: tenantId={}", tenantId);

        kafkaProducer.publish("tenant.reactivated", tenantId, Map.of(
                "tenantId", tenantId,
                "previousStatus", TenantStatus.SUSPENDED.name()
        ));

        return mapToDTO(updated);
    }

    private TenantDTO mapToDTO(Tenant tenant) {
        return TenantDTO.builder()
                .tenantId(tenant.getTenantId())
                .companyName(tenant.getCompanyName())
                .companyDomain(tenant.getCompanyDomain())
                .status(tenant.getStatus())
                .planId(tenant.getPlanId())
                .surgeCap(tenant.getSurgeCap())
                .featureFlags(tenant.getFeatureFlags())
                .createdAt(tenant.getCreatedAt())
                .build();
    }
}
