package com.vnpt.avplatform.tms.services;

import com.vnpt.avplatform.tms.models.request.CreateTenantRequest;
import com.vnpt.avplatform.tms.models.response.PageResult;
import com.vnpt.avplatform.tms.models.response.TenantDTO;

public interface TenantService {
    TenantDTO createTenant(CreateTenantRequest request);
    TenantDTO getTenant(String tenantId);
    PageResult<TenantDTO> listTenants(int page, int size);
    TenantDTO suspendTenant(String tenantId, String reason);
    TenantDTO reactivateTenant(String tenantId);
}
