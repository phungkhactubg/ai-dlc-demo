package com.vnpt.avplatform.tms.repositories;

import com.vnpt.avplatform.tms.models.entity.Tenant;
import com.vnpt.avplatform.tms.models.entity.TenantBranding;
import com.vnpt.avplatform.tms.models.entity.TenantStatus;

import java.util.List;
import java.util.Map;
import java.util.Optional;

public interface TenantRepository {
    Tenant save(Tenant tenant);
    Optional<Tenant> findByTenantId(String tenantId);
    Optional<Tenant> findByCompanyDomain(String domain);
    List<Tenant> findAll(int page, int size);
    long count();
    boolean existsByTenantId(String tenantId);
    boolean existsByCompanyDomain(String domain);
    Tenant updateStatus(String tenantId, TenantStatus status);
    Tenant updateBranding(String tenantId, TenantBranding branding);
    Tenant updateFeatureFlags(String tenantId, Map<String, Boolean> flags);
}
