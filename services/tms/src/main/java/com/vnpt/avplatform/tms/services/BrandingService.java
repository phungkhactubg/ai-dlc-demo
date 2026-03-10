package com.vnpt.avplatform.tms.services;

import com.vnpt.avplatform.tms.models.entity.TenantBranding;
import com.vnpt.avplatform.tms.models.request.UpdateBrandingRequest;
import org.springframework.web.multipart.MultipartFile;

public interface BrandingService {
    TenantBranding updateBranding(String tenantId, UpdateBrandingRequest request);
    String uploadLogo(String tenantId, MultipartFile logo);
    TenantBranding initiateDomainVerification(String tenantId, String customDomain);
    boolean verifyDomain(String tenantId);
}
