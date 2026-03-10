package com.vnpt.avplatform.tms.controllers;

import com.vnpt.avplatform.shared.model.ApiResponse;
import com.vnpt.avplatform.tms.models.entity.TenantBranding;
import com.vnpt.avplatform.tms.models.request.UpdateBrandingRequest;
import com.vnpt.avplatform.tms.services.BrandingService;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import java.util.Map;
import java.util.Objects;
import java.util.UUID;

@Slf4j
@RestController
@RequestMapping("/api/v1/tenants/{tenantId}/branding")
@PreAuthorize("hasRole('TENANT_ADMIN')")
public class TenantBrandingController {

    private final BrandingService brandingService;

    public TenantBrandingController(BrandingService brandingService) {
        this.brandingService = Objects.requireNonNull(brandingService, "brandingService must not be null");
    }

    @PutMapping
    public ResponseEntity<ApiResponse<TenantBranding>> updateBranding(
            @PathVariable String tenantId,
            @Valid @RequestBody UpdateBrandingRequest request,
            HttpServletRequest httpRequest) {
        TenantBranding branding = brandingService.updateBranding(tenantId, request);
        return ResponseEntity.ok(ApiResponse.success(branding, resolveTraceId(httpRequest)));
    }

    @PostMapping("/logo")
    public ResponseEntity<ApiResponse<Map<String, String>>> uploadLogo(
            @PathVariable String tenantId,
            @RequestPart("logo") MultipartFile logo,
            HttpServletRequest httpRequest) {
        String cdnUrl = brandingService.uploadLogo(tenantId, logo);
        return ResponseEntity.ok(ApiResponse.success(Map.of("cdnUrl", cdnUrl), resolveTraceId(httpRequest)));
    }

    @PostMapping("/domain-verification")
    public ResponseEntity<ApiResponse<TenantBranding>> initiateDomainVerification(
            @PathVariable String tenantId,
            @RequestParam String customDomain,
            HttpServletRequest httpRequest) {
        TenantBranding branding = brandingService.initiateDomainVerification(tenantId, customDomain);
        return ResponseEntity.ok(ApiResponse.success(branding, resolveTraceId(httpRequest)));
    }

    @GetMapping("/domain-verification")
    public ResponseEntity<ApiResponse<Map<String, Boolean>>> checkDomainVerification(
            @PathVariable String tenantId,
            HttpServletRequest httpRequest) {
        boolean verified = brandingService.verifyDomain(tenantId);
        return ResponseEntity.ok(ApiResponse.success(Map.of("verified", verified), resolveTraceId(httpRequest)));
    }

    private String resolveTraceId(HttpServletRequest request) {
        String traceId = request.getHeader("X-Trace-ID");
        return (traceId != null && !traceId.isBlank()) ? traceId : UUID.randomUUID().toString();
    }
}
